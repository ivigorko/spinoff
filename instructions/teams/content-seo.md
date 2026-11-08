# Команда content: координация

Источники: `agents/content/_lead.md`, `instructions/teams/content-seo.md`.

## Назначение и триггер

Координация специализаций content. Поручение на выбранное направление; для узкой задачи предпочесть role:<id>.

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
| `content.content-performance-analyst` | Контекст и источник | inventory, segments, performance, actions, risks |
| `content.content-gap-analyst` | Контекст и источник | inventory, coverage_matrix, gaps, consolidation, priorities |
| `content.content-strategist` | content-gap-analyst | pillars, page_mapping, priorities, metrics, dependencies |
| `content.content-calendar-planner` | content-strategist, content-performance-analyst | calendar, capacity, dependencies, refresh_slots |
| `content.brief-writer` | content-calendar-planner | intent, outline, unique_value, facts, links, acceptance |
| `content.seo-blog-writer` | brief-writer | draft, metadata, links, sources, editorial_checks |
| `content.landing-page-copywriter` | brief-writer | page_copy, offer_evidence, conversion_path, metadata, acceptance |
| `content.meta-tag-writer` | seo-blog-writer, landing-page-copywriter | variants, selected_metadata, rationale, acceptance |
| `content.faq-paa-writer` | brief-writer | questions, answers, sources, placement, eligibility |
| `content.content-optimizer` | meta-tag-writer, faq-paa-writer | baseline, gaps, edit_plan, revised_content, acceptance |

## Результат и критерий завершения

Каждый выбранный обязательный продукт принят; partial не скрыт общим quality score.
Все выбранные обязательные outputs зарегистрированы; consumer видит ограничения. Общая команда не выдаёт среднюю оценку, скрывающую критический провал.

## Проверки, ошибки и ограничения

- Не запускать все специализации без необходимости; team plan раскрывает полную библиотеку.
- Не передавать partial как complete; отдельный ограниченный процесс можно начать по нужной роли.
- Обязательны quality/qa-checklist.md и instructions/currentness.md.
- Optional logs/migration допустимо not_applicable только при неприменимости scope; отсутствие данных — blocked/partial.
- Для узкой задачи `role:<id>`, для полной библиотеки направления `team:content`. Роли не являются одновременно запущенными subagents.

## Общий gate

instructions/operating-policy.md обязателен до выбора подграфа. Leader не заменяет Нину и не выдаёт команду Игоря. Отдельная роль/команда/адаптер не пропускает приёмку фазы. Параллельны только независимые задачи разрешённого этапа; локальная SQLite не является общей многопользовательской очередью.
