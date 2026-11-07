# Итоговая сверка перед отправкой ветки — 07.11.2026

Основания: ТЗ «SEO_система_Codex_Лабрика_обновлено.md» (SHA-256 09266bab433b95ca4d45dfe5dbd5a4904de1ad465b8a66d41004b9cb930ce318), upstream commit 738e86a84a55c44ef9093b6631943bef8a4738e0 и поручения Игоря. Исходный частный документ не публикуется; ниже только трассировка требований и фактических возможностей репозитория.

Полный перенос инструкций и workflows не означает реализацию всех проектных этапов ТЗ. Библиотека процедур адаптирована; этап офлайн-координации работает, остальные этапы имеют явные ограничения. Предметная критическая сверка всех 11 workflows и representative ролей, найденные дефекты и проверки — [pilot-critical-review.md](pilot-critical-review.md). Пофайловая трассировка 144 оригиналов — [migration-map.md](migration-map.md).

| Раздел ТЗ | Где учтён | Реальное состояние и незавершённое |
|---|---|---|
| 1. Цель и проверенность | README, status, access-verification | Полный логический цикл выбран целью; инструкции отделены от кода, tools от account/data authorization |
| 2. Исправления upstream | currentness C01–C17, roles/config/procedures | Исправлены aliases, quotas/SEO promises, fictitious ROI, retired features, scoring и source limitations; original bytes сохранены |
| 3. Полномочия | AGENTS, permissions, capability/QA contracts | Код не делает внешние действия; реальные apply/store/publish требуют инструмента и поручения. JSON authorization_ref не выдаёт прав |
| 4. Архитектура/Drive delivery | storage-layout, recovery, source-matrix | Код/state/client data разделены, локальный immutable registry есть. Drive outbox/upload/verify/reconciliation/restore не реализованы; это незавершённый этап 2 ТЗ |
| 5. Репозиторий | repository-inventory, source map, AGENTS | Выбран spinoff, отдельная ветка; старое не удалялось. Структура адаптирована под Python/Codex, а не буквальный clone путей Claude |
| 6. Пути/совместимость | data-flow, compatibility, storage-layout | Единые project/run/artifact IDs в каждой подсистеме; legacy technical и process registry разделены, auto-import между ними отсутствует |
| 7. Данные/наблюдения/рекомендации | schemas, config, core/processes | Profile/source/work-product/claims/release/comparison contracts работают. Все provider-specific datasets не типизированы автоматически; manual JSON normalization требует original/mapping/QA |
| 8. Источники/адаптеры | source-matrix, source-policy, access-verification | Все категории ТЗ учтены. Внешних CLI adapters нет. Исторически проверен session Drive read/export; конкретные GSC/Yandex/Labrika данные из CLI не проверены |
| 9. Свежесть | freshness.json, frozen process plan, source_fresh | Current freshness/hash/revision проверяются. Historical baseline не получает автоматического исключения; просроченный snapshot нельзя зарегистрировать даже как partial. Свежесформированный historical analytics export допустим с честными датами записей. Специальный архивный режим пока отсутствует |
| 10. DAG/этапы/частичные задачи | processes/teams/roles config, workflows, skills | Все 11 workflows, role/team selectors и 30-node agency-cycle координируются. Partial/blocked/readiness работают. Collect/Normalize/Deliver/apply — ручные действия с реальными инструментами, не встроенные внешние executors |
| 11. Состояния/конкурентность | processes, recovery, schemas | Один локальный SQLite writer, immutable artifacts и события. Нет leases/fencing/multi-worker, общего scheduler и автоматического failed-submit ledger. awaiting_measurement отражается причиной/coverage, отдельного persistent enum нет |
| 12. QA/приоритет/roadmap | quality, procedures, subject_gates | Critical QA, task/finding IDs, dependencies/acceptance/effort и partial gates. Typed selected checks у 25 ролей; все остальные выводы требуют ручной содержательной приёмки. Score не является доказанным uplift |
| 13. AGENTS/skills | AGENTS, 18 .agents/skills, 75 role procedures/12 leads | Функциональные маршрутизаторы и подробные предметные процедуры; количество агентов не цель. Skills не доказывают исполнение анализа без данных |
| 14. Команды будущей системы | CLI/process commands, runbook | Действующие plan/start/source/template/submit/status/mark и technical import задокументированы. apply/verify/measure здесь evidence contracts, а не live executors; разговорный go маршрутизируется в полный process, legacy CLI go остаётся partial technical alias. Universal resume/store/apply CLI из ТЗ не реализован |
| 15. Внедрение/результат | release/expected_changes/verification/comparison | Работает приёмка записей prepared→release→fresh field verification→closed-window measurement. Фактический deploy/site checks/data collection должен выполнить авторизованный внешний исполнитель; клиентский SEO эффект не измерялся |
| 16. Тесты/готовность | unittest suite, CI, pilot-critical-review | 86 tests на момент сверки, реальные coordinator traversal/products/events и негативные кейсы. Storage/network/failure tests будущих adapters и реальный клиентский E2E не выполнялись; synthetic не заменяет их |
| 17. Этапы MVP | implementation-plan/status | Inventory/design + offline каркас выполнены с указанными границами. Drive storage, first real analysis, direct APIs/concurrency и real closed loop остаются следующими этапами |
| 18. Стартовое поручение | AGENTS, orchestrator/runbook | Перенесены автономность, read-only/подготовка, safety и отчётность. Новое явное поручение разрешает push этой отдельной ветки; main/production/deploy не входят |
| 19. Решения пилота | onboarding/profile/setup, access-verification | Домен/цель, Drive folder/write, property/counter, dataset, квоты, storage retention и полномочия должны быть конкретными. Не выбирались и не выдавались за заполненные |
| 20. Источники/статусы утверждений | provenance, currentness, access-verification | Pinned upstream сохранён; публичные возможности, пользовательский account context и проверенность executor/export/API разделены. Секреты/личные выгрузки вне Git |

## Labrika, Яндекс, GSC и Drive

Labrika учтена как источник technical/content/schema/indexation, семантики/частотности/кластеров/посадочных, позиций, конкурентов, внутренних/исходящих ссылок и анализа доноров, GEO-рекомендаций, фактической AI-видимости, Diff monitoring и product-description generation. Это отдельные функции с разными форматами, доступами и лимитами. Outbound не подменяет inbound базу; GEO идеи не подменяют наблюдённый ответ; AI position не равна SERP rank. ТЗ сообщало о наличии части отчётов в аккаунте — это не теряется, но технический доступ Codex к ним не подтверждён. Мониторинг, генерации и платные проверки не запускались.

Яндекс разделён на Вебмастер host, Метрика counter/goals/filters и Wordstat demand/region/operators. GSC property/search analytics отличается от воспроизводимого SERP. Историческое общее Yandex connection не доказывает эти права. Новых OAuth/token requests для публикации кода не требуется и не выполнялось.

Drive остаётся предполагаемым долговременным хранилищем клиентских материалов. Проверенный session read/export не означает autonomous CLI access или delivery. Клиентские файлы и state остались вне Git; отправка ветки переносит только код, процедуры, схемы и synthetic examples. Ни private исходное ТЗ, ни реальные XLSX/содержимое Drive в репозиторий не добавляются.

## Вывод перед отправкой

Нового основания объявить всю систему полностью развёрнутой нет. Достаточна публикация отдельной development-ветки как проверяемой реализации процедур и офлайн-каркаса. До клиентского production-пилота остаются выбор сайта и реальных данных, предметная приёмка и фактическая проверка необходимых подключений/хранилища. Эти пробелы перечислены явно, не заменены mock-integrations или фиктивным completed.
