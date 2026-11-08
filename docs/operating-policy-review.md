# Содержательная сверка порядка и реализации

08.11.2026. Три пользовательских источника прочитаны напрямую, metadata/modified/hash сохранены в provenance/operating-sources.json. Drive и клиентские документы не изменены. Upstream/предметные роли сохранены, неизвестные навыки Grok не объявлены перенесёнными.

| Требование | Найденное противоречие | Исправление и проверка |
|---|---|---|
| Пять файлов карточки + таблица/чат/реестр | onboarding/onboard.md заменял пять файлов schema profile | Карточка и handoff — отдельные обязательные outputs; review связывает те же пять distinct file locator/hash; отрицательные тесты отсутствия/подмены |
| Настоящая приёмка Ниной | submit/completed мог выглядеть достаточным для перехода | Отдельный authenticated-reader boundary, внешние review records, nina_acceptance отдельно от technical status. Reader не реализован, без него fail closed; JSON/QA не принимаются как решение |
| Исследование до аудита | Crawl зависел только от onboard и начинался параллельно с market | Agency DAG: market→algorithms→competitors→keywords/SERP/clusters→crawl. Внешний gate требует принятого исследования; отдельный role не обходит |
| Аудит до стратегии | Отдельная strategy роль принималась по минимальному business source | Project-wide gate требует Nina audit review, точные complete products, те же project/profile hashes |
| Утверждение ≠ запуск | Учитывались DAG/source guards, но не отдельная команда | Проверяются разные исходные факты strategy approval и launch, связанные с конкретной версией; тест launch отсутствует при наличии approval |
| Явный запрет проекта | Standalone partial role мог обойти остановленный основной DAG | Общий phase hold, scoped separate lift command; новые run/workspace/profile не дают разрешения. Клиентские данные/запреты этим изменением не менялись |
| Параллельные независимые задачи | Риск заменить фазы чрезмерной последовательностью | Внутри принятого этапа независимые узлы остаются ready одновременно; тест schema/CWV в обратном порядке после crawl |
| Ни один adapter write не принимает фазу | source registration или произвольная запись могли выглядеть приёмкой | Raw registration не создаёт review; start/submit/legacy execute проверяют общий gate. JSON импорт решения и QA authority запрещены; честно раскрыта доверенная кодовая граница будущего адаптера |
| Приёмка полного аудита | Частичный продукт мог участвовать в standalone суммировании | Nina review требует complete non-synthetic products, минимальные substantive outputs и отсутствие открытых blocker в принятом решении; все заказанные направления/содержание дополнительно проверяет Нина |
| Публикация/вторая проверка | Технический completed не различал пользовательское «Выполнено» | nina_acceptance выделен отдельно. Release evidence требует material review; content route Nina→Slava, другие изменения — scoped Igor ok. Код не создаёт permissions и не публикует; measurement ждёт Nina second verification |
| Свежие данные | Единый возраст мог восприниматься новым paid crawl вместо reuse | Правило reuse <30 дней перед запуском; строгая freshness отдельных datasets и исходная дата сохраняются. Нужны уточнения, а не омоложение старого экспорта |
| Порядок/качество | Оценка ≥3 могла оправдать недоказанные данные | Оценка не отменяет source/subject QA, неизвестные метрики/ROI и реальные SEO currentness corrections |
| Сроки/полномочия | Риск добавить SLA и автоматические permissions | Новые 2/4/2 сроки не вводились; даты/бюджеты не назначены. Общая норма не снимает отдельный запрет пользователя |

## Последствия для существующих процессов

Все 11 исходных workflows и 75 ролей остаются процедурной библиотекой. На client run каждому узлу назначается каноническая operating phase. Узкий workflow не обязан заново выполнять все фазы, но обязан получить уже принятые внешние входы; он не закрывает research/audit/strategy одним выбранным output. Если его локальный DAG не содержит нужный предыдущий этап, он ждёт принятую фазу проекта из реестра. Это намеренное устранение обхода, а не автоматический запуск отсутствующих ролей.

Agency cycle теперь содержит 32 вместо30 узлов: явные algorithms и competitors. Приёмки Нины — внешние решения между фазами, не выдуманные роли/автоматические узлы. Generic QA, source dates/hashes/scope, analytics calendar-month protection, release/verification tests и сохранённые upstream originals не ослаблены.

Snapshots contract3 и ниже — legacy_unreviewed, только история; source/submit не модернизируют их молча. Для продолжения нужен новый run и реальная приёмка соответствующих материалов. Эта разработка не мигрирует и не переписывает существующие клиентские workspace/Drive. Синтетические fixtures проверяют координацию, не подтверждают клиентский результат.

## Реальные ограничения

Доверенный reader/authentication, общая очередь, Drive storage/recovery adapter и external executor не реализованы. Поэтому позитивные client-format regression tests используют явно фиктивный trusted reader, а реальный CLI без bridge блокирует переход. Это не «настоящая приёмка Ниной в тестах». До bridge порядок вне кода контролируется исполнителем и фактической Ниной, без обхода закрытых mutation APIs. Локальные записи не обеспечивают защиту от оператора, который меняет код/SQLite, и не согласуют несколько workspace.


## Подтверждение проверок

Проверки выполняются через реальные start/source/submit/status/legacy execute, не только JSON Schema. Новые регрессии проверяют отсутствие/подмену пяти файлов, fake QA/JSON/actor, неполную фазу, отдельную роль/команду/новый root, hold и отдельное снятие, старый snapshot, испорченный hash, разницу approval/launch/deployment, вторую проверку перед measurement. Позитивные случаи: независимые audit branches в обратном порядке, оба маршрута permission check и полный client-format cycle с внешними фиктивными source decisions между этапами. Никакие тесты не читают клиента и не делают настоящую приёмку Ниной.

Результат итогового прогона фиксируется в сообщении сдачи; playbook renderer/checker и ограниченный repository secret/data guard обязательны вместе с unit tests и git diff --check.
