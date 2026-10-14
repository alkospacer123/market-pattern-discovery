"""Post-calculation source pin and report cross-reference audit, no strategy imports."""
import argparse
import csv
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE=Path(__file__).resolve().parent
PIN='f8486b446cf3d5f9f3cba6dfec32bdef8fd184c8'

def dump(path,value):
    path.write_text(json.dumps(value,sort_keys=True,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')

def run(root,results,output):
    output.mkdir(parents=True,exist_ok=False)
    summary=json.loads((results/'SUMMARY.json').read_text())
    tables=json.loads((results/'REPORT_TABLES.json').read_text())
    expected={
        'comparison':summary['historical_comparison']+[{'year':'2026 YTD',**summary['calendar_CLOSED'],'OPEN':summary['OPEN'],
            'positive_months':summary['positive_months'],'negative_months':summary['negative_months'],
            'calendar_months':summary['coverage_months_with_any_M15_bars']}],
        'monthly':[{k:r[k] for k in ('month','closed','gross_PF','gross_R','coverage_status','result_sign')} for r in summary['monthly']],
        'slices':summary['slices'],'coverage':summary['source_coverage'],
        'top_winners':[{k:r[k] for k in ('instrument','direction','trade_id','entry_time','exit_time','gross_R')} for r in summary['top_winners']]}
    assert tables==expected,'REPORT_TABLE_NOT_BOUND_TO_AUDITED_SUMMARY'
    report=(results/'REPORT_RU.md').read_text()
    m=summary['calendar_CLOSED']
    for token in (f"Gross PF {m['gross_PF']:.9f}",f"Gross R {m['gross_R']:+.9f}R",
                  f"{m['closed']} CLOSED / {summary['OPEN']} terminal OPEN",f"{m['expectancy_R']:+.9f}R",
                  f"{m['avg_win_R']:.9f}R",f"{m['avg_loss_R']:.9f}R"):
        assert token in report,('REPORT_HEADLINE_VALUE',token)
    assert subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()==PIN
    receipts=json.loads((results/'SOURCE_RECEIPTS.json').read_text());checks=[]
    # Every actual source ends BEFORE the authorized cutoff. Therefore its entire
    # byte length is admitted and hashing those bytes cannot touch future OHLCV.
    # This audit does NOT use a full-file read on a source with excluded suffix.
    for r in receipts:
        p=root/f"forever/{r['instrument']}/{r['instrument']}_M15.csv"
        assert r['stop_reason']=='EOF','FULL_PIN_VALIDATION_UNAVAILABLE_WITH_LOCKED_SUFFIX'
        size=p.stat().st_size
        assert size==r['bytes_consumed'],'SOURCE_SIZE_CHANGED'
        allowed=hashlib.sha256();blob=hashlib.sha1(b'blob '+str(size).encode()+b'\0')
        remaining=size
        with p.open('rb',buffering=0) as f:
            while remaining:
                chunk=f.read(min(65536,remaining));assert chunk
                allowed.update(chunk);blob.update(chunk);remaining-=len(chunk)
        assert allowed.hexdigest()==r['prefix_sha256'],'PERMITTED_PREFIX_CHANGED'
        assert blob.hexdigest()==r['git_blob_sha'],'WORKTREE_NOT_EQUAL_TO_PINNED_GIT_BLOB'
        git_blob=subprocess.check_output(['git','-C',str(root),'rev-parse',PIN+':'+str(p.relative_to(root))],text=True).strip()
        assert git_blob==blob.hexdigest(),'PIN_METADATA_CHANGED'
        checks.append({'instrument':r['instrument'],'status':'PASS','authorized_bytes':size,
                       'prefix_sha256':allowed.hexdigest(),'git_blob_sha':blob.hexdigest(),'no_excluded_suffix_read':True})
    audit=json.loads((results/'INDEPENDENT_AUDIT.json').read_text())
    repeat=json.loads((results/'REPEATABILITY.json').read_text())
    assert audit['status']==repeat['status']=='PASS'
    for name,digest in repeat['files_SHA256'].items():
        assert hashlib.sha256((results/name).read_bytes()).hexdigest()==digest,('SEALED_FILE_CHANGED',name)
    dump(output/'SUPPLEMENTAL_AUDIT.json',{'status':'PASS','report_tables_equal_audited_summary':True,
        'report_headlines_equal_audited_summary':True,'source_checkout_equal_pinned_git_blobs':checks,
        'all_repeat_sealed_files_unchanged':True,'sealed_file_count':repeat['file_count'],
        'postcalculation_audit_only':True,'strategy_changes':False})
    d=summary['diagnostics'];new=summary['new_2026_entry_CLOSED'];carry=summary['carry']['outcome']
    lines=['# Итоговое ревью — OOS 2026 YTD','',
        f"**Gross PF {m['gross_PF']:.9f}; Gross R {m['gross_R']:+.9f}R; {m['closed']} CLOSED / {summary['OPEN']} OPEN.** Независимый scalar-аудит PASS, {audit['fields_compared']:,} полей, 0 расхождений; max delta {audit['max_numeric_delta']:.12g}. Первый запуск и два полных повтора: {repeat['file_count']} файлов каждого, direct bytes и SHA256 PASS.", '',
        'Результат подтверждает устойчивость TRAIL_375 на доступном префиксе сильнее, чем WF2025: Gross PF вырос с 1,581307595 до 2,062109497; положительны 8 из 9 покрытых месяцев против 7 из 12 в 2025. Среди января–июля с наблюдаемым префиксом всех четырёх инструментов — 6 положительных месяцев из 7. Август и сентябрь неполные; их положительный знак не доказывает положительность полного календарного месяца.', '',
        f"CLOSED-R DD {m['closed_R_drawdown']:.9f}R против 28,637394275R в 2025; серия проигрышей {d['max_losing_trade_run']} против 11. Лучший месяц даёт {100*d['top1_share_total_R']:.6f}% R, три лучших — {100*d['top3_share_total_R']:.6f}%, против 42,298813% и 80,509708% в 2025. Без десяти крупнейших победителей остаётся {d['ex_top10_winners_R']:+.9f}R / PF {d['ex_top10_winners_PF']:.9f}. Это диагностика; основной результат не сокращён.", '',
        'Все четыре инструмента в целом положительны; обе совокупные стороны положительны. Слабая ячейка сохранена: IMOEXF LONG, PF 0,945293005, −0,845399267R, 27 CLOSED. Никакие направления не отключены.', '',
        f"Новые входы 2026: {new['closed']} CLOSED, Gross PF {new['gross_PF']:.9f}, {new['gross_R']:+.9f}R. Перенос из 2025 T3-M15-Si-000215 закрыт {carry['exit_time']} с {carry['gross_R']:+.9f}R; исходные Stop, initial R, S1 и накопленное состояние сохранены каноническим непрерывным replay.", '',
        'Исторический контроль: 2023 PF 2,207277631 / 165 CLOSED / +90,390672377R; 2024 PF 1,772133705 / 315 CLOSED / +122,131983847R; 2025 PF 1,581307595 / 300 CLOSED / +86,876613431R / 1 OPEN, WF-cohort 299 CLOSED / 1 OPEN / PF 1,563150474, WF_MIXED. Журналы и индикаторы сверены до чтения цен 2026.', '',
        'Точная область вывода: наблюдаемые завершения с 05.01.2026 09:00 MSK; USDRUBF/CNYRUBF до 30.08.2026 19:00 MSK, GLDRUBF/IMOEXF до 16.09.2026 00:00 MSK. Разрешённая граница осталась 13.10.2026 00:00 MSK, исключительно. Нет котировок за оставшийся хвост; октябрь NO_COVERAGE. Исходные timestamps — начала свечей, последние Open соответственно 30.08 18:45 и 15.09 23:45 MSK. Coverage — свидетельство pinned CSV, без внешней сертификации календаря MOEX.', '',
        'Все PF/R — Gross, без FINAM/MOEX комиссий, спреда, проскальзывания, фандинга, дивидендных денежных поправок и искусственных R-потерь. Исторические cost-stress файлы PR #512 не менялись и не используются как новые результаты этого OOS.', '',
        'Это OOS 2026 YTD, а не полный календарный год. Более короткий период и разное покрытие инструментов ограничивают прямое сравнение DD и числа сделок. Положительный PF и лучшая месячная регулярность не дают готовности к LIVE. Независимость аудита вычислительная, автор один; независимое человеческое ревью PENDING.', '',
        '**Draft PR #513. STOP для независимой проверки ChatGPT и решения пользователя. NO MERGE / NO AUTO-MERGE / NO LIVE.**']
    (output/'REVIEW_MEMO_RU.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','source_files':len(checks),'sealed_files':repeat['file_count']}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--data-root',type=Path,required=True)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.data_root,a.results,a.output)
