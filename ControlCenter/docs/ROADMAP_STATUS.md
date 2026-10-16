# Roadmap Control Center v1.0 — CC-03 source preparation

Основание [#524 / утверждённый roadmap](https://github.com/alkospacer123/market-pattern-discovery/issues/524#issuecomment-6198924792). Без добавления этапов. Base фактического main `52e167d7b36170f1f639827eb875a57d52175491`; CC-02 #531 MERGED. Root roadmap и trading projects не изменяются.

| Этап | Статус | Остаток |
| --- | --- | --- |
| CC-00 | Инвентаризация обновлена; producer code / documented / physical authority разделены | Actual Intel sources/paths/cadence не наблюдались |
| CC-01 | DEMO и independent M15 сохранены | DEMO не runtime authority |
| CC-02 | #531 merged; fixed OFFLINE_FIXTURE receiver/schema/evidence/TTL сохранены | Test binding не реальный account |
| CC-03 | Hosted Windows native suite реально выполнен в #534; 12 native cases без Windows SKIP | **NEEDS_FIX:** два atomic producer FAIL; [Windows evidence](CC03_WINDOWS_HOSTED_ACCEPTANCE.md). Source/account/TTL/calendar approval и Intel physical остаются отдельными gates |
| CC-04 | НЕ НАЧАТ | Отдельный M15 runtime/source/account после engineering acceptance |
| CC-05 | НЕ НАЧАТ | Реальные decision/execution/finance sources и независимая сверка |
| CC-06 / CC-07 | НЕ НАЧАТЫ | Отдельные control-plane mock/audit и явные approvals на каждое действие |
| CC-08 | НЕ НАЧАТ | Alert/calendar/readiness/retention acceptance |

H1 T3/H1/TRAIL1, Stage7, active identity, N4, R15 1.5%/max6%, frozen sizing и параметры не менялись. Последний документированный Intel installed `3a18c8c…`, Disabled/HALTED; #532 документирует созданную durable authorization без start/rearm permission — историческое evidence, не новый read. Source fill flag #528 True не является authorization и не изменяется.

Нынешний частичный exporter не публикует bars, fills, позиции, active SLTP или финансы; реальные account authority/cadence/calendar UNKNOWN. Панель без источника работает; M15 NOT_DEPLOYED отдельно; все 10 controls disabled. Source preparation не равна CC03_PHYSICAL_PASS или завершённому physical CC-03.

**Один Draft PR → STOP для независимого аудита. NO MERGE / NO AUTO-MERGE / NO INTEL INSTALLATION / NO H1 START/REARM. Самостоятельного перехода к CC-04 нет.**
