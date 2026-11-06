# Onboard → Research → Audit → Strategy → Execute → Report → обновление стратегии

Источник: `instructions/flow.md`. Canonical DAG: `seo_system/config/processes.json`, ID `agency-cycle`.

## Назначение и триггер

Запрос на onboard → research → audit → strategy → execute → report → обновление стратегии.

## Входы и зависимости

- Явное поручение и полный профиль.
- Принятые реальные источники на каждом этапе; выполнение внешних действий отдельно от регистрации.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `onboard` / onboard | `operations.onboard` | Внешние входы | profile, scope, goals, brand_voice, access_inventory, constraints |
| `market` / research | `research.market-researcher` | onboard | market_scope, segments, demand, opportunities |
| `discovery` / research | `keywords.keyword-discovery` | onboard | seeds, candidates, metrics, coverage |
| `serp` / research | `keywords.serp-analyzer` | discovery | query_scope, features, page_types, intent_evidence |
| `crawl` / audit | `technical.site-crawler` | onboard | inventory, status_summary, redirects, coverage |
| `technical` / audit | `technical.indexation-manager` | crawl | robots, sitemaps, canonicals, indexation_map, conflicts |
| `intent` / research | `keywords.intent-classifier` | serp | intent_map, mixed_intents, page_types |
| `clusters` / research | `keywords.cluster-builder` | intent | clusters, url_mapping, link_relationships, unresolved |
| `content` / audit | `content.content-gap-analyst` | crawl, clusters | inventory, coverage_matrix, gaps, consolidation, priorities |
| `compile` / audit | `audit.data-compiler` | market, technical, content | artifact_inventory, findings, conflicts, coverage |
| `strategy` / strategy | `strategy.seo-strategist` | compile | assessment, pillars, kpis, risks, decisions |
| `priority` / strategy | `strategy.priority-matrix-builder` | strategy | scale, scored_tasks, dependencies, sequence |
| `roadmap` / strategy | `strategy.roadmap-planner` | priority | capacity, phases, tasks, dependencies, checkpoints |
| `prepare` / execute | `audit.fix-generator` | roadmap | baseline, patches, tests, rollback, authorization_boundary |
| `release` / execute | `operations.release-record` | prepare | release, authorization_boundary, tests, rollback |
| `verify` / verify | `operations.production-verify` | release | checks, regressions, decision |
| `measure` / measurement | `operations.measurement` | verify | comparison, confounders, decision |
| `report` / report | `analytics.monthly-report-writer` | measure | summary, kpis, work_log, changes, next_month, limitations |
| `refresh` / strategy_refresh | `operations.strategy-refresh` | report | continue, change, stop, next_backlog, review_window |
| `next-roadmap` / strategy_refresh | `strategy.roadmap-planner` | refresh | capacity, phases, tasks, dependencies, checkpoints |

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

`seo process plan --workflow agency-cycle` → `seo process start --profile <profile.json> --workflow agency-cycle --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic`.
