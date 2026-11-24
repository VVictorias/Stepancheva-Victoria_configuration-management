# Домашняя работа №4

**Вариант №22. Ассемблер и интерпретатор учебной виртуальной машины.**

Переход в папку работы из корня репозитория.
[Правила ассемблера и параметры запуска](homework_4/README.md).

```bash
cd homework_4
```

## Этап 1. Перевод программы в промежуточное представление

Ассемблер читает мнемонику и аргумент, проверяет их и сохраняет пары `(A, B)`.
Флаг `--ir` показывает поля четырёх команд из методички.

```bash
bash run.sh assemble --input examples/control.asm --output /tmp/control.bin --ir
```

```text
A=0, B=197
A=11, B=93
A=3, B=959
A=5, B=654
Ассемблировано команд: 4
```

## Этап 2. Формирование машинного кода

Поле A занимает биты 0–3, поле B начинается с бита 4. У `LOAD` поле B
заканчивается на бите 31, у остальных команд на бите 19. Байты записываются
от младшего к старшему. `LOAD` занимает 4 байта, остальные команды по 3.

```bash
bash run.sh assemble --input examples/control.asm --output /tmp/control.bin --test
wc -c < /tmp/control.bin
```

```text
0x50, 0x0C, 0x00, 0x00
0xDB, 0x05, 0x00
0xF3, 0x3B, 0x00
0xE5, 0x28, 0x00
Ассемблировано команд: 4
      13
```

Все четыре последовательности совпали с методичкой. В файле 13 байт.

## Этап 3. Интерпретатор и операции с памятью

Интерпретатор загружает код с байта 0 в общий массив команд и данных.
Адрес 32-битного слова `i` соответствует байту `4 * i`. Интерпретатор
читает команды из этого массива, декодирует их и выполняет.
В примере `READ` и `STORE` копируют слова 100–103 в слова 104–107.

```bash
bash run.sh assemble --input examples/copy.asm --output /tmp/copy.bin
bash run.sh interpret --input /tmp/copy.bin --output /tmp/copy.xml --range 100 107
cat /tmp/copy.xml
```

```xml
<memory>
  <cell address="100">197</cell>
  <cell address="101">0</cell>
  <cell address="102">54321</cell>
  <cell address="103">268435455</cell>
  <cell address="104">197</cell>
  <cell address="105">0</cell>
  <cell address="106">54321</cell>
  <cell address="107">268435455</cell>
</memory>
```

## Этап 4. Реализация АЛУ

`bswap()` меняет порядок четырёх байтов 32-битного слова.
Результат `0x01020304 → 0x04030201` попадает в аккумулятор, затем
`STORE` сохраняет его в слове 101.

```bash
bash run.sh assemble --input examples/bswap.asm --output /tmp/bswap.bin
bash run.sh interpret --input /tmp/bswap.bin --output /tmp/bswap.xml --range 100 101
cat /tmp/bswap.xml
```

```xml
<memory>
  <cell address="100">16909060</cell>
  <cell address="101">67305985</cell>
</memory>
```

## Этап 5. Выполнение тестовой задачи

В каждой программе 36 команд. `BSWAP` обрабатывает девять слов по адресам
100–108, а `STORE` возвращает результат в то же слово. Исходные векторы
и значения в XML приведены в десятичной системе.

Исходный вектор `vector_bytes.asm` `[16909060, 1122867, 1, 256, 65536, 16777216, 5614335, 168496141, 252851286]`.

```bash
bash run.sh assemble --input examples/vector_bytes.asm --output /tmp/vector_bytes.bin
bash run.sh interpret --input /tmp/vector_bytes.bin --output /tmp/vector_bytes.xml --range 100 108
cat /tmp/vector_bytes.xml
```

```xml
<memory>
  <cell address="100">67305985</cell>
  <cell address="101">857870592</cell>
  <cell address="102">16777216</cell>
  <cell address="103">65536</cell>
  <cell address="104">256</cell>
  <cell address="105">1</cell>
  <cell address="106">4289352960</cell>
  <cell address="107">218893066</cell>
  <cell address="108">1446253071</cell>
</memory>
```

Исходный вектор `vector_edges.asm` `[0, 168430090, 11250432, 1048560, 128, 255, 268435455, 134217728, 8356094]`.

```bash
bash run.sh assemble --input examples/vector_edges.asm --output /tmp/vector_edges.bin
bash run.sh interpret --input /tmp/vector_edges.bin --output /tmp/vector_edges.xml --range 100 108
cat /tmp/vector_edges.xml
```

```xml
<memory>
  <cell address="100">0</cell>
  <cell address="101">168430090</cell>
  <cell address="102">11250432</cell>
  <cell address="103">4043247360</cell>
  <cell address="104">2147483648</cell>
  <cell address="105">4278190080</cell>
  <cell address="106">4294967055</cell>
  <cell address="107">8</cell>
  <cell address="108">4269833984</cell>
</memory>
```

Исходный вектор `vector_small.asm` `[1, 2, 3, 7, 15, 31, 63, 127, 255]`.

```bash
bash run.sh assemble --input examples/vector_small.asm --output /tmp/vector_small.bin
bash run.sh interpret --input /tmp/vector_small.bin --output /tmp/vector_small.xml --range 100 108
cat /tmp/vector_small.xml
```

```xml
<memory>
  <cell address="100">16777216</cell>
  <cell address="101">33554432</cell>
  <cell address="102">50331648</cell>
  <cell address="103">117440512</cell>
  <cell address="104">251658240</cell>
  <cell address="105">520093696</cell>
  <cell address="106">1056964608</cell>
  <cell address="107">2130706432</cell>
  <cell address="108">4278190080</cell>
</memory>
```

Во всех трёх дампах проверены 27 значений и их адреса.

## Тестирование

```bash
python3 -B -m unittest discover -s tests -q
```

Все 18 тестов прошли (`OK`). Проверены границы, ошибки машинного кода и XML.
Отдельный тест подтверждает, что запись в область кода меняет будущую команду.
