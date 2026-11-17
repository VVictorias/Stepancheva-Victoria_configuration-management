"""Итеративный DFS: достижимый граф и поиск обратных рёбер."""

from dataclasses import dataclass


@dataclass
class Graph:
    """Граф с устойчивым порядком вершин и рёбер из POM или файла."""

    root: str
    edges: dict


def build_graph(repository, root):
    """Собрать граф стеком DFS, не используя рекурсивные вызовы."""
    pending = [(root, frozenset())]
    visited = set()
    edges = {}
    while pending:
        state = pending.pop()
        if state in visited:
            continue
        visited.add(state)
        package, exclusions = state
        children = repository.children(package, exclusions)
        adjacent = edges.setdefault(package, [])
        for child, _ in children:
            if child not in adjacent:
                adjacent.append(child)
        pending.extend(reversed(children))
    return Graph(root, edges)


def traverse(graph):
    """Получить порядок завершения DFS и обратные рёбра без рекурсии."""
    colors = {graph.root: "active"}
    stack = [(graph.root, iter(graph.edges[graph.root]))]
    completed = []
    cycles = []
    while stack:
        node, children = stack[-1]
        child = next(children, None)
        if child is None:
            stack.pop()
            colors[node] = "done"
            completed.append(node)
        elif colors.get(child) == "active":
            cycles.append((node, child))
        elif child not in colors:
            colors[child] = "active"
            stack.append((child, iter(graph.edges[child])))
    return completed, cycles


def adjacency_text(graph):
    """Вывести каждую достижимую вершину, включая листья."""
    return "\n".join(
        f"{node}: {' '.join(children)}".rstrip()
        for node, children in graph.edges.items()
    )


def dependency_order(graph):
    """Вернуть зависимости раньше потребителей; отклонить циклический граф."""
    completed, cycles = traverse(graph)
    if cycles:
        details = ", ".join(f"{left} -> {right}" for left, right in cycles)
        raise ValueError(f"порядок загрузки невозможен, есть цикл: {details}")
    return [node for node in completed if node != graph.root]
