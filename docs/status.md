# Фактическое состояние v0.2 — 06.11.2026

Ветка codex/seo-system-foundation. Первые коммиты 2357b5d/e7bce23 содержали только технический срез; после поимённой сверки выполнена полная функциональная адаптация библиотеки процедур. Исходный spinoff и upstream сохранены, удалений нет. Main, production, push/PR/deployment не затрагивались.

## Покрытие переноса

| Компонент | Фактическое состояние |
|---|---|
| 144 upstream файла | Сохранены побайтно в vendor; SHA-256 и disposition каждого в provenance/source-map.json |
| 75 специализаций | Предметные процедуры с назначением, триггером, required/optional inputs, действиями, sections, completion, QA и ошибками; roles.json + procedures/roles |
| 12 leaders | Командные DAGs, порядок и обязанности приёмки/передачи; teams.json, procedures/leads и team-инструкции |
| 17 исходных инструкций | Все получили активные функциональные адаптации; единые scope/paths/gates и исправленные aliases |
| 11 workflows | Все адаптированы и связаны с coordinator; дополнительно agency-cycle и role/team selectors |
| Onboarding/base/QA/tool guides | Полный 19-вопросный охват и быстрый режим, profile schema, текущие SEO-решения и critical QA |
| 11 шаблонов + dashboards | Адаптированы как templates; unfilled template не является принятым результатом |
| 18 skills | Укрупнённые маршрутизаторы и командные входы; они загружают конкретные предметные процедуры, не заменяют их краткими общими обещаниями |

Часть исходных инструкций сознательно изменена: средняя quality score не перекрывает критический провал; нет универсальных word count/density/link quotas, гарантированного ROI/роста и автоматического disavow; Google FAQ rich-result promises исключены по актуальному changelog. Источники и решения C01–C16 — instructions/currentness.md. Obsidian settings/legacy ignore conventions сохранены reference-only с объяснением, а не выданы за активные функции Codex.

Полная человеческая трассировка: docs/migration-map.md. Машиночитаемая: provenance/source-map.json. Эти документы описывают адаптацию функций, а не буквальное сохранение устаревших команд и обещаний.

## Что исполняется автоматически

- Локальный process coordinator: frozen profile/plan/role contracts, DAG, зависимости, ready/blocked/partial/completed, неизменяемые sources/products, hashes, scoped registry, parent IDs и события.
- Проверки work-product schema, required sections, input IDs, source scope/freshness, фактических значений claims по JSON pointers, synthetic/client isolation и critical checklist.
- Client evidence сохраняет и проверяет оригинальные байты и normalization provenance наряду с normalized JSON. Правильность ручного mapping не выводится из совпадения hash.
- Release record сверяется с source evidence, task/URL scope и baseline подготовленных изменений. Проверка production требует новых данных после release на target revision, expected/actual и покрытия URL; post-migration audit не принимает старые pages.
- Measurement проверяет values/definitions/scope/units, закрытые сравнимые окна, zero denominator, расчёт изменений и связь post-release окон с release. Unknown values не становятся measured.
- Существующий автоматический технический pages import JSON/CSV/XLSX: HTTP errors, пустые title/H1, findings→report/priority/roadmap/QA. Он остаётся отдельным partial-срезом; legacy CLI go не заменяет полный workflow.

## Что выполняет Codex по готовым процедурам

Все предметные research/audit/keywords/content/links/AI/local/ecommerce/strategy/analytics действия и содержательное ревью. Coordinator не является автономным SEO-аналитиком: заполнение sections и флаг QA не доказывают правильность анализа, подлинность источника или будущую SEO-эффективность. Codex обязан прочитать процедуру, получить реальные разрешённые данные, выполнить действия и проверить выводы до submit.

Применение, публикация, отправка и доставка результатов выполняются только подходящим реальным инструментом в действующем поручении; coordinator лишь регистрирует их evidence. Authorization_ref в JSON не выдаёт полномочия. Synthetic release в тесте не означает внешний deployment.

## Проверено

- Python 3.12.14, uv 0.12.23; uv sync --frozen.
- 59 unittest tests прошли. Включены все 11 исходных workflows и agency-cycle на явно synthetic fixtures; dependency/partial gates, source/product immutability, project/market isolation, hashes/freshness, raw original preservation, claims/QA, отсутствие скрытой подмены synthetic/client, release/verify/post-migration/measurement negative cases и zero denominator.
- Сквозной пример несёт один finding→task→prepared patch→release→fresh title verification→сравнение 100/120→report→strategy refresh/next backlog. Это вымышленные contract fixtures, не реальный SEO-кейс и не причинное доказательство результата.
- render_playbook.py --check, check_playbook.py, limited repository guard и git diff --check прошли. Inventory checker сверяет 144 оригинала, targets, 75/12/11 coverage и все selectors/DAGs.
- Собраны spinoff_seo-0.2.0.tar.gz и wheel. Source archive содержит все 144 preserved sources, активные procedures/skills и onboarding. Wheel установлен отдельно; plan/start/mark/source/template/submit/status прошли smoke из установленного пакета.
- Дополнительно выполнен synthetic agency-cycle: process-725373b09d474338ae0e, 20 принятых узлов, status completed, synthetic=true, external_actions_performed=false. Его summary находится только в игнорируемом workspace/agency-cycle-v02-final-summary.json.

Тесты подтверждают контрактную связность и реализованные gates. Они не доказывают, что любая будущая ручная работа выполнена качественно, что все источники доступны или что сайт получит рост.

## Внешние интеграции и оставшиеся ограничения

- Через инструменты сессии проверены Drive search/read/native Sheets→XLSX export существующих файлов. Write/storage adapter, fileId/revision reconciliation, outbox/restore и длительное хранение не проверены/не реализованы.
- В GSC discovery нет active connection. У Yandex есть active generic connection, но конкретные counter/host reads не подтверждены. Релевантный Labrika tool не найден; UI-доступ не подтверждён. Детали — docs/access-verification.md. Эта разработка не создавала accounts/tokens и не запускала платные проверки.
- Автоматические CLI-адаптеры keyword/analytics/AI/provider reports и их индивидуальные нормализаторы ещё не реализованы. Разрешённые реальные данные можно явно нормализовать Codex в source-backed JSON с оригиналом/mapping; произвольный отчёт не считается pages dataset.
- Нет multi-worker DB/leases/fencing, фонового scheduler, автоматического deployment/crawl или live SEO monitor. SQLite — один локальный писатель, без distributed guarantees. Recovery и резервное копирование локального диска требуют соблюдения runbook.
- Это ограниченный pattern-based secret/data guard, не exhaustive security scan или DLP. Клиентские файлы, credentials и state вне Git.

## Ближайший следующий этап

Адаптация процедур завершена; теперь уместен ограниченный пользовательский пилот: выбрать сайт, цель и пригодный существующий отчёт/источник, заполнить полный профиль, проверить реальные поля/даты/scope и пройти выбранный workflow. Новые аккаунты и все API для этого не обязательны. Storage adapter и отдельные прямые API расширяются по фактической необходимости и правам. Ни сайт пилота, ни production-изменение, ни paid audit в этой работе не выбирались и не выполнялись.
