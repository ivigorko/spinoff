# Аудит электронной торговли и план исправлений

Источник: `workflows/ecommerce-audit.md`. Canonical DAG: `seo_system/config/processes.json`, ID `ecommerce-audit`.

## Назначение и триггер

Запрос на аудит электронной торговли и план исправлений.

## Входы и зависимости

- Реальный каталог, варианты, платформа и целевые площадки.
- Выборка карточек, фильтров, фида и доступных диагностик.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `facets` / audit | `ecommerce.faceted-navigation-auditor` | Внешние входы | parameter_inventory, index_policy, conflicts, tests |
| `categories` / audit | `ecommerce.category-strategist` | facets | taxonomy, mapping, category_briefs, linking, priorities |
| `products` / audit | `ecommerce.product-page-optimizer` | categories | sample, product_facts, content_changes, acceptance |
| `schema` / audit | `ecommerce.product-schema-generator` | products | eligibility, product_data, json_ld, validation |
| `feed` / audit | `ecommerce.shopping-feed-optimizer` | products | feed_inventory, validation, consistency, fixes |
| `priority` / strategy | `strategy.priority-matrix-builder` | facets, categories, products, schema, feed | scale, scored_tasks, dependencies, sequence |
| `roadmap` / strategy | `strategy.roadmap-planner` | priority | capacity, phases, tasks, dependencies, checkpoints |

Входы и режимы узлов (переопределяют standalone role только в этом workflow):

- `facets`: products; режим `analysis`.
- `categories`: products; режим `analysis`.
- `products`: products; режим `analysis`.
- `schema`: products; режим `analysis`.
- `feed`: products; режим `analysis`.
- `priority`: business; режим `analysis`.
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

## Общий порядок пользователя

instructions/operating-policy.md имеет приоритет над сокращениями upstream. Пять файлов карточки и настоящая приёмка Нины обязательны до исследования; принятые исследование/аудит — до следующей фазы. Команда Игоря, утверждение, приёмка и QA — разные факты. Специальный workflow не выдаёт разрешения перескочить фазу; выбранный каталог может ожидать внешние принятые входы. Параллельны только независимые задачи внутри разрешённого этапа. Доверенного reader решений и общей очереди пока нет; для клиента без проверенных решений переход закрыт.

## Фактический режим

Процедура адаптирована для исполнения Codex. CLI автоматизирует DAG, state, проверку контрактов/ссылок/значений evidence и фиксацию результата. Предметный анализ и ревью — ручная работа Codex с реальными разрешёнными источниками. Сетевые адаптеры, store/apply/publish/scheduling не имитируются.

## Команды

`seo process plan --workflow ecommerce-audit` → `seo gates --profile <profile.json> --workspace <private-dir>` → `seo process start --profile <profile.json> --workflow ecommerce-audit --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic` на зарезервированных example-доменах.
