# Полный SEO-анализ по явно покрытым модулям

Источник: `workflows/full-seo-audit.md`. Canonical DAG: `seo_system/config/processes.json`, ID `full-seo-audit`.

## Назначение и триггер

Запрос на полный seo-анализ по явно покрытым модулям.

## Входы и зависимости

- Профиль, существующие источники по модулям, рыночный scope и конкуренты.
- Отсутствующий модуль должен быть blocked/partial/not_applicable, а не вымышленным результатом.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `crawl` / analysis | `technical.site-crawler` | Внешние входы | inventory, status_summary, redirects, coverage |
| `indexation` / analysis | `technical.indexation-manager` | crawl | robots, sitemaps, canonicals, indexation_map, conflicts |
| `cwv` / analysis | `technical.core-web-vitals-analyst` | crawl | method, field_data, lab_data, diagnosis, acceptance |
| `schema` / analysis | `technical.schema-specialist` | crawl | inventory, eligibility, json_ld, validation, implementation |
| `internal-links` / analysis | `technical.internal-linking-architect` | crawl | graph, orphans, link_changes, acceptance |
| `mobile` / analysis | `technical.mobile-seo-auditor` | crawl | sample, render_checks, parity, issues, acceptance |
| `keyword-discovery` / analysis | `keywords.keyword-discovery` | Внешние входы | seeds, candidates, metrics, coverage |
| `serp` / analysis | `keywords.serp-analyzer` | keyword-discovery | query_scope, features, page_types, intent_evidence |
| `competitor-keywords` / analysis | `keywords.competitor-keyword-spy` | keyword-discovery | candidate_targets, verified_positions, overlap |
| `keyword-gaps` / analysis | `keywords.keyword-gap-analyst` | serp, competitor-keywords | comparison, gaps, defensive_actions |
| `intent` / analysis | `keywords.intent-classifier` | serp | intent_map, mixed_intents, page_types |
| `clusters` / analysis | `keywords.cluster-builder` | intent, keyword-gaps | clusters, url_mapping, link_relationships, unresolved |
| `content-gaps` / analysis | `content.content-gap-analyst` | crawl, clusters | inventory, coverage_matrix, gaps, consolidation, priorities |
| `backlinks` / analysis | `links.backlink-auditor` | Внешние входы | coverage, domains, anchors, risks, recommendations |
| `ai` / analysis | `aeo.ai-overview-optimizer` | Внешние входы | observations, cited_sources, content_gaps, experiments |
| `local` / analysis | `local.local-competitor-analyst` | Внешние входы | geo_scope, profiles, pack_observations, gaps |
| `ecommerce` / analysis | `ecommerce.faceted-navigation-auditor` | Внешние входы | parameter_inventory, index_policy, conflicts, tests |
| `compile` / analysis | `audit.data-compiler` | crawl, indexation, cwv, schema, internal-links, mobile, keyword-discovery, serp, competitor-keywords, keyword-gaps, intent, clusters, content-gaps, backlinks, ai, local, ecommerce | artifact_inventory, findings, conflicts, coverage |
| `recommendations` / analysis | `audit.recommendation-engine` | compile | recommendations, priorities, dependencies, acceptance |
| `priority` / analysis | `strategy.priority-matrix-builder` | recommendations | scale, scored_tasks, dependencies, sequence |
| `roadmap` / analysis | `strategy.roadmap-planner` | priority | capacity, phases, tasks, dependencies, checkpoints |
| `report` / analysis | `audit.report-builder` | compile, priority, roadmap | scope, method, findings, priorities, roadmap, limitations |
| `summary` / analysis | `audit.executive-summary-writer` | report | state, risks, opportunities, decisions, next_steps |

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

`seo process plan --workflow full-seo-audit` → `seo process start --profile <profile.json> --workflow full-seo-audit --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic`.
