# Месячный отчёт и следующий план

Источник: `workflows/monthly-reporting.md`. Canonical DAG: `seo_system/config/processes.json`, ID `monthly-reporting`.

## Назначение и триггер

Запрос на месячный отчёт и следующий план.

## Входы и зависимости

- Два закрытых сопоставимых периода, definitions и журнал релизов.
- ROI без стоимости/ценности не вычислять; partial отчёт допустим с ограничениями.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `rankings` / analysis | `analytics.ranking-tracker` | Внешние входы | scope, rankings, distribution, movers, limitations |
| `traffic` / analysis | `analytics.traffic-analyst` | Внешние входы | definitions, periods, segments, changes, explanations |
| `conversions` / analysis | `analytics.conversion-analyst` | Внешние входы | goal_definitions, funnel, conversions, attribution, actions |
| `content` / analysis | `content.content-performance-analyst` | traffic, conversions | inventory, segments, performance, actions, risks |
| `roi` / analysis | `analytics.roi-calculator` | traffic, conversions | costs, value_model, calculations, scenarios, limitations |
| `report` / analysis | `analytics.monthly-report-writer` | rankings, traffic, conversions, content, roi | summary, kpis, work_log, changes, next_month, limitations |
| `refresh` / analysis | `operations.strategy-refresh` | report | continue, change, stop, next_backlog, review_window |

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

`seo process plan --workflow monthly-reporting` → `seo process start --profile <profile.json> --workflow monthly-reporting --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic`.
