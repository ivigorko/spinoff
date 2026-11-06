# Подготовка ссылочной и PR-кампании

Источник: `workflows/link-building-campaign.md`. Canonical DAG: `seo_system/config/processes.json`, ID `link-building-campaign`.

## Назначение и триггер

Запрос на подготовка ссылочной и pr-кампании.

## Входы и зависимости

- Подтверждённые inbound данные либо ограниченный scope без полной базы.
- Полезные активы и публичные business contacts; отправка/покупки не входят.
- Профиль проекта и фактические права; source manifest и принятые контекстные продукты.

## Действия и результаты этапов

| Узел / фаза | Процедура | Зависимости | Результат |
|---|---|---|---|
| `audit` / analysis | `links.backlink-auditor` | Внешние входы | coverage, domains, anchors, risks, recommendations |
| `competitors` / analysis | `links.competitor-backlink-analyzer` | audit | profiles, verified_placements, gaps, opportunities |
| `prospects` / analysis | `links.link-prospector` | competitors | prospects, relevance, public_contacts, asset_mapping |
| `broken` / analysis | `links.broken-link-finder` | prospects | candidates, status_checks, replacements, drafts |
| `pr` / analysis | `links.digital-pr-strategist` | prospects | assets, campaigns, media_targets, calendar, measurement |
| `outreach` / analysis | `links.outreach-writer` | prospects, broken, pr | drafts, personalization_evidence, followups, recipient_scope |
| `summary` / analysis | `audit.executive-summary-writer` | audit, competitors, outreach | state, risks, opportunities, decisions, next_steps |

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

`seo process plan --workflow link-building-campaign` → `seo process start --profile <profile.json> --workflow link-building-campaign --workspace <private-dir>` → `source` → `template` → выполнение Codex → `submit` → `status`. Для сухого примера только synthetic fixtures с `--synthetic`.
