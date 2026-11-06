# План запуска нового сайта

Источник: `workflows/new-site-launch.md`. Canonical DAG: `seo_system/config/processes.json`, ID `new-site-launch`.

## Назначение и триггер

Запрос на план запуска нового сайта.

## Входы и зависимости

- Бриф и целевая структура, тестовая версия/макеты или ограничение планирования.
- Результат launch-ready план, а не факт deployment.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `discovery` / analysis | `keywords.keyword-discovery` | Внешние входы | seeds, candidates, metrics, coverage |
| `intent` / analysis | `keywords.intent-classifier` | discovery | intent_map, mixed_intents, page_types |
| `clusters` / analysis | `keywords.cluster-builder` | intent | clusters, url_mapping, link_relationships, unresolved |
| `architecture` / analysis | `content.content-strategist` | clusters | pillars, page_mapping, priorities, metrics, dependencies |
| `schema` / analysis | `technical.schema-specialist` | architecture | target_pages, planned_changes, acceptance_plan, limitations |
| `indexation` / analysis | `technical.indexation-manager` | architecture | target_pages, planned_changes, acceptance_plan, limitations |
| `brief` / analysis | `content.brief-writer` | architecture | intent, outline, unique_value, facts, links, acceptance |
| `content` / analysis | `content.seo-blog-writer` | brief | draft, metadata, links, sources, editorial_checks |
| `meta` / analysis | `content.meta-tag-writer` | content | variants, selected_metadata, rationale, acceptance |
| `roadmap` / analysis | `strategy.roadmap-planner` | schema, indexation, meta | capacity, phases, tasks, dependencies, checkpoints |

Входы и режимы узлов (переопределяют standalone role только в этом workflow):

- `discovery`: business; режим `analysis`.
- `intent`: business; режим `analysis`.
- `clusters`: business; режим `analysis`.
- `architecture`: business; режим `analysis`.
- `schema`: business, keywords; режим `planning`.
  - Вместо извлечения текущей разметки/директив определить proposed URL и правила по architecture и business facts.
  - Подготовить конкретные planned changes и acceptance checks; отсутствие live наблюдения раскрыть в limitations; не объявлять сайт проверенным.
- `indexation`: business, keywords; режим `planning`.
  - Вместо извлечения текущей разметки/директив определить proposed URL и правила по architecture и business facts.
  - Подготовить конкретные planned changes и acceptance checks; отсутствие live наблюдения раскрыть в limitations; не объявлять сайт проверенным.
- `brief`: business; режим `analysis`.
- `content`: business; режим `analysis`.
- `meta`: business; режим `draft`.
  - Работать с принятым draft предшественника, не требовать опубликованную страницу; сохранить ID и target URL из brief/architecture.
  - Результат остаётся предложением/черновиком; live проверка выполняется после разрешённого релиза.
- `roadmap`: business; режим `analysis`.

На каждом узле выполнить предметную процедуру procedures/roles/<team>/<name>.md, её QA и work-product contract. Readiness рассчитывается coordinator; он не пишет экспертный результат вместо Codex.

## Условия перехода и завершения

Все обязательные узлы приняты; report/coverage отражают реально выполненное. Partial входы никогда не дают completed всего workflow.
При partial dependencies consumer обязан явно принимать неполноту; итог остаётся partial. Optional-модуль исключается только с предметным обоснованием. Все остальные обязательные узлы должны иметь принятый продукт.

## Проверки и ошибки

- Отсутствующий вход блокирует зависимую ветку, независимые ready узлы доступны.
- Partial передаётся лишь узлам с accept_partial_inputs и сохраняется в итоговом статусе.
- Никаких новых paid calls, публикаций, сообщений или ACL-изменений из координатора.
- Применить quality/qa-checklist.md, source freshness, immutable lineage и subject-specific currentness decisions.
- Результаты соответствуют scope/цели, а не просто наличию заполненного JSON.

## Фактический режим

Процедура адаптирована для исполнения Codex. CLI автоматизирует DAG, state, проверку контрактов/ссылок/значений evidence и фиксацию результата. Предметный анализ и ревью — ручная работа Codex с реальными разрешёнными источниками. Сетевые адаптеры, store/apply/publish/scheduling не имитируются.

## Команды

`seo process plan --workflow new-site-launch` → `seo process start --profile <profile.json> --workflow new-site-launch --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic`.
