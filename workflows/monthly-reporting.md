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
| `rankings` / report | `analytics.ranking-tracker` | Внешние входы | scope, rankings, distribution, movers, limitations |
| `traffic` / report | `analytics.traffic-analyst` | Внешние входы | definitions, periods, segments, changes, explanations |
| `conversions` / report | `analytics.conversion-analyst` | Внешние входы | goal_definitions, funnel, conversions, attribution, actions |
| `content` / report | `content.content-performance-analyst` | traffic, conversions | inventory, segments, performance, actions, risks |
| `roi` / report | `analytics.roi-calculator` | traffic, conversions | costs, value_model, calculations, scenarios, limitations |
| `report` / report | `analytics.monthly-report-writer` | rankings, traffic, conversions, content, roi | summary, kpis, work_log, changes, next_month, limitations |
| `refresh` / strategy | `operations.strategy-refresh` | report | continue, change, stop, next_backlog, review_window |

Входы и режимы узлов (переопределяют standalone role только в этом workflow):

- `rankings`: serp; режим `analysis`.
- `traffic`: analytics; режим `analysis`.
- `conversions`: analytics; режим `analysis`.
- `content`: analytics; режим `analysis`.
- `roi`: analytics; режим `analysis`.
- `report`: analytics; режим `analysis`.
- `refresh`: business; режим `analysis`.

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

`seo process plan --workflow monthly-reporting` → `seo gates --profile <profile.json> --workspace <private-dir>` → `seo process start --profile <profile.json> --workflow monthly-reporting --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic` на зарезервированных example-доменах.
