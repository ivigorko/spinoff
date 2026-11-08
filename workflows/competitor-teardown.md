# Разбор выбранных конкурентов

Источник: `workflows/competitor-teardown.md`. Canonical DAG: `seo_system/config/processes.json`, ID `competitor-teardown`.

## Назначение и триггер

Запрос на разбор выбранных конкурентов.

## Входы и зависимости

- Однозначный список конкурентов и допустимый scope чтения.
- Сопоставимые snapshot данные; scraping не доказывает ranking/traffic.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `crawl` / research | `competitor.competitor-site-crawler` | Внешние входы | inventory, structure, coverage, findings |
| `keywords` / research | `competitor.competitor-keyword-analyst` | crawl | targets, observed_rankings, overlap, gaps |
| `content` / research | `competitor.competitor-content-analyzer` | crawl | sample, comparison, gaps, recommendations |
| `links` / research | `competitor.competitor-backlink-profiler` | crawl | coverage, domains, anchors, assets, opportunities |
| `serp` / research | `competitor.competitor-serp-tracker` | keywords | scope, positions, movements, opportunities |
| `technical` / research | `competitor.competitor-technical-benchmarker` | crawl | method, comparison, advantages, actions |
| `strategy` / strategy | `strategy.competitive-strategy-analyst` | keywords, content, links, serp, technical | landscape, attack, defend, differentiate, defer |
| `summary` / audit | `audit.executive-summary-writer` | strategy | state, risks, opportunities, decisions, next_steps |

Входы и режимы узлов (переопределяют standalone role только в этом workflow):

- `crawl`: competitors; режим `analysis`.
- `keywords`: competitors; режим `analysis`.
- `content`: competitors; режим `analysis`.
- `links`: backlinks; режим `analysis`.
- `serp`: serp; режим `analysis`.
- `technical`: competitors; режим `analysis`.
- `strategy`: business; режим `analysis`.
- `summary`: business; режим `analysis`.

На каждом узле выполнить предметную процедуру procedures/roles/<team>/<name>.md, её QA и work-product contract. Readiness рассчитывается coordinator; он не пишет экспертный результат вместо Codex.

## Условия перехода и завершения

Все обязательные узлы приняты; report/coverage отражают реально выполненное. Partial входы никогда не дают completed всего workflow.
При partial dependencies consumer обязан явно принимать неполноту; итог остаётся partial. Optional-модуль исключается только с предметным обоснованием. Все остальные обязательные узлы должны иметь принятый продукт.

## Проверки и ошибки

- Отсутствующий вход блокирует зависимую ветку, независимые ready узлы доступны.
- Partial передаётся лишь узлам с accept_partial_inputs и сохраняется в итоговом статусе.
- Никаких новых paid calls, публикаций, сообщений или ACL-изменений из координатора.
- Применить quality/qa-checklist.md, source freshness, immutable lineage и subject-specific currentness decisions.
- Результаты соответствуют scope/цели, а не просто наличию заполненного JSON.

## Общий порядок пользователя

instructions/operating-policy.md имеет приоритет над сокращениями upstream. Пять файлов карточки и настоящая приёмка Нины обязательны до исследования; принятые исследование/аудит — до следующей фазы. Команда Игоря, утверждение, приёмка и QA — разные факты. Специальный workflow не выдаёт разрешения перескочить фазу; выбранный каталог может ожидать внешние принятые входы. Параллельны только независимые задачи внутри разрешённого этапа. Доверенного reader решений и общей очереди пока нет; для клиента без проверенных решений переход закрыт.

## Фактический режим

Процедура адаптирована для исполнения Codex. CLI автоматизирует DAG, state, проверку контрактов/ссылок/значений evidence и фиксацию результата. Предметный анализ и ревью — ручная работа Codex с реальными разрешёнными источниками. Сетевые адаптеры, store/apply/publish/scheduling не имитируются.

## Команды

`seo process plan --workflow competitor-teardown` → `seo gates --profile <profile.json> --workspace <private-dir>` → `seo process start --profile <profile.json> --workflow competitor-teardown --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic` на зарезервированных example-доменах.
