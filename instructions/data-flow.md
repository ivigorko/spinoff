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
