# Единый producer/consumer контракт

Источник: upstream instructions/data-flow.md. Активные пути не зависят от имён клиентов, дат в названиях или wikilinks.

1. Профиль — `project_id` и `profile_version`; исходники неизменяемы.
2. Для технического автоматического среза — существующий artifact registry и source-manifest по instructions/data-contract.md.
3. Для процессной библиотеки — `projects/<project_id>/processes/<run_id>/frozen.json`, `sources/<source_id>.json`, `products/<artifact_id>.json` и отдельный SQLite process-state.sqlite3. Coordinator хранит node, source IDs, hashes, parent artifact IDs и события.
4. Producer возвращает work-product по schema с role ID и предметными sections из roles.json. Consumer получает точный набор input_artifact_ids из замороженного DAG, а не «все файлы клиента».
5. Любой внешний факт в claims имеет source ID и JSON pointer/value; field value сверяется с immutable JSON evidence. Инференс тоже имеет evidence; гипотеза обозначена. Содержательную правильность текста и полноту предметной процедуры проверяет Codex, а не одна JSON Schema.
6. Нормализованный JSON evidence — не подмена оригинального экспорта. Для client run manifest.original обязателен: file, sha256, format и описание normalization/mapping. Coordinator сохраняет и повторно проверяет исходные байты рядом с normalized JSON, но не доказывает правильность ручного mapping. source_locator/primary_origin/даты/scope сохраняются. Готовый pages-import может дать normalized/pages.json; другие форматы нормализуются явно по реальным полям. Синтетические fixtures явно помечены и не попадают в client run.
7. Required dependencies блокируют submit до приёмки. Partial допускается только узлом с accept_partial_inputs; downstream coverage остаётся partial. Optional not_applicable допустим при предметной неприменимости, а не вместо потерянных данных.
8. Freshness — одна конфигурация; исходная дата важнее даты загрузки. После изменения нужны новые проверки затронутых URL с целевой revision. Данные другого host/market не смешиваются.
9. Drive является предполагаемым долговременным хранилищем материалов, не транзакционной очередью. Сейчас session read/export проверен, storage adapter/write/reconciliation отсутствуют. Локальные артефакты не называть загруженными в Drive.
10. Для нескольких клиентов все ключи и resolver имеют project/run scope. SQLite предназначена одному локальному писателю, вне Drive sync. Multi-worker orchestration не реализована.

Незарегистрированный каталог после аварии не считать принятым продуктом и не перезаписывать. Сначала сохранить единственную копию и сверить state; правила восстановления в docs/recovery.md. Перенос старых vault-разделов описан в provenance/source-map.json; исторический snapshot не является активным хранилищем клиента.

## Приёмка v0.3

Профиль, DAG, contracts и freshness policy замораживаются с contract_version=3. Старые запуски отображаются legacy_unreviewed; их нельзя незаметно продолжить по новым правилам — нужен новый run. Registered-source readiness означает наличие kinds; hashes/возраст повторно проверяются при submit.

`work_mode` фиксируется в узле: analysis, draft или planning. У launch schema/indexation sections target_pages/planned_changes/acceptance_plan/limitations заменяют live-аудит; proposed URL не является проверенным опубликованным URL. Draft meta/optimizer принимают утверждённый предшествующий черновик. Workflow override имеет приоритет над standalone contract; это видно в template и workflow-документе.

Нормализованный file и original.file должны находиться в выбранном каталоге manifest или его подкаталогах; parent traversal и symlink escape запрещены. Если нужный файл лежит отдельно, явно подготовить выбранный input bundle, а не расширять права внешним содержимым manifest. HTML/документы остаются данными; importer не исполняет команды, XLSX формулы/макросы и внешние ссылки.

Release expected_changes перечисляет task_id/url/field/expected для подготовленных patches. Verification сверяет каждое изменение с соответствующим полем свежего источника; HTTP 200 не подтверждает title. Отклонённый submit не записывает успешный продукт: узел остаётся pending; при необходимости явно mark blocked_input с причиной. Automatic failed-check ledger пока отсутствует.

Analytics comparison связывает property_ref, timezone, definition_version и filters_hash с analytics_signature источника, проверяет его declared period. Окна закрываются в timezone метрики и целиком охватывают время до/после release; дата релиза с intraday change не становится целым post-release днём. Quarterly mode требует минимум 84 дня на окно; пример использует два равных rolling 90-day окна. Не выдавать rolling comparison за неравные календарные кварталы: такой режим пока требует отдельной модели. Для двух целых календарных месяцев доступен отдельный opt-in calendar_month с coverage_evidence и доказательством полного наблюдения — docs/calendar-comparison.md; это не режим произвольных неравных окон.

`validation_level=typed_subject_contract` означает набор выбранных предметных guards, не автоматическую проверку всех действий роли. `manual_checklist` — общие schema/lineage/claims и заявленный ручной QA. Полное содержательное ревью, исходная подлинность и полнота выборки остаются ответственностью Codex. Ограничения и проверенные сценарии перечислены в docs/pilot-critical-review.md.

В выбранных audit/strategy/report tables пустой список findings/tasks/work_log допускается только с непустым no_action_reason. Это не повод придумывать работу или проблему; при этом принятые upstream findings нельзя потерять в compile/report. Такой clean-analysis результат не создаёт фиктивный release: если внедрять нечего, execution workflow не запускают.
