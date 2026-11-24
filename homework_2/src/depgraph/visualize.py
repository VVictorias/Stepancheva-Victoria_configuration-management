"""Mermaid, ASCII-дерево и открытие графа в обычном браузере."""

from html import escape
from pathlib import Path
import tempfile
import webbrowser


MERMAID_MODULE = (
    "https://cdn.jsdelivr.net/npm/mermaid@11.12.1/dist/mermaid.esm.min.mjs"
)


def mermaid_text(graph):
    """Использовать безопасные внутренние идентификаторы Mermaid."""
    names = {node: f"n{index}" for index, node in enumerate(graph.edges)}
    lines = ["flowchart TD"]
    for node, identifier in names.items():
        label = escape(node, quote=True)
        lines.append(f'    {identifier}["{label}"]')
    for node, children in graph.edges.items():
        for child in children:
            lines.append(f"    {names[node]} --> {names[child]}")
    return "\n".join(lines) + "\n"


def ascii_tree(graph):
    """Построить дерево стеком, отмечая циклы и уже раскрытые узлы."""
    lines = [graph.root]
    expanded = {graph.root}
    pending = tree_children(graph, graph.root, "", frozenset({graph.root}))
    while pending:
        node, prefix, last, ancestors = pending.pop()
        branch = "`-- " if last else "|-- "
        suffix = ""
        if node in ancestors:
            suffix = " [цикл]"
        elif node in expanded:
            suffix = " [уже показан]"
        lines.append(prefix + branch + node + suffix)
        if suffix:
            continue
        expanded.add(node)
        padding = "    " if last else "|   "
        pending.extend(
            tree_children(graph, node, prefix + padding, ancestors | {node})
        )
    return "\n".join(lines)


def tree_children(graph, node, prefix, ancestors):
    """Подготовить элементы стека с сохранением порядка соседей."""
    children = graph.edges[node]
    return [
        (child, prefix, index == len(children) - 1, ancestors)
        for index, child in reversed(list(enumerate(children)))
    ]


def html_page(graph, diagram):
    """Создать HTML со встроенным исходником и графическим SVG Mermaid."""
    title = escape(graph.root)
    return f"""<!doctype html>
<html lang="ru">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Граф зависимостей {title}</title>
<h1>{title}</h1>
<p id="status">Построение диаграммы...</p>
<pre class="mermaid">{escape(diagram)}</pre>
<script type="module">
try {{
 const {{default: mermaid}} = await import('{MERMAID_MODULE}');
 mermaid.initialize({{startOnLoad:false, securityLevel:'strict'}});
 await mermaid.run({{querySelector:'.mermaid'}});
 document.getElementById('status').textContent = 'Диаграмма готова';
}} catch(error) {{
 document.getElementById('status').textContent =
  'Не удалось построить диаграмму. Проверьте доступ к CDN Mermaid: ' + error;
}}
</script>
</html>
"""


def write_visualization(graph, output=None, open_browser=True):
    """Сохранить текст и HTML, при обычном запуске показать граф."""
    directory = (
        Path(output) if output else Path(tempfile.mkdtemp(prefix="depgraph-"))
    )
    directory = directory.expanduser().resolve()
    directory.mkdir(parents=True, exist_ok=True)
    diagram = mermaid_text(graph)
    (directory / "graph.mmd").write_text(diagram, encoding="utf-8")
    page = directory / "graph.html"
    page.write_text(html_page(graph, diagram), encoding="utf-8")
    if open_browser and not webbrowser.open(page.as_uri()):
        raise ValueError(f"браузер не открылся; откройте {page} вручную")
    return page
