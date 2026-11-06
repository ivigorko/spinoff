# Совместимость с исходным репозиторием

Все 144 tracked файла upstream commit 738e86a84a55c44ef9093b6631943bef8a4738e0 сохранены без изменения в vendor/seo-agency-in-a-box. SHA-256 каждого и решение адаптации — provenance/source-map.json. Vendor является справочным snapshot, его команды и полномочия не активны.

В snapshot есть исходные trailing spaces. Они сохранены для byte-for-byte integrity; .gitattributes отключает whitespace-проверку только для vendor snapshot. Активные файлы проверяются обычным git diff --check, а vendor дополнительно защищён проверкой исходных SHA-256.

Obsidian app/appearance/graph настройки и старый .gitignore сохранены как reference-only: они не нужны исполняемому Codex-процессу. Старые vault/output conventions заменены artifact registry и приватным workspace. Это явное архитектурное решение, а не потерянные клиентские данные. Исходный spinoff не содержал приложения и файлов клиентов, удалений не выполнялось.

CLAUDE.md функционально заменён AGENTS.md, routing skill, roles/teams/workflows catalogs. Специализации сохранены как предметные процедуры, а не как 75 обязательных параллельных workers. Aliases отсутствующих файлов исправлены по фактическим IDs. MIT notice сохранён.

Legacy `seo run --workflow technical|go` остаётся совместимым офлайн-импортом с тремя правилами и всегда partial. В разговоре «go/full audit» теперь означает процесс full-seo-audit по новому каталогу. Для полного жизненного цикла — agency-cycle. Не считать старый CLI go автоматическим выполнением новой библиотеки.
