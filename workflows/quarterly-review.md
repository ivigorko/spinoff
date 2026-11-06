# Квартальный пересмотр стратегии

Источник: `workflows/quarterly-review.md`. Canonical DAG: `seo_system/config/processes.json`, ID `quarterly-review`.

## Назначение и триггер

Запрос на квартальный пересмотр стратегии.

## Входы и зависимости

- Сопоставимые кварталы, цели и журнал работ.
- Обновлённое конкурентное покрытие; рассылка не входит.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `traffic` / analysis | `analytics.traffic-analyst` | Внешние входы | definitions, periods, segments, changes, explanations |
| `rankings` / analysis | `analytics.ranking-tracker` | Внешние входы | scope, rankings, distribution, movers, limitations |
| `roi` / analysis | `analytics.roi-calculator` | traffic | costs, value_model, calculations, scenarios, limitations |
| `competitive` / analysis | `strategy.competitive-strategy-analyst` | traffic, rankings | landscape, attack, defend, differentiate, defer |
| `strategy` / analysis | `strategy.seo-strategist` | traffic, rankings, competitive, roi | assessment, pillars, kpis, risks, decisions |
| `roadmap` / analysis | `strategy.roadmap-planner` | strategy | capacity, phases, tasks, dependencies, checkpoints |
| `summary` / analysis | `strategy.client-communication-manager` | roadmap | audience, summary, decision_requests, status, faq |
| `refresh` / analysis | `operations.strategy-refresh` | summary | continue, change, stop, next_backlog, review_window |

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

## Фактический режим

Процедура адаптирована для исполнения Codex. CLI автоматизирует DAG, state, проверку контрактов/ссылок/значений evidence и фиксацию результата. Предметный анализ и ревью — ручная работа Codex с реальными разрешёнными источниками. Сетевые адаптеры, store/apply/publish/scheduling не имитируются.

## Команды

`seo process plan --workflow quarterly-review` → `seo process start --profile <profile.json> --workflow quarterly-review --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic`.
