# Команда analytics: координация

Источники: `agents/analytics/_lead.md`, `instructions/teams/analytics-reporting.md`.

## Назначение и триггер

Координация специализаций analytics. Поручение на выбранное направление; для узкой задачи предпочесть role:<id>.

## Входы и зависимости

Версия профиля, scope, разрешённые источники и принятые контекстные результаты
Обязательные evidence kinds определяются выбранными ролями, не всей командой. Входящие продукты других команд получать через scoped registry.

## Действия

1. Уточнить цель и выбрать workflow или минимальные роли; не запускать весь каталог автоматически.
2. Прочитать предметные процедуры и проверить реальные источники/свежесть/полномочия.
3. Выполнить готовые узлы по DAG; блокировать только зависимые ветки.
4. Принять продукты по предметному и критическому QA, сохранить source lineage и coverage.
5. Передать точные artifact IDs consumer; обозначить complete/partial/blocked, не имитировать внешние действия.

## Специализации и порядок

| Узел / процедура | Обязательные предшественники | Предметный результат |
|---|---|---|
| `analytics.ranking-tracker` | Контекст и источник | scope, rankings, distribution, movers, limitations |
| `analytics.traffic-analyst` | Контекст и источник | definitions, periods, segments, changes, explanations |
| `analytics.conversion-analyst` | Контекст и источник | goal_definitions, funnel, conversions, attribution, actions |
| `analytics.roi-calculator` | traffic-analyst, conversion-analyst | costs, value_model, calculations, scenarios, limitations |
| `analytics.dashboard-builder` | traffic-analyst, conversion-analyst, ranking-tracker | kpi_definitions, views, source_links, refresh_spec, alerts |
| `analytics.monthly-report-writer` | roi-calculator, dashboard-builder | summary, kpis, work_log, changes, next_month, limitations |

## Результат и критерий завершения

Каждый выбранный обязательный продукт принят; partial не скрыт общим quality score.
Все выбранные обязательные outputs зарегистрированы; consumer видит ограничения. Общая команда не выдаёт среднюю оценку, скрывающую критический провал.

## Проверки, ошибки и ограничения

- Не запускать все специализации без необходимости; team plan раскрывает полную библиотеку.
- Не передавать partial как complete; отдельный ограниченный процесс можно начать по нужной роли.
- Обязательны quality/qa-checklist.md и instructions/currentness.md.
- Optional logs/migration допустимо not_applicable только при неприменимости scope; отсутствие данных — blocked/partial.
- Для узкой задачи `role:<id>`, для полной библиотеки направления `team:analytics`. Роли не являются одновременно запущенными subagents.
