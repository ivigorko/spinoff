# Хранение и состояния

Адаптация vault/README.md и исходных dashboard conventions. Git содержит исходники, contracts, активные инструкции, preserved vendor, синтетические fixtures и тесты. Клиентские raw/normalized/results/state/credentials остаются в приватном workspace, не в Git.

Технический срез: `projects/<project>/runs/<run>/...`, state.sqlite3. Процессная библиотека: `projects/<project>/processes/<run>/{frozen.json,sources,products}`, process-state.sqlite3. Между этими двумя подсистемами нет скрытого auto-import: полученный normalized dataset явно регистрируется как source с правильным origin/locator/hash и schema. Не переносить состояние по одному имени файла.

Process source — проверенный локальный нормализованный JSON, оригинальный provider export сохраняется отдельно. Product — неизменяемый JSON с role, предметными sections, input IDs, claims и critical QA. Coordinator фиксирует nodes, source/product hashes, parent IDs и события в транзакции одного локального писателя. Принятый продукт не редактируется; исправление — новый run/version.

Рекомендуемое постоянное хранилище материалов — Drive по разрешённым project folders и fileId/version. Session read/export подтверждён, write adapter/outbox/reconciliation/restore ещё не реализованы. Не хранить активную SQLite в Drive-sync и не называть local_validated результат uploaded/verified in Drive.

Dashboard и ROI tracker теперь шаблоны по реальным состояниям/расчётам. Они не являются live monitoring или доказанным финансовым эффектом. Приватный диск выбранной среды и резервное копирование должны быть подтверждены для долговременного использования.
