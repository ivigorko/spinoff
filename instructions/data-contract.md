# Контракт данных

JSON Schema находится в seo_system/schemas; формат конфигурации MVP — JSON, а не предложенный в черновике YAML. `schema_version=1`. CLI не принимает произвольные поля: неподдержанные поля не должны молча исчезать.

Полная процедурная библиотека v0.2 использует дополнительно process-source/work-product/release-record/comparison schemas и каталог roles/operations/teams/processes. Подробный producer/consumer контракт — instructions/data-flow.md. Этот документ далее описывает совместимый автоматический pages-срез; его finding/task schema не является универсальной схемой всех SEO-направлений.

Профиль: project_id, профиль/ревизия сайта, домены и allowed_hosts, цель, market с регионом/языком/engine/device, timezone, неизвестные Drive ID и мощность как null. Заполнять реальные значения до пилота.

Source manifest: source_id и source_locator, primary_origin, project_id, host, site_revision, source_generated_at и collected_at с timezone, формат, локальный file относительно manifest либо абсолютный путь, SHA-256, число строк и coverage. Пользователь импортирует только файлы, доступ к которым разрешён. Файл не скачивается автоматически из указанного пути.

JSON pages — массив URL и числовых status_code; title и h1 опциональны. Отсутствующий ключ означает «не измерено», пустая строка — измерено пустое значение. CSV и XLSX требуют column_mapping: каноническое поле → точное имя исходного столбца. XLSX требует sheet, CSV — явный delimiter при отличии от запятой. Исходные байты и mapping сохраняются. Типы не угадываются; преобразование HTTP-кода из трёх цифр CSV документировано. Формулы XLSX отвергаются; макросы не исполняются. Максимум 20 MiB, 100000 строк, распакованный XLSX 100 MiB. Это механизм импорта; фактический mapping конкретной выгрузки Labrika ещё не подтверждён.

Логические пути: projects/<project_id>/runs/<run_id>/{raw,normalized,findings,deliverables}. SQLite хранит реестр, статусы узлов и события в отдельном локальном workspace. Resolver принимает project + run + artifact ID, проверяет scope и checksum. Не искать «самый новый файл». Каждый запуск фиксирует профиль, source manifest, hash реализации и fingerprint; одинаковые входы переиспользуют проверенные результаты. Изменение схемы требует новой версии пакета и повторной проверки импорта.

`row_index` evidence — индекс с нуля в нормализованном pages. Для CSV/XLSX он соответствует порядку непустых импортированных строк, а не обязательно номеру строки Excel. Сверка выполняется с normalized/pages.json; raw и mapping позволяют восстановить происхождение. В findings сохраняется raw artifact ID.

`local_validated` — файл локально проверен. Это не статус Drive upload. Родительские ID и пути лежат в artifacts.json и SQLite; manifest.json фиксирует входы. artifacts.json служит экспортом реестра, не отдельным источником истины. Не хранить workspace в Git и не помещать активную SQLite в синхронизируемую папку Drive.
