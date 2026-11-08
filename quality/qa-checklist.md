# Предметный и общий QA

Адаптация upstream quality/qa-checklist.md. Шесть critical check IDs work-product: scope, evidence, domain_procedure, currentness, permissions, completeness. Для каждого note сообщает, что реально проверено.

| Направление | Обязательная содержательная проверка Codex |
|---|---|
| Research | Даты/рынок/метод; первичные источники; наблюдение отдельно от оценки рынка/причины |
| Keywords/SERP | Query universe, engine/region/device/time; real volume/rank vs candidate; intent/mapping и дубли |
| Technical | Полнота crawl/graph; robots/canonical/index status отдельно; rendered проверки и реальные performance observations |
| Content | Принятый brief/intent, brand voice, проверенные факты, уникальная польза, metadata/links; никаких фиктивных экспертов/отзывов |
| Links | Тип inbound/outbound/internal, provider coverage, проверенные placements; отсутствие автоматического disavow/покупки/рассылки |
| AI | Prompt/platform/time/raw answer и конкретные mentions/citations; рекомендации не подменяют наблюдения |
| Local | Реальные локации/NAP, geo scope, reviews и rules платформы; отсутствие doorway и fake reviews |
| Ecommerce | Реальные catalog/price/availability/variants; feed-page consistency; действующая eligibility конкретного schema feature |
| Strategy | Цель, resources/unknowns, риск, dependencies, owner, acceptance, metric/window; сценарии не прогноз |
| Analytics | Counter/property, definitions, units, sampling, закрытые сопоставимые периоды, нулевой baseline и confounders |
| Implementation | Baseline revision, конкретный diff, тесты, rollback, действующее поручение, drift и фактический release |
| Verification | Новые данные после release на целевой revision; expected/actual и все затронутые URLs; failures не скрыты |
| Reporting | Все существенные числа разрешаются до источников; prepared/applied/verified/measured разделены; coverage и next decisions видны |

Нельзя принять незаполненный template, чужой проект, unsupported метрику, фиктивный external action или неполный результат под видом полного. Читабельность и эстетика проверяются дополнительно, без среднего «3/5 достаточно».

JSON Schema и coordinator не понимают полностью смысл SEO-текста: проходят только структурные/ссылочные/числовые gates и заявленный checklist. Reviewer обязан прочитать продукт и исходные observations; schema pass не означает экспертную правильность.


## Приёмка пользователя поверх технического QA

instructions/operating-policy.md: пять файлов карточки и реальная приёмка Нины обязательны до фаз. Оценка 1–5 и порог3 не отменяют critical checks и не доказывают приёмку. `completed`/local_validated/subject gates — технический результат; «Выполнено» — только по регламенту Нины, после второй проверки для выкладки. Отдельная роль, адаптер и synthetic mode для реального домена не являются исключениями. Доверенный reader внешних решений не реализован.
