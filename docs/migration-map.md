# Адаптация upstream

Это семантическая адаптация выбранных producer/consumer, не перенос всех 75 prompt-файлов. Pin и точные исходные файлы — provenance/upstream.json. MIT notice сохранён. Публикации и обновления upstream автоматически не выполняются.

| Исходный producer → consumer | Старые пути/правило | Новое решение | Состояние |
|---|---|---|---|
| CLAUDE.md/onboarding → все команды | vault/01-Clients/[client]/profile.md, site-info/goals | JSON profile + AGENTS + preflight; нет фиктивного scrape onboarding | Работает локально |
| technical/site-crawler → technical/audit | vault/10-Technical/[client]/crawl-data + output duplicate | immutable raw → normalized/pages → scoped registry | Импорт готового экспорта работает; crawl отсутствует |
| instructions/data-flow → audit/data-compiler | Читать все vault-секции, wikilinks | Только артефакты выбранного project/run; SHA resolver | Работает для технического среза |
| instructions/flow + CLAUDE go → audit/strategy | Research обязателен перед техническим; go не вызывает roadmap | Минимальный offline DAG + report/priority/roadmap/QA | Работает; go честно partial |
| _base/quality-gate + quality/qa-checklist → delivery | Средняя оценка >=3/5; двойное сохранение | Критические проверки блокируют; local_validated не Drive verified | Работает локально |
| audit findings → strategy/priority-matrix-builder | vault/08-Strategy/priority-matrix | deliverables/tasks.json + priority.md | Работает; нет выдуманной оценки дохода |
| strategy/roadmap-planner → client summary | vault/08-Strategy/roadmap; предположить 40–60h/month | roadmap.md с неизвестной мощностью и сценариями 30/60/90 | Работает локально |
| Content/links/AEO/local/ecommerce → audit | vault/04,05,09,11 и общие разделы | Будущие типизированные datasets; skills описывают gates | Не реализовано в CLI |
| Analytics/monthly report → strategy | vault/07-Reports + dashboards/ROI | Будущие baseline + release log + comparable measurements | Не реализовано; ROI не рассчитывается |
| deliverables → Drive | Нет надёжного fileId/revision протокола | Отдельный будущий outbox/reconciliation adapter | Не реализовано |

Единая политика свежести вместо нескольких противоречащих prompt-правил. Ни один старый vault/output путь не используется исполняемым кодом. Процедуры внедрения и измерения описаны отдельно и не выдают публикационные полномочия.
