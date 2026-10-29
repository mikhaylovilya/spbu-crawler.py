# spbu-crawler.py

Веб-краулер Web 1.0. Обходит HTML-страницы сайта, очищает текст, собирает ссылки, считает статистику и сохраняет все обработанные страницы в один JSON-файл.

## Возможности

- обход сайта в ширину с ограничениями по количеству страниц и глубине;
- задержка между запросами и настраиваемый таймаут;
- очистка текста от `script`, `style`, `noscript`, `template`, `svg` и лишних пробелов;
- извлечение заголовка страницы и всех ссылок с текстом якоря;
- определение внутренних и внешних ссылок, внутренних поддоменов и документов `.doc`, `.docx`, `.pdf`;
- учёт неработающих страниц: HTTP 4xx/5xx, таймауты и сетевые ошибки;
- экспорт страниц, ошибок и статистики в один JSON.

Краулер не выполняет JavaScript, не читает `robots.txt` и не ходит по документам `.doc`, `.docx`, `.pdf`: такие ссылки только учитываются в статистике.

## Установка

```bash
git clone https://github.com/mikhaylovilya/spbu-crawler.py.git
cd spbu-crawler.py
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python -m crawler https://spbu.ru
```

По умолчанию результат сохраняется в `crawl.json`, статистика печатается в консоль. Пример с настройками:

```bash
python -m crawler https://example.com \
  --output result.json \
  --max-pages 200 \
  --max-depth 4 \
  --delay 0.5
```

Обход поддоменов:

```bash
python -m crawler https://example.com --include-subdomains --max-pages 500
```

### Параметры

| Параметр | По умолчанию | Описание |
| --- | --- | --- |
| `url` | обязательный | Стартовый URL со схемой `http` или `https` |
| `-o`, `--output` | `crawl.json` | Путь к итоговому JSON |
| `--max-pages` | `100` | Максимум HTTP-запросов за запуск |
| `--max-depth` | `3` | Максимальная глубина обхода, стартовая страница имеет глубину `0` |
| `--delay` | `0.2` | Задержка между запросами в секундах |
| `--timeout` | `10` | Таймаут одного запроса в секундах |
| `--include-subdomains` | выключено | Обходить также внутренние поддомены |

Без `--include-subdomains` краулер ходит только по основному домену и его `www`-варианту. Поддомены, встреченные в ссылках, всё равно учитываются в статистике. Ссылки на документы `.doc`, `.docx`, `.pdf` не скачиваются, но попадают в статистику.

## Формат результата

```json
{
  "start_url": "https://example.com/",
  "generated_at": "2026-10-29T00:00:00+00:00",
  "stats": {
    "total_pages": 12,
    "total_links": 185,
    "internal_pages": 12,
    "broken_pages": 2,
    "internal_subdomains": 3,
    "external_links": 40,
    "unique_external_resources": 17,
    "unique_document_links": 4
  },
  "pages": [
    {
      "url": "https://example.com/",
      "status_code": 200,
      "title": "Example",
      "text": "Очищенный текст страницы",
      "links": [
        {
          "url": "https://example.com/about",
          "text": "О сайте",
          "internal": true
        }
      ],
      "depth": 0,
      "fetched_at": "2026-10-29T00:00:00+00:00"
    }
  ],
  "failures": [
    {
      "url": "https://example.com/missing",
      "error": "HTTP 404",
      "status_code": 404
    }
  ]
}
```

### Статистика

| Поле | Что считает |
| --- | --- |
| `total_pages` | Количество успешно обработанных HTML-страниц |
| `total_links` | Общее количество ссылок на страницах, включая повторы |
| `internal_pages` | Количество обработанных страниц на основном домене и его поддоменах |
| `broken_pages` | Количество неработающих страниц из массива `failures` |
| `internal_subdomains` | Количество уникальных внутренних поддоменов среди обработанных страниц и найденных ссылок; `www` не считается отдельным поддоменом |
| `external_links` | Общее количество ссылок на внешние ресурсы, включая повторы |
| `unique_external_resources` | Количество уникальных внешних URL |
| `unique_document_links` | Количество уникальных ссылок на файлы `.doc`, `.docx`, `.pdf` |

В `pages` попадают только успешно обработанные HTML-страницы. Неработающие страницы, таймауты и сетевые ошибки сохраняются в `failures`; страницы с не-HTML содержимым пропускаются.

## Тесты

```bash
source .venv/bin/activate
python -m pytest
```

Быстрый запуск только интеграционных тестов краулера:

```bash
python -m pytest tests/test_crawl.py -q
```