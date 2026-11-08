# Локальная стратегия и подготовка профилей

Источник: `workflows/local-seo-setup.md`. Canonical DAG: `seo_system/config/processes.json`, ID `local-seo-setup`.

## Назначение и триггер

Запрос на локальная стратегия и подготовка профилей.

## Входы и зависимости

- Реальные локации, NAP, услуги и платформы целевого рынка.
- Проверенные профили/geo observations; публикация отдельно.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `competitors` / audit | `local.local-competitor-analyst` | Внешние входы | geo_scope, profiles, pack_observations, gaps |
| `profile` / audit | `local.gbp-optimizer` | competitors | profile_audit, accuracy, categories, content, actions |
| `citations` / audit | `local.citation-builder` | profile | canonical_nap, citation_inventory, inconsistencies, submission_pack |
| `content` / audit | `local.local-content-writer` | competitors, profile | locations, page_copy, local_facts, links, acceptance |
| `reviews` / audit | `local.review-strategist` | profile | review_inventory, sentiment, response_drafts, collection_plan |
| `roadmap` / strategy | `strategy.roadmap-planner` | citations, content, reviews | capacity, phases, tasks, dependencies, checkpoints |

Входы и режимы узлов (переопределяют standalone role только в этом workflow):

- `competitors`: local; режим `analysis`.
- `profile`: local; режим `analysis`.
- `citations`: local; режим `analysis`.
- `content`: business; режим `analysis`.
- `reviews`: local; режим `analysis`.
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

`seo process plan --workflow local-seo-setup` → `seo gates --profile <profile.json> --workspace <private-dir>` → `seo process start --profile <profile.json> --workflow local-seo-setup --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic` на зарезервированных example-доменах.
