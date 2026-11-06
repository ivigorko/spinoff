# Полный рабочий цикл

Источник: upstream instructions/flow.md. Функциональная адаптация для Codex, без обязательного запуска множества агентов. Каталог: seo_system/config/processes.json. `agency-cycle` связывает весь цикл; `full-seo-audit` ограничен анализом и планом, не публикацией.

| Фаза | Триггер / обязательные входы | Действия и выход | Gate / ограничения |
|---|---|---|---|
| Onboard | Новый проект или изменение scope; поручение и факты бизнеса | Бриф, versioned profile, goals/conversions, brand voice, competitors, resources, source inventory | Не угадывать домен; неизвестное фиксировать; onboarding/onboard.md |
| Research | Нужны новые решения; профиль и доступные данные | Market/search updates/SERP/AI research, keywords, intent, clusters, конкурентное покрытие | Минимальные зависимости; technical crawl не блокируется несвязанным market research |
| Audit | Нужен аудит; свежие конкретные datasets | Technical, content, links, AI и применимые local/ecommerce findings; compiled inventory + coverage | Нет источника — blocked/partial; не подменять index status, backlink database или CWV эвристикой |
| Strategy | Принятые findings и цель | Pillars, KPI/baseline, risk, priorities, resource roadmap и checkpoints | Не выдумывать часы, доход и обещания роста; неизвестные ресурсы дают сценарии |
| Execute | Выбранные задачи и актуальная revision | Prepared diff/content, tests, rollback; отдельно разрешённый фактический release | JSON не выдаёт полномочия. Координатор не делает apply/publish. Release требует evidence реального действия |
| Verify / Measure | Реальный release и ожидаемые значения | Новые post-release URL checks; затем сопоставление закрытых периодов | Публикация ≠ исправление; verified ≠ рост SEO; awaiting_measurement/inconclusive допустимы |
| Report / Refresh | Принятые результаты и журнал работ | Месячный/квартальный отчёт, decisions continue/change/stop, версия стратегии и следующий backlog | Не отправлять отчёт автоматически. Новый цикл/расписание только в разрешённом объёме |

Частичная задача выбирает `role:<team.name>`, `team:<name>` или нужный workflow. Она не обязана проходить все фазы. Ключевые связи: research→clusters→page mapping→brief→draft→QA; audit→compiled findings→recommendations→priority→roadmap; selected task→prepared→release evidence→fresh verify→measurement→report→strategy refresh.

`seo process plan --workflow <id>` раскрывает DAG и контракты. `start` замораживает профиль/процедуры; `source` регистрирует разрешённые локальные JSON evidence; `template` даёт незаполненный каркас; Codex выполняет процедуру; `submit` проверяет структуру, зависимости и evidence. Готовый продукт неизменяем. Исправления и новый цикл дают новую версию/run.

Полный цикл может ожидать фактический release и аналитическое окно. Это нормальный реальный статус, а не повод генерировать фиктивный release или measured результат. Во время разработки проверяется synthetic fixture с явной маркировкой, а не production.
