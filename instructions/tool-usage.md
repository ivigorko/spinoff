# Провайдеры и разрешённые действия

Источник: upstream instructions/tool-usage.md. Логическая операция важнее конкретной покупки или бренда инструмента.

| Потребность | Предпочтение | Что проверить |
|---|---|---|
| Уже готовые данные проекта | Пригодный существующий экспорт/подключение | Scope, source date, columns, completeness, original origin |
| Технические страницы/рекомендации | Доступный отчёт Labrika, crawl export либо разрешённое ограниченное чтение | Ошибки не равны полному URL inventory; новый анализ может расходовать квоты |
| Позиции/ядро/кластеры/конкуренты | Проверенный отчёт Labrika, Wordstat, GSC или эквивалент | Engine/region/device/date, frequency method, selected query universe |
| Аналитика | Метрика/GA4/GSC конкретного counter/property | Definitions, filters, period closure, sampling/top-row limits, attribution |
| Ссылки | Dataset нужного типа | Internal/outbound/inbound различны; поисковые примеры не полная база backlinks |
| AI | Существующие наблюдения Labrika/платформы и отдельные GEO recommendations | Prompt/platform/answer/time/mention/citation/method; отдельные лимиты |
| Crawl/extract/search | Доступный допустимый provider, включая Firecrawl/Tavily при наличии | Авторизация, лимит, robots/ToS, audience, расход; general search не измеряет точный SERP |
| Хранение | Разрешённая папка Drive после проверки записи | fileId/version/checksum, reconciliation и отсутствие ACL-расширения |

Наличие tool или OAuth app client ID не означает активное соединение, нужный account scope и доступ из CLI. Для каждого отчёта фиксировать documented/account/executor/export/API verified отдельно. Не подключать новые accounts автоматически ради прохождения процедуры.

Перед новым сбором проверить registry и пригодность уже имеющихся источников. Для нового crawl сначала оценить объём и лимиты; собирать только разрешённые домены/страницы, не отправлять формы. После 401/403 не обходить запрет; после неопределённого внешнего write сначала сверить факт выполнения.

В этой задаче новые paid calls и production запрещены. Координатор работает с локальными файлами, не выполняет network calls и не создаёт accounts. Codex может пользоваться разрешёнными инструментами сессии, фактическое состояние — docs/access-verification.md. Инструкции подключения конкретного API перед реализацией сверять с его первичной документацией и правилами среды.
