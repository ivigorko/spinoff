# Команда keywords: координация

Источники: `agents/keywords/_lead.md`, `instructions/teams/keyword-research.md`.

## Назначение и триггер

Координация специализаций keywords. Поручение на выбранное направление; для узкой задачи предпочесть role:<id>.

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
| `keywords.keyword-discovery` | Контекст и источник | seeds, candidates, metrics, coverage |
| `keywords.serp-analyzer` | keyword-discovery | query_scope, features, page_types, intent_evidence |
| `keywords.intent-classifier` | serp-analyzer | intent_map, mixed_intents, page_types |
| `keywords.competitor-keyword-spy` | keyword-discovery | candidate_targets, verified_positions, overlap |
| `keywords.keyword-gap-analyst` | competitor-keyword-spy, intent-classifier | comparison, gaps, defensive_actions |
| `keywords.cluster-builder` | keyword-gap-analyst | clusters, url_mapping, link_relationships, unresolved |

## Результат и критерий завершения

Каждый выбранный обязательный продукт принят; partial не скрыт общим quality score.
Все выбранные обязательные outputs зарегистрированы; consumer видит ограничения. Общая команда не выдаёт среднюю оценку, скрывающую критический провал.

## Проверки, ошибки и ограничения

- Не запускать все специализации без необходимости; team plan раскрывает полную библиотеку.
- Не передавать partial как complete; отдельный ограниченный процесс можно начать по нужной роли.
- Обязательны quality/qa-checklist.md и instructions/currentness.md.
- Optional logs/migration допустимо not_applicable только при неприменимости scope; отсутствие данных — blocked/partial.
- Для узкой задачи `role:<id>`, для полной библиотеки направления `team:keywords`. Роли не являются одновременно запущенными subagents.
