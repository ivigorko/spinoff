# Инвентаризация spinoff

Проверено 06.11.2026 в /workspace/spinoff. Origin: https://github.com/ivigorko/spinoff.git. Исходный HEAD и origin/main: 62822d3768a2827607842ea1ad1cc8281609b8f2, Initial commit. Локальная стартовая ветка work. `git ls-remote --heads --tags origin` показал только main; tags нет. В доступной истории один коммит. `git ls-tree -r HEAD` показал единственный README.md с текстом `# spinoff`.

В исходном дереве нет приложения, зависимостей, CI, deployment-конфигурации, submodules, AGENTS.md или .agents/skills. В доступных /workspace/.agents и .codex инструкций и skills не найдено. Удалять нечего. README расширен с сохранением исходного заголовка. Работа ведётся в локальной codex/seo-system-foundation; main и production не менялись.

Это проверка доступного Git-дерева, локальной/удалённой истории и признаков использования в репозитории. Настройки GitHub deployments/environments, внешние CI и ссылки из всех других приватных репозиториев не проверены. Отсутствие кода не доказывает отсутствие любых внешних ссылок. Никаких файлов по предположению не удалено, никаких production-настроек не изменено.

Upstream получен отдельно в /workspace/upstream-seo, commit 738e86a84a55c44ef9093b6631943bef8a4738e0. Прочитаны CLAUDE.md, data-flow/flow, full-seo-audit, quality gate, site-crawler, priority-matrix-builder и roadmap-planner. Найденные роли/пути рассматриваются как исходная библиотека; весь upstream не копировался.

Исходное ТЗ получено из Library через текущий Library skill, материализовано в /workspace/source-materials/SEO_система_Codex_Лабрика_обновлено.md. Размер 98333 байт; SHA-256 09266bab433b95ca4d45dfe5dbd5a4904de1ad465b8a66d41004b9cb930ce318. library_file_id: libfile_ca5fad5e72b88191a365a3e83d3b9742, version 0. Полный черновик не добавлялся в Git; его происхождение зафиксировано в provenance/upstream.json.
