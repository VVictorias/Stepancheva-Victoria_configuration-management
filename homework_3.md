# Домашняя работа №3

**Вариант №22. Преобразование учебного конфигурационного языка в TOML.**

Lark разбирает файл по правилам из `src/language.lark`, а `tomli-w` записывает вычисленные значения в TOML.

## Правила языка

Целые числа соответствуют шаблону `[+-]?([1-9][0-9]*|0)`, имена шаблону `[_a-zA-Z]+`.
Строки имеют вид `@"Текст"`. Массивы `list(...)` могут быть пустыми или вложенными.
Запись `5 -> base` объявляет константу и даёт ключ `base = 5` в TOML.

Операция в выражении стоит перед аргументами. `?{+ base 2}` складывает целые,
`?{- base 2}` вычитает, `?{ord @"A"}` возвращает код Unicode символа.
Выражения могут ссылаться на объявленные выше константы и входить в другие выражения или массивы.

## Примеры работы

Команды выполняются из корня репозитория после [установки библиотек](homework_3/README.md#подготовка-и-запуск).

```bash
cd homework_3
source .venv/bin/activate
```

### Учебное приложение. Подсчёт тем

```text
@"Тренажёр по Python" -> title
5 -> topics
?{+ topics 2} -> total_topics
list(@"Чтение", @"Практика", @"Тест") -> activities
```
```bash
bash run.sh --input examples/study.cfg --output /tmp/study.toml
cat /tmp/study.toml
```
```toml
title = "Тренажёр по Python"
topics = 5
total_topics = 7
activities = [
    "Чтение",
    "Практика",
    "Тест",
]
```

### Интернет-магазин. Цена со скидкой и код категории

```text
@"Клавиатура" -> product
1290 -> price
200 -> discount
?{- price discount} -> final_price
@"A" -> category
?{ord category} -> category_code
```
```bash
bash run.sh --input examples/store.cfg --output /tmp/store.toml
cat /tmp/store.toml
```
```toml
product = "Клавиатура"
price = 1290
discount = 200
final_price = 1090
category = "A"
category_code = 65
```

### Компьютерный класс. Ряды компьютеров

```text
@"Кабинет информатики" -> room
list(list(1, 2, 3), list(4, 5, ?{+ 5 1})) -> rows
list(@"Linux", @"Windows") -> systems
```
```bash
bash run.sh --input examples/classroom.cfg --output /tmp/classroom.toml
cat /tmp/classroom.toml
```
```toml
room = "Кабинет информатики"
rows = [
    [
        1,
        2,
        3,
    ],
    [
        4,
        5,
        6,
    ],
]
systems = [
    "Linux",
    "Windows",
]
```

## Ошибки

При ошибке синтаксиса программа показывает строку и столбец, при ошибке вычисления сообщает её причину.
В обоих случаях она возвращает код 1 и оставляет выходной файл без изменений.

```bash
printf '%s\n' 'list(1, ) -> items' > /tmp/bad.cfg
bash run.sh --input /tmp/bad.cfg --output /tmp/bad.toml
printf '%s\n' '?{+ missing 1} -> value' > /tmp/unknown.cfg
bash run.sh --input /tmp/unknown.cfg --output /tmp/unknown.toml
```
```text
Ошибка: /tmp/bad.cfg: строка 1, столбец 9: синтаксическая ошибка (неожиданный символ ')')
Ошибка: /tmp/unknown.cfg: строка 1: неизвестная константа 'missing'
```

## Тестирование

```bash
python3 -B -m unittest discover -s tests -q
```

Все 16 тестов прошли (`OK`). Проверены конструкции языка, вложенность, ошибки и все три примера.
Тесты читают выходной TOML через `tomllib` и сравнивают данные с ожидаемыми.
