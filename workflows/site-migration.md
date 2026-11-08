# План и контроль миграции сайта

Источник: `workflows/site-migration.md`. Canonical DAG: `seo_system/config/processes.json`, ID `site-migration`.

## Назначение и триггер

Запрос на план и контроль миграции сайта.

## Входы и зависимости

- Старый и новый host/структура в согласованном scope, baseline и rollback.
- Post-migration шаг требует фактического release и новых observations; координатор их не создаёт.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `baseline` / audit | `technical.site-crawler` | Внешние входы | inventory, status_summary, redirects, coverage |
| `mapping` / execute | `technical.site-migration-specialist` | baseline | baseline, url_mapping, redirect_rules, parity, rollback, verification |
| `indexation` / audit | `technical.indexation-manager` | mapping | robots, sitemaps, canonicals, indexation_map, conflicts |
| `meta` / execute | `content.meta-tag-writer` | mapping | variants, selected_metadata, rationale, acceptance |
| `links` / audit | `technical.internal-linking-architect` | mapping | graph, orphans, link_changes, acceptance |
| `dashboard` / report | `analytics.dashboard-builder` | mapping | kpi_definitions, views, source_links, refresh_spec, alerts |
| `prepared` / execute | `audit.fix-generator` | indexation, meta, links, dashboard | baseline, patches, tests, rollback, authorization_boundary |
| `release` / execute | `operations.release-record` | prepared | release, authorization_boundary, tests, rollback |
| `verify` / verify | `operations.production-verify` | release | checks, regressions, decision |
| `post-audit` / execute | `technical.site-migration-specialist` | verify | baseline, url_mapping, redirect_rules, parity, rollback, verification |

Входы и режимы узлов (переопределяют standalone role только в этом workflow):

- `baseline`: pages; режим `analysis`.
- `mapping`: pages; режим `analysis`.
- `indexation`: pages; режим `analysis`.
- `meta`: pages; режим `analysis`.
- `links`: internal_links; режим `analysis`.
- `dashboard`: analytics; режим `analysis`.
- `prepared`: business; режим `analysis`.
- `release`: release; режим `analysis`.
- `verify`: verification, release; режим `analysis`.
- `post-audit`: pages; режим `analysis`.

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

`seo process plan --workflow site-migration` → `seo gates --profile <profile.json> --workspace <private-dir>` → `seo process start --profile <profile.json> --workflow site-migration --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic` на зарезервированных example-доменах.
