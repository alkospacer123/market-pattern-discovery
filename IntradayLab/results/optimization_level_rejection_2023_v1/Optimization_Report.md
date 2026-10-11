# Optimization Level Rejection M5 — 2023

**NO QUALIFYING OPTIMIZATION LEVEL_REJECTION CANDIDATE**

Base `e8312745c22539be3eeacd53bcc9e63aae30170f`; pre-P&L freeze `e81b10c58a33f36a4eb9e8c174cc0bfd32843b4c`. 72 unique configurations × 3 instruments = 216 evaluations.
2023 M5 development data only. CLOSED economics after C1 are conditional; full annual return/account equity remains unavailable. Missing months never count as profitable.
Original six completed-bar level, one-bar breach/reentry, directional 30-minute dedup, one complete waiting M5 then future Open, structural Stop, 4-tick risk, 35-minute reserve, 17:00 deadline, session flat, Stop-first, no entry-bar Take; shared engine unchanged.
Reentry 1/2 ticks (completed Close and future Open, original parameter coupling); Stop buffer 1/2 ticks; holding 120/60 minutes; Take 2..10 FULL_NET_C1_R. No duplicate configurations or architecture incompatibilities.
Let s be initial gross price risk, c=2×entry tick. Planned Take distance q×(s+c)+c, outward rounded; ideal after-C1 Stop loses s+c, ideal net/net Stop is -1; adverse Open gaps can lose more. net_R_c1=(gross−actual C1)/s preserves A/B/C reporting; planned/realized net/net R use s+planned/actual C1. Never mix these denominators.
Selection: ≥100 CLOSED, ≥40 entry days, ≥6 entry months; both PF ≥2, expectancy >0, ≥9 positive exit months, conditional CLOSED DD ≤20R, winner share ≤25%, positive-month share ≤50%, ≥2 adjacent one-parameter neighbors with ≥100 CLOSED/PF R ≥1.5/expectancy >0.
Ranking: positive months DESC, min(PF R,price) DESC, DD ASC, CLOSED DESC, stable ID ASC. Only complete passes can be candidates. Diagnostic rows below use that same ordering without implying qualification.
Full journals in evaluations/<ID>/<instrument>/; all_candidates.csv, monthly_results.csv (12 months each), direction_results.csv, execution_funnel.csv, parameter_neighborhood.csv and detailed_artifact_index.csv preserve every evaluation. SKIP and EXCLUDED have separate ledgers and blank economics.

| Instrument | Evaluated | Sample pass | Both PF pass | Months pass | Neighbor pass | Full pass |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| USDRUBF | 72 | 72 | 0 | 0 | 0 | 0 |
| CNYRUBF | 72 | 72 | 0 | 0 | 0 | 0 |
| GLDRUBF | 72 | 72 | 0 | 0 | 0 | 0 |

Best three diagnostic configurations per instrument, under the published ranking order:

| Instrument / ID | CLOSED | PF R / price | Net R | + months | DD R | Failed gates |
| --- | ---: | --- | ---: | ---: | ---: | --- |
| USDRUBF / LR_OPT2023_REENTRY2_SB2_HOLD120_TP6 | 532 | 0.85227460036116066731271307981982391585929965666054 / 0.81093443694184273578741015029405358309736440862557 | -56.04173539511562408103264005694 | 5 | 65.49701213387067012206417131531 | PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors |
| USDRUBF / LR_OPT2023_REENTRY2_SB2_HOLD120_TP7 | 531 | 0.83723516604356550836956718439066842021764862014591 / 0.80230535015224010439321444106133101348412353197042 | -61.97502987841010737551593453894 | 5 | 72.18030661716515341654746579731 | PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors |
| USDRUBF / LR_OPT2023_REENTRY2_SB2_HOLD120_TP5 | 534 | 0.81870766413545419515482252583831397405543841176993 / 0.78978133795193764884174063650140723100238146785018 | -69.19884642134429736852945696294 | 5 | 79.28893847938767387032380865694 | PF_R|PF_price|positive_expectancy|months|conditional_DD|neighbors |
| CNYRUBF / LR_OPT2023_REENTRY1_SB1_HOLD120_TP7 | 208 | 0.83957406561589776046336108053676157939869793066657 / 0.74644067796610169491525423728813559322033898305085 | -24.65640859738209349980871561996 | 4 | 45.75366449489154070499628591719 | PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors |
| CNYRUBF / LR_OPT2023_REENTRY1_SB1_HOLD120_TP3 | 213 | 0.78935416145868364650107471028677913036291649502704 / 0.71471371504660452729693741677762982689747003994674 | -32.74171469835536088986770987559 | 4 | 53.95851948497891460046613341019 | PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors |
| CNYRUBF / LR_OPT2023_REENTRY1_SB1_HOLD120_TP2 | 219 | 0.77635669719678106800957430539029032588440027534464 / 0.63376623376623376623376623376623376623376623376623 | -34.62951108071696064277181060709 | 4 | 53.12161834264298965584553661669 | PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors |
| GLDRUBF / LR_OPT2023_REENTRY2_SB2_HOLD60_TP3 | 143 | 0.91174799800765553222498405939938151938690304246307 / 1.0024991669443518827057647450849716761079640119960 | -8.45464445219431183655968040919 | 3 | 26.39596860918925750234065318839 | PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors |
| GLDRUBF / LR_OPT2023_REENTRY2_SB1_HOLD60_TP2 | 149 | 0.90930542345383236867777471915597489952580530031871 / 0.97108981646905960695143738833847653077797628715283 | -8.48203144712118689980512487595 | 3 | 29.41432019543458226502396005945 | PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors |
| GLDRUBF / LR_OPT2023_REENTRY2_SB1_HOLD60_TP3 | 145 | 0.90062621774411938075745560148394555242621952310024 / 0.96822823796401361646944399416437023828821526989788 | -9.70922641496844647732821711695 | 3 | 27.85673130679084588990183822815 | PF_R|PF_price|positive_expectancy|months|conditional_DD|month_concentration|neighbors |
