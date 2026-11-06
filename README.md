# spinoff

SEO Agency for Codex: адаптация [SEO Agency in a Box](https://github.com/z1fex/SEO-AGENCY-IN-A-BOX) по техническому заданию версии 1.1. Поддерживает **Onboard → Research → Audit → Strategy → Execute → Verify/Measure → Report → обновление стратегии**.

Перенесена функциональная библиотека: **75 специализаций, 12 leaders, 17 общих/team-инструкций, все 11 workflows, onboarding, базовые правила, QA, tool guides и 11 шаблонов**. Все 144 upstream-файла сохранены без изменения в vendor; [source map](provenance/source-map.json) связывает каждый с адаптацией или объяснённым reference-only решением. Устаревшие правила исправлены в [currentness](instructions/currentness.md).

Критическая проверка и границы пилота: [docs/pilot-critical-review.md](docs/pilot-critical-review.md). Перечень перенесённых файлов не доказывает предметную полноту; выбранные outputs проверяет код, остальные — Codex по процедуре.

**Как это работает:** Codex читает предметную процедуру и выполняет анализ/подготовку по реальным разрешённым данным. Локальный CLI координирует DAG, зависимости, состояния, immutable evidence/products и проверки контрактов. Он не генерирует вместо специалиста все SEO-результаты, не доказывает экспертную правильность одного JSON и не делает внешних действий. Отдельный автоматический технический срез проверяет HTTP/title/H1 по импортированным страницам.

Внешние адаптеры CLI, запись в Drive, deployment и расписание не реализованы. Через инструменты текущей сессии подтверждены чтение и XLSX-экспорт существующих Drive-файлов; остальные границы в [протоколе доступа](docs/access-verification.md). Факт адаптации инструкций не означает подключение всех сервисов.

## Установка и выбор процесса

Python 3.11+ и uv; проверено на Python 3.12.14. Runtime-зависимости и hashes в uv.lock.

```bash
uv sync --frozen
uv run seo roles --team keywords
uv run seo process plan --workflow keyword-strategy
uv run seo process plan --workflow full-seo-audit
uv run seo process plan --workflow agency-cycle
uv run seo process plan --workflow role:content.meta-tag-writer
```

11 исходных workflows: `full-seo-audit`, `keyword-strategy`, `content-sprint`, `competitor-teardown`, `link-building-campaign`, `local-seo-setup`, `ecommerce-audit`, `new-site-launch`, `site-migration`, `monthly-reporting`, `quarterly-review`. Дополнительно — `agency-cycle`, `team:<name>` и `role:<team.name>`.

## Синтетический пример полного цикла

```bash
uv run python -m examples.process_fixture --output workspace/cycle-demo --workflow agency-cycle
```

Пример явно synthetic. Он проверяет передачу продуктов, release/verification/measurement records и strategy refresh, не обращается к сайтам или API, ничего не публикует и не доказывает качество реального SEO-анализа.

## Работа Codex с реальным проектом

Сначала [onboarding](onboarding/onboard.md), затем минимальный подходящий workflow и [runbook](docs/runbook.md). `process start` замораживает профиль и план. `source` регистрирует пригодный локальный JSON evidence с provenance. `template` даёт незаполненный каркас: Codex выполняет предметную процедуру, заполняет sections/claims/QA, затем `submit` принимает продукт и открывает зависимости. `status` показывает ready/blocked/partial/completed. Координатор сохраняет факты внешних действий только по evidence, сам их не выполняет.

Raw клиента, state, results, токены и credentials вне Git. Drive рассматривается как постоянное хранилище после отдельного write/read/reconciliation этапа; local_validated не означает загружено в Drive.

## Автоматический технический импорт

Сохранён `seo run --workflow technical` для JSON/CSV/XLSX pages: scope/freshness/checksum/revision → три технических правила → report/priority/roadmap/QA. Он всегда partial. Старый CLI `--workflow go` — только совместимый alias этого среза; разговорный «go/full audit» маршрутизируется Codex в новый `full-seo-audit`.

```bash
uv run python examples/create_demo.py --output workspace/technical-input
uv run seo run --profile workspace/technical-input/profile.json --manifest workspace/technical-input/source-manifest.json --workspace workspace/technical-state --workflow technical
uv run seo inspect-import --file <file.xlsx> --format xlsx
```

## Проверки и навигация

```bash
uv run python -m unittest discover -v
uv run python scripts/render_playbook.py --check
uv run python scripts/check_playbook.py
uv run python scripts/check_repository.py
uv build
```

[AGENTS](AGENTS.md) · [.agents/skills](.agents/skills) · [Предметные роли](procedures/roles) · [Leaders](procedures/leads) · [Workflows](workflows) · [Контракты](instructions/data-flow.md) · [Статус](docs/status.md) · [Восстановление](docs/recovery.md) · [План внедрения](docs/implementation-plan.md).
