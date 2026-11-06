# Фактическое состояние — 06.11.2026

Локальная ветка: codex/seo-system-foundation, исходная база 62822d3768a2827607842ea1ad1cc8281609b8f2. Удалений нет; main и production не менялись. Push/PR/deployment не выполнялись.

## Реализовано

- Корневой AGENTS.md, семь .agents/skills, правила полномочий/источников/качества, карта миграции выбранных upstream producer/consumer. Upstream pin, MIT notice и SHA исходного ТЗ сохранены.
- Python CLI plan/preflight/run/status/resolve. Исполняемый объём — один pages import в технический workflow; go выполняет тот же частичный срез и явно показывает отсутствующие модули.
- JSON Schema для profile, source manifest, pages, finding, task, artifact. Явный mapping для CSV/XLSX, лист XLSX, оригинальные raw, даты, provenance, scope, revision, checksum и coverage.
- SQLite для одного локального писателя: runs, artifacts, tasks, events; атомарная регистрация принятого пакета, fingerprint по входам/политике/реализации/схемам, reuse с проверкой хэшей, scoped artifact resolver. Не многопользовательская очередь.
- Три детерминированные проверки: HTTP ошибки и пустые title/H1. Evidence до строки набора, QA, отчёт/приоритеты/roadmap/tasks/coverage; отсутствующие данные не выдумываются.
- Воспроизводимое synthetic demo, uv.lock, тесты и ограниченный Git data/secret guard. CI подготовлен; удалённый workflow не запускался.

## Проверено

`uv sync --frozen` выполнен в новой .venv, Python 3.12.14 / uv 0.12.23. `uv run python -m unittest discover -v`: 23 теста прошли. Проверены E2E/evidence/roadmap, reuse после открытия новой SQLite connection, неверные project/host/checksum/count/types, дубликаты, stale/future timestamps, revision drift, отсутствие полей, CSV mapping, XLSX sheet/formulas, ложная evidence, повреждённые выходы, orphan directory и CLI plan/preflight.

`python scripts/check_repository.py` и `git diff --check` пройдены. `uv build` создал sdist и wheel; wheel установлен в отдельную /workspace/spinoff-wheel-test, из /tmp выполнены plan и полный offline run с packaged schemas/config. Демо выполнено без сети SEO-сервисов; результаты синтетические. Эти проверки не подтверждают формат реального отчёта Labrika, аккаунтный доступ, устойчивость диска или запись в Drive.

Принятый synthetic go: run-4c8d73890832c11f3190 в workspace/demo-state/projects/synthetic-demo/runs/. Три строки дали три finding/task: HTTP 503, пустой H1 и пустой title. Сформированы report/priority/roadmap/coverage/QA; повтор run вернул reused=true и тот же run ID. Workspace игнорируется Git и не содержит реальных клиентских данных. Сборки лежат отдельно в /workspace/spinoff-build; это локальные файлы, не опубликованные пакеты.

## Ещё не реализовано или не проверено

- Реальный профиль пилота, цели бизнеса и доступная мощность команды не получены. Демо не подставляется вместо клиента.
- Drive adapter, write/read smoke test, fileId/revision mapping, upload outbox/reconciliation, восстановление workspace из Drive. Текущий диск не подтверждён как долговременный.
- Реальные форматы/смысл столбцов нескольких типов Labrika отчётов. Поддержан контейнер pages JSON/CSV/XLSX с mapping, а не универсальный импорт Labrika. Позиции/семантика/конкуренты/ссылки/AI требуют отдельных schemas, normalization и findings.
- Прямые API Labrika, GSC, Вебмастера, Метрики/Wordstat/GA4; live crawl/search, квоты, OAuth и права на properties.
- Полные JSON schemas для run/change/analytics/keywords/AI и state tables permissions/changes/outbox/lineage с полноценными переходами. Текущие skills и шаблоны описывают процесс; это не его полная автоматизация.
- Произвольный DAG planner, partial dependency policy, retries/leases/fencing, несколько workers и распределённое состояние. SQLite держит локальную транзакцию на весь run; не предназначена для долгих сетевых задач.
- Программное apply/publish/production verification/measurement и расписание. Патчи и измерения выполняются лишь по конкретным будущим поручениям и проверенным входам; этот релиз их не делает.
- Полное DLP/secret scanning и exhaustive security review. Локальный guard проверяет ограниченные паттерны; staged diff необходимо просматривать.

Это полезная часть этапа 1 исходного ТЗ, а не выполнение всех критериев этапов 0–5. Для частичных результатов не заявлять готовность полной SEO-системы.

## Ближайшие действия

1. Выбрать один пилотный сайт и готовый отчёт Labrika; заполнить профиль и scope. Проверить фактические листы, столбцы и дату анализа; добавить обезличенный контрактный fixture без клиентских данных. Пройти реальный technical import.
2. Указать разрешённую папку Drive. В среде с действующим доступом выполнить write/read smoke test и реализовать storage adapter/outbox; только после этого считать хранилище подключённым.
3. Выбрать следующий реально полезный тип отчёта (позиции/семантика/аналитика), добавить schema/adapter/QA и совместимость provenance. Не запускать новые платные анализы без полномочий.
4. По конкретной принятой задаче подготовить первый патч с тестами/rollback; применить в разрешённой среде, проверить production и согласовать измерительное окно.
