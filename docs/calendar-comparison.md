# Сравнение календарных месяцев — v0.4

Новый `mode: calendar_month` — явное дополнение к comparison contract. Отсутствие mode или `mode: equal_duration` сохраняет прежнюю проверку равных закрытых окон: произвольные неравные периоды по-прежнему отклоняются.

Режим поддерживает **аддитивные неотрицательные итоги**, например визиты или достижения, для двух полных календарных месяцев. Он валидирует supplied totals/deltas, а не получает данные из API. Невзвешенные averages/rates/уникальные пользователи с дневной дедупликацией не следует выдавать за сумму daily observations. Отдельная модель для таких метрик пока отсутствует.

## Обязательные проверки

1. Начало каждого периода — первое число месяца, конец — последний день того же месяца, включая 28/29 февраля. Периоды не пересекаются, baseline предшествует current, current закрыт в timezone метрики. Равные по длине фрагменты не становятся полными месяцами от выбора mode.
2. Одинаковы metric/unit/scope и analytics_signature: property_ref, timezone, definition_version, filters_hash. Значения и определения summary records соответствуют зарегистрированным источникам, их scope/period и hashes.
3. В каждом measurement обязателен `coverage_evidence: {source_id, pointer}`. Он разрешается в зарегистрированном analytics source, соответствующем property/scope/period/signature. Нельзя пройти этот режим на одном заявлении исполнителя в work-product без source record.
4. Source record соответствует `schemas/observation-coverage.json`: те же start/end/scope/metric/unit, aggregation=sum, coverage_status=confirmed_complete, непустое coverage_basis и known_gaps=[]; observation_start/end покрывают весь месяц в timezone. Конец наблюдения включать не нужно: он должен достигать следующей локальной полуночи после последнего дня. Начало/конец периода не подменяются датой загрузки.
5. Срок observation_end не позже source_generated_at и текущего времени. Поздний запуск счётчика, раннее выключение, известные разрывы или unknown/incomplete coverage отклоняются даже при наличии строки с нулём на каждый день.
6. daily_values содержит ровно одну запись {date,value} для каждого календарного дня: без дублей, пробелов, дат вне месяца, null, отрицательных или бесконечных значений. Сумма совпадает с period total. Легитимные нулевые дни допускаются только вместе с отдельным подтверждением непрерывного наблюдения.
7. Absolute/percent deltas проверяются по исходным totals; при нулевом baseline процент остаётся null. Старые release bracketing, scope, freshness и partial gates не отключаются.

coverage_basis должен описывать реальное source-backed подтверждение жизненного цикла трекинга и непрерывности. Нельзя объявлять его подтверждённым, просто выписав 30/31 дат или дополнив пропуски нулями. Нормализатор хранит оригинал и mapping; подлинность источника/правильность mapping всё ещё требуют ревью. Локальная схема не сертифицирует провайдера или отсутствие всех скрытых сбоев.

## Форма результата

```json
{
  "mode": "calendar_month",
  "baseline": {
    "coverage_evidence": {"source_id": "analytics-export", "pointer": "/observation_coverage/0"}
  },
  "current": {
    "coverage_evidence": {"source_id": "analytics-export", "pointer": "/observation_coverage/1"}
  }
}
```

Это только новые поля для добавления в существующий comparison: start/end/scope/metric/unit/value/evidence и deltas по-прежнему обязательны. Это не готовый work-product. Полный воспроизводимый synthetic пример с scope, source originals, daily coverage и coordinator submit — tests/test_calendar_months.py (`test_coordinator_accepts_complete_calendar_month_product`). Пример не является данными клиента.

## Что означает сравнение

Mode допускает **описательное сравнение полных месячных totals**, а не заявляет причинный рост. Число дней показывать рядом с дельтой; при необходимости отдельно рассчитать среднее в день. Полные месяцы разной длины могут различаться рабочими днями, сезонностью и изменениями трекинга. Формулировка «рост SEO на X%» требует дополнительных оснований.

Реальный пилот повторён на тех же локальных копиях: расчёты и сопоставления не изменились; три аналитических результата остаются partial. Попытка полного calendar_month сравнения без source-backed observation_coverage отклонена и отмечена blocked_input, успешного продукта нет. Нельзя заменить partial на completed только за счёт нового mode. Клиентские metrics, manifests и подробный протокол остаются в игнорируемом workspace, вне Git.
