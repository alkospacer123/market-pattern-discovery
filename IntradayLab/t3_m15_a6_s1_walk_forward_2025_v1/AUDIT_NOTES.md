# Уточнения для независимого ревью

До открытия 2025 первый CONTROL attempt был остановлен на сериализации служебного checkpoint Signal (numpy.int64). Полные свидетельства, первоначальный freeze и STOP сохранены в failure_evidence; они не используются как результат WF. Исправлены только cast служебного поля и force-add ignored results paths. Добавлен синтетический regression test. Новый freeze 2ba722c6 опубликован перед повторным CONTROL и первым чтением 2025. engine/scalar/features/параметры/исполнение не изменены.

В W1–W3 поле FULL_WF в машинных interim tables означает весь разрешённый на этот seal момент WF prefix, не завершённый год. Точная граница задана SOURCE_RECEIPTS/ CHECKPOINT; календарные кварталы — W1/W2/W3; expanding cumulative — CUM_Wn. Полный календарный 2025 — только results/W4/FULL_WF. Таблицы каждого seal не заменяются после чтения следующего блока. Новые квартальные signal+entry ID выделены в entry_cohorts с horizon_end_exclusive; их известный исход не подставляется из ещё не прочитанного будущего.

Один автор: независимость вычислительная, а не внешнее человеческое ревью. Стандартный Git read metadata подтверждает source pin; полная закрытая часть CSV намеренно не хешируется и не проверяется на порядок. Применяются unbuffered FileIO, read-spy poison tests, source inspection и runtime Python raw-open allowlist; системная трассировка всех read syscalls отдельно не утверждается. Coverage проверяет разрешённый source prefix и не доказывает абсолютную полноту биржевого календаря.

Ни отрицательный квартал, ни отрицательные диагностики не являются поводом для остановки/выбора параметров. При полной технической достоверности все четыре квартала сохраняются. Решение применяется только после всего года согласно #511. STOP после одного Draft PR; 2026 и LIVE закрыты.

Поле FREEZE.json before_any_raw_read=false у исправленного freeze: к этому моменту был прочитан только DEVELOPMENT в неуспешном serialization attempt. FREEZE_INITIAL подтверждает исходный freeze до любого raw-read; before_any_WF_2025_read=true для исправленного адаптера.

strace установлен, но syscall trace в этом исследовании не выполнялся. external_syscall_trace=not available в READ_AUDIT означает отсутствие отдельного syscall-artifact, а не отсутствие бинарного файла. Свидетельства доступа — application-level byte counters, unbuffered reader, read-spy tests, independent prefix hashes и source inspection.
