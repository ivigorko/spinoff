# Команда ecommerce: координация

Источники: `agents/ecommerce/_lead.md`, `instructions/teams/ecommerce-seo.md`.

## Назначение и триггер

Координация специализаций ecommerce. Поручение на выбранное направление; для узкой задачи предпочесть role:<id>.

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
| `ecommerce.faceted-navigation-auditor` | Контекст и источник | parameter_inventory, index_policy, conflicts, tests |
| `ecommerce.category-strategist` | faceted-navigation-auditor | taxonomy, mapping, category_briefs, linking, priorities |
| `ecommerce.product-page-optimizer` | category-strategist | sample, product_facts, content_changes, acceptance |
| `ecommerce.product-schema-generator` | product-page-optimizer | eligibility, product_data, json_ld, validation |
| `ecommerce.shopping-feed-optimizer` | product-page-optimizer | feed_inventory, validation, consistency, fixes |

## Результат и критерий завершения

Каждый выбранный обязательный продукт принят; partial не скрыт общим quality score.
Все выбранные обязательные outputs зарегистрированы; consumer видит ограничения. Общая команда не выдаёт среднюю оценку, скрывающую критический провал.

## Проверки, ошибки и ограничения

- Не запускать все специализации без необходимости; team plan раскрывает полную библиотеку.
- Не передавать partial как complete; отдельный ограниченный процесс можно начать по нужной роли.
- Обязательны quality/qa-checklist.md и instructions/currentness.md.
- Optional logs/migration допустимо not_applicable только при неприменимости scope; отсутствие данных — blocked/partial.
- Для узкой задачи `role:<id>`, для полной библиотеки направления `team:ecommerce`. Роли не являются одновременно запущенными subagents.

## Общий gate

instructions/operating-policy.md обязателен до выбора подграфа. Leader не заменяет Нину и не выдаёт команду Игоря. Отдельная роль/команда/адаптер не пропускает приёмку фазы. Параллельны только независимые задачи разрешённого этапа; локальная SQLite не является общей многопользовательской очередью.
