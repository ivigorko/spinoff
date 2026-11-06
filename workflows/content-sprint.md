# Контентный спринт от плана до проверенного draft

Источник: `workflows/content-sprint.md`. Canonical DAG: `seo_system/config/processes.json`, ID `content-sprint`.

## Назначение и триггер

Запрос на контентный спринт от плана до проверенного draft.

## Входы и зависимости

- Принятая стратегия/keyword mapping либо явно описанный ограниченный scope.
- Актуальная страница, факты и brand voice; публикация отдельно.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `calendar` / analysis | `content.content-calendar-planner` | Внешние входы | calendar, capacity, dependencies, refresh_slots |
| `serp` / analysis | `keywords.serp-analyzer` | calendar | query_scope, features, page_types, intent_evidence |
| `brief` / analysis | `content.brief-writer` | calendar, serp | intent, outline, unique_value, facts, links, acceptance |
| `draft` / analysis | `content.seo-blog-writer` | brief | draft, metadata, links, sources, editorial_checks |
| `meta` / analysis | `content.meta-tag-writer` | draft | variants, selected_metadata, rationale, acceptance |
| `faq` / analysis | `content.faq-paa-writer` | brief, draft | questions, answers, sources, placement, eligibility |
| `optimize` / analysis | `content.content-optimizer` | draft, meta, faq | baseline, gaps, edit_plan, revised_content, acceptance |
| `summary` / analysis | `audit.executive-summary-writer` | optimize | state, risks, opportunities, decisions, next_steps |

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

`seo process plan --workflow content-sprint` → `seo process start --profile <profile.json> --workflow content-sprint --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic`.
