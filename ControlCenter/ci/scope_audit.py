"""Independent immutable-tree audit, works with sparse/shallow merge checkout.

Compare every top-level Git entry outside ControlCenter with verified main.
This does not open protected runtime source/data files or rely on working files.
"""
import json
from pathlib import Path
import subprocess


def audit():
    baseline=json.loads(Path(__file__).with_name('protected-main-tree.json').read_text())
    output=subprocess.check_output(['git','ls-tree','--full-tree','-z','HEAD'],text=True)
    actual={}
    for entry in output.split('\0'):
        if not entry:continue
        metadata,name=entry.split('\t',1)
        if name!='ControlCenter':actual[name]=metadata
    assert actual==baseline['entries'], 'CHANGED_PATH_OUTSIDE_CONTROLCENTER'
    report=dict(base_sha=baseline['base_sha'],outside_controlcenter='UNCHANGED',
                protected={name:actual[name] for name in ('TradingSystemLab','IntradayLab')})
    print(json.dumps(report,indent=2))
    return report


if __name__=='__main__':audit()
