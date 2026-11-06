# spinoff

Рабочая основа SEO-системы для Codex по [SEO Agency in a Box](https://github.com/z1fex/SEO-AGENCY-IN-A-BOX) и техническому заданию версии 1.1 от 06.11.2026. Сейчас работает локальный вертикальный срез: **импорт → проверка → технические находки → отчёт → приоритеты → roadmap → QA**.

Это ещё не развёрнутая SEO-платформа. В CLI внешние адаптеры, публикация и автоматическое измерение не реализованы. Через инструменты текущей сессии подтверждены поиск, чтение и XLSX-экспорт существующих файлов Drive; запись не проверена. Проверка остальных источников описана в [протоколе доступа](docs/access-verification.md). `go` возвращает partial с видимыми ограничениями. Реальные клиентские данные и секреты не хранятся в Git.

## Быстрый запуск

Python 3.11+ и uv; проверено с Python 3.12.14 и uv 0.12.23. `uv.lock` фиксирует runtime-зависимости и hashes. Установка не подключает внешние SEO-сервисы.

```bash
uv sync --frozen
uv run python examples/create_demo.py --output workspace/demo-input
uv run seo preflight --profile workspace/demo-input/profile.json
uv run seo plan --workflow technical
uv run seo run --profile workspace/demo-input/profile.json --manifest workspace/demo-input/source-manifest.json --workspace workspace/demo-state --workflow technical
uv run seo status --workspace workspace/demo-state --project synthetic-demo
```

Демо синтетическое, сайт example.com не запрашивается. Команда run вернёт путь к report.md, priority.md, roadmap.md, tasks.json, coverage.json, qa.json внутри deliverables, а также manifest.json и artifacts.json. Повтор той же команды проверяет хэши и переиспользует run, не создаёт копии. Новое создание демо меняет даты и тем самым создаёт другие входы.

Для реального запуска заполните профиль и source manifest в приватном workspace по [руководству](docs/setup.md). JSON, CSV и XLSX pages поддерживаются с явным mapping; фактические заголовки отчёта Labrika предстоит проверить. Поддержка контейнера XLSX не означает проверенную интеграцию с Labrika.

Перед mapping можно посмотреть локальный контейнер: `uv run seo inspect-import --file <file.xlsx> --format xlsx`. Для первой строки конкретного листа добавьте `--sheet '<имя>'`. Это просмотр формата, не аудит; дата источника и права на сервис им не подтверждаются. Поддержаны Google Sheets XLSX-экспорты без worksheet dimension metadata.

## Проверки

```bash
uv run python -m unittest discover -v
uv run python scripts/check_repository.py
git diff --check
```

Проверяются checksum, scope и изоляция проектов, свежесть исходных данных, ревизия, дубликаты, типы, CSV/XLSX mapping, запрет формул, evidence, неполное покрытие, повтор запуска и повреждённые результаты. GitHub Actions подготовлен для этих проверок; удалённый запуск ещё не выполнялся.

## Навигация

- [Правила Codex](AGENTS.md) и [.agents/skills](.agents/skills) — выбор сценария, входы, выходы и gates.
- [Статус и следующие шаги](docs/status.md) — реализованное и границы MVP.
- [Runbook](docs/runbook.md), [восстановление](docs/recovery.md), [контракт данных](instructions/data-contract.md).
- [Матрица источников](docs/source-matrix.md), [полный цикл](workflows/lifecycle.md), [миграция upstream](docs/migration-map.md).
- [Происхождение](provenance/upstream.json), [исходная инвентаризация](docs/repository-inventory.md), [MIT upstream](LICENSE).
