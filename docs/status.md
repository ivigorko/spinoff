# Обновление 08.11.2026: действующий operating gate

Пользовательский порядок Нины объединён с техническими процедурами: instructions/operating-policy.md, docs/operating-policy-review.md. Contract4 закрывает обходы через role/team, источники и legacy execute; пять файлов карточки и handoff не заменяются profile.json. QA и локальный completed отдельно от реальной приёмки Ниной. Основной DAG — 32 узла с market/algorithms/competitors до семантики/аудита. Подробная библиотека и строгие source/subject/measurement guards сохранены.

Доверенный reader решений Нины/Игоря, shared queue и Drive adapter отсутствуют. CLI не принимает произвольный JSON approval; client gates без проверенных внешних решений закрыты. Позитивные client-format tests используют фиктивный test reader, не Нину. Не заявлять working multi-user orchestration, Grok skills transfer или автоматическую публикацию. Клиентские материалы и состояния этим обновлением не менялись; старые snapshots legacy_unreviewed не мигрированы молча.

Ниже — предыдущая техническая инвентаризация, читать с указанным новым ограничением.

# Текущее состояние v0.4 — 08.11.2026

Исправлены две проблемы реального аналитического пилота: добавлен явный режим `calendar_month` с source-backed полным наблюдением и разъяснён scope legacy technical CLI в instructions/data-quality.md. Прежняя защита равных окон по умолчанию сохранена; произвольные неравные периоды не допускаются. Контракт, проверки и пределы — [calendar-comparison.md](calendar-comparison.md).

109 unittest tests проходят, включая 23 новых calendar-month cases: полные 30/31 дней, leap/nonleap February, дата начала/конца и timezone, missing/duplicate/unknown daily data, gaps, поздний запуск, несовместимые scope/signature/period, источник coverage, нулевая база и реальный coordinator submit/rejection. Оба режима проходят общий контроль deltas и источников.

На тех же копиях реального пилота повторены 204 проверки данных, 43 независимые XML-проверки и 60 числовых сопоставлений: 59 прямых совпадений и одно условное, без числовых расхождений. Три зарегистрированных клиентских продукта остались partial. Новый calendar_month диагностический submit без первичных свидетельств observation coverage отвергнут, продукта не создал и отмечен blocked_input. Новые функциональные возможности не подменяют отсутствующие исходные данные или проверенность API.

Клиентские файлы и подробный повторный протокол сохранены только в игнорируемом workspace; код/документация не содержат их payload. Исходные клиентские источники, сайт, рабочие документы и Grok не менялись. В рамках этой доработки push/publication/deployment не выполняются.

Ниже — исторический статус v0.3; его число тестов и ограничения календарного режима относятся к той версии.

## Историческое состояние v0.3 — 06.11.2026

Ветка `codex/seo-system-foundation`. Сохранены исходный spinoff и pinned upstream; удалений нет. Main/production, push/PR/deployment не затрагивались. v0.3 исправляет подтверждённые ошибки приёмки и уточняет прежние заявления о полноте v0.2. Подробная сверка каждого workflow и representative ролей — [pilot-critical-review.md](pilot-critical-review.md).

## Что перенесено

144 upstream файла сохранены побайтно; source map содержит hashes, активные targets, режим и явные review limits. Каталог содержит 75 специализаций, 12 лидеров, 17 исходных инструкций, 11 workflows, onboarding/base/QA/tools/templates и 18 skills. Это доказательство инвентаризации и процедурной адаптации. Оно не доказывает автоматизацию и экспертное качество каждого направления.

Для всех процессов есть назначение/триггер, входы, зависимости, действия, предметные выходы, условия перехода, QA/ошибки. Схемы/методические правила обновлены C01–C17; quotas, обещания роста/агентской стоимости, автоматический disavow и retired search features не перенесены как действующие требования. Трассировка — [migration-map.md](migration-map.md), `provenance/source-map.json`.

## Что исполняет код

- Локальный process coordinator: frozen profile/DAG/contracts/freshness policy, scoped registry, source/product hashes, immutable products, input IDs, states/events, partial propagation. Ready показывает зарегистрированные kinds; submit повторно проверяет evidence.
- Generic work-product schema/lineage/claims и critical checklist для всех ролей. Для выбранных ролей дополнительные предметные guards в `subject_gates.py`: clusters/keyword facts, drafts/metadata, inventory/CWV, inbound links/NAP/catalog/JSON-LD, findings/tasks/patches/report, traffic/ROI/work log. `validation_level` явно отличает typed checks от manual checklist. Проверенные поля не означают автоматическое ревью всей роли.
- Draft и planning режимы с workflow overrides: content sprint и launch работают без опубликованных pages; launch plans помечены proposed. Campaign report сохраняет register/drafts/tracking plan и не выдаёт их за отправку/мониторинг.
- Release expectations связаны с patches; fresh verification проверяет действительные поля и expected values всех изменений. HTTP 200 не подтверждает title. Source revision/time обязательны. Measurement проверяет property/timezone/definitions/filters/source period, арифметику, закрытые равные окна и точное bracketing релиза.
- Источники сохраняют normalized JSON и original bytes/provenance; пути обоих ограничены выбранным input bundle, включая symlinks. Достоверность первичного источника/ручной нормализации не следует из SHA.
- Отдельный технический pages import JSON/CSV/XLSX проверяет HTTP/title/H1 и строит partial report/priority/roadmap. Это не полный SEO-анализ. Старый CLI go остаётся partial alias.

Старые snapshots обозначены `legacy_unreviewed` и не принимают новые submits: нужен новый run. Неудачный submit не записывает успешного продукта; узел остаётся pending до исправления или явного mark blocked. Failed-submit audit ledger пока отсутствует.

## Что исполняет Codex вручную

Получение разрешённых данных доступными инструментами, нормализация неподдержанных provider exports, предметное исследование, диагнозы, стратегии, тексты, полное содержательное ревью и финальная приёмка. Coordinator не заменяет эти действия. QA=true остаётся декларацией исполнителя. Не все 75 роли имеют typed gates и негативные предметные тесты.

В предыдущем contract3 agency-cycle содержал 30 узлов (текущий contract4 — 32, см. выше): onboarding/market, все ветки full audit, strategy/roadmap, preparation/release/verify/measurement/report/refresh/next roadmap. Это исполняемый coordinator DAG, а не автономный SEO-аналитик. Тестовая цепочка несёт один fictional finding→task→title patch→release→fresh title→100/120 comparison→refresh. Остальные outputs сокращённые contract cases, не клиентские deliverables.

Применение/публикация/доставка требуют фактического инструмента и полномочий в поручении; JSON authorization_ref их не выдаёт. Никаких внешних изменений coordinator сам не выполняет.

## Проверено

- 86 unittest tests проходят, из них 27 новых pilot-review tests. Все 11 upstream workflows и agency-cycle проходят настоящие start/source/template/submit/status; дополнительно проверены вызовы submit, реальные products/completed events в SQLite и передачи artifact IDs.
- Отрицательные проверки ловят garbage clusters, выдуманные frequency/CWV/NAP/цены/ROI, outbound вместо inbound, неверные task dependencies, before state, неподтверждённые work statuses, HTTP 200 вместо title, field pointer mismatch, выход manifest/original за input bundle, analytics signature/period и intraday release overlap.
- Content sprint и launch проходят без pages; live observations в planning отклоняются. Quarterly rejects 28-day windows; пример использует два rolling 90-day окна. Неравные календарные кварталы пока отдельный неподдержанный режим.
- `render_playbook.py --check`, `check_playbook.py`, `check_repository.py`, `git diff --check`. Inventory checker проверяет bytes/targets/contracts/DAGs; это не доказательство экспертной полноты.
- Собраны wheel/sdist v0.3.0. Wheel установлен отдельно в spinoff-wheel-test: импорт из site-packages, CLI plan и 30-node agency-cycle завершились успешно, synthetic=true, external_actions_performed=false. Source archive содержит все 144 vendor originals, локальный AGENTS boundary marker, review report и regression tests. Исторический build v0.2 и старый 20-node summary не являются доказательством текущих contracts.

## Подключения и блокеры

Session Drive search/read/native Sheets export подтверждены предшествующими read probes. Автономный CLI storage/write/reconciliation/restore adapter отсутствует. GSC active connection не обнаружено; Yandex generic connection не подтверждает counter/host reads. Labrika usable tool/UI session не подтверждены. Полные детали — [access-verification.md](access-verification.md). Новые accounts/tokens/платные проверки не создавались.

Нет multi-worker leases, scheduler, deployment, live SEO monitor, универсальных provider-format нормализаторов и реального клиентского сквозного кейса. SQLite рассчитана на одного локального писателя. Secret/data repository guard ограничен паттернами, не является полным DLP/security audit.

Возможен ограниченный пилот: однозначно выбранный сайт/цель, разрешённый существующий dataset с проверенными датами/scope и ручная приёмка каждого предметного результата. Недоступные модули остаются blocked/partial. Production apply, live verification и измерение результата не считаются выполненными по synthetic fixtures. Все API заранее не требуются; новые доступы нужны лишь для конкретного шага.

Итоговая сверка с каждым из 20 разделов исходного ТЗ от 07.11.2026 — [requirements-review.md](requirements-review.md). Drive storage, реальные provider adapters и клиентский closed loop остаются незавершёнными этапами ТЗ. Публикация отдельной ветки разрешена новым поручением Игоря; прежнее ограничение на непрошеную публикацию не блокирует этот push.
