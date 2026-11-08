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
| `crawl` / audit | `technical.site-crawler` | Внешние входы | inventory, status_summary, redirects, coverage |
| `indexation` / audit | `technical.indexation-manager` | crawl | robots, sitemaps, canonicals, indexation_map, conflicts |
| `cwv` / audit | `technical.core-web-vitals-analyst` | crawl | method, field_data, lab_data, diagnosis, acceptance |
| `schema` / audit | `technical.schema-specialist` | crawl | inventory, eligibility, json_ld, validation, implementation |
| `internal-links` / audit | `technical.internal-linking-architect` | crawl | graph, orphans, link_changes, acceptance |
| `mobile` / audit | `technical.mobile-seo-auditor` | crawl | sample, render_checks, parity, issues, acceptance |
| `keyword-discovery` / research | `keywords.keyword-discovery` | Внешние входы | seeds, candidates, metrics, coverage |
| `serp` / research | `keywords.serp-analyzer` | keyword-discovery | query_scope, features, page_types, intent_evidence |
| `competitor-keywords` / research | `keywords.competitor-keyword-spy` | keyword-discovery | candidate_targets, verified_positions, overlap |
| `keyword-gaps` / research | `keywords.keyword-gap-analyst` | serp, competitor-keywords | comparison, gaps, defensive_actions |
| `intent` / research | `keywords.intent-classifier` | serp | intent_map, mixed_intents, page_types |
| `clusters` / research | `keywords.cluster-builder` | intent, keyword-gaps | clusters, url_mapping, link_relationships, unresolved |
| `content-gaps` / audit | `content.content-gap-analyst` | crawl, clusters | inventory, coverage_matrix, gaps, consolidation, priorities |
| `backlinks` / audit | `links.backlink-auditor` | Внешние входы | coverage, domains, anchors, risks, recommendations |
| `ai` / audit | `aeo.ai-overview-optimizer` | Внешние входы | observations, cited_sources, content_gaps, experiments |
| `local` / audit | `local.local-competitor-analyst` | Внешние входы | geo_scope, profiles, pack_observations, gaps |
| `ecommerce` / audit | `ecommerce.faceted-navigation-auditor` | Внешние входы | parameter_inventory, index_policy, conflicts, tests |
| `compile` / audit | `audit.data-compiler` | crawl, indexation, cwv, schema, internal-links, mobile, keyword-discovery, serp, competitor-keywords, keyword-gaps, intent, clusters, content-gaps, backlinks, ai, local, ecommerce | artifact_inventory, findings, conflicts, coverage |
| `recommendations` / audit | `audit.recommendation-engine` | compile | recommendations, priorities, dependencies, acceptance |
| `priority` / strategy | `strategy.priority-matrix-builder` | recommendations | scale, scored_tasks, dependencies, sequence |
| `roadmap` / strategy | `strategy.roadmap-planner` | priority | capacity, phases, tasks, dependencies, checkpoints |
| `report` / audit | `audit.report-builder` | compile, priority, roadmap | scope, method, findings, priorities, roadmap, limitations |
| `summary` / audit | `audit.executive-summary-writer` | report | state, risks, opportunities, decisions, next_steps |

Входы и режимы узлов (переопределяют standalone role только в этом workflow):

- `crawl`: pages; режим `analysis`.
- `indexation`: pages; режим `analysis`.
- `cwv`: performance; режим `analysis`.
- `schema`: pages; режим `analysis`.
- `internal-links`: internal_links; режим `analysis`.
- `mobile`: pages; режим `analysis`.
- `keyword-discovery`: business; режим `analysis`.
- `serp`: serp; режим `analysis`.
- `competitor-keywords`: competitors; режим `analysis`.
- `keyword-gaps`: business; режим `analysis`.
- `intent`: business; режим `analysis`.
- `clusters`: business; режим `analysis`.
- `content-gaps`: business; режим `analysis`.
- `backlinks`: backlinks; режим `analysis`.
- `ai`: ai_visibility; режим `analysis`.
- `local`: local; режим `analysis`.
- `ecommerce`: products; режим `analysis`.
- `compile`: business; режим `analysis`.
- `recommendations`: business; режим `analysis`.
- `priority`: business; режим `analysis`.
- `roadmap`: business; режим `analysis`.
- `report`: business; режим `analysis`.
- `summary`: business; режим `analysis`.

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

`seo process plan --workflow full-seo-audit` → `seo gates --profile <profile.json> --workspace <private-dir>` → `seo process start --profile <profile.json> --workflow full-seo-audit --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic` на зарезервированных example-доменах.
