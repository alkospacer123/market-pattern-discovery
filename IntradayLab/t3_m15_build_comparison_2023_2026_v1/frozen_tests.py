"""Run frozen synthetic tests without writing inside historical directories."""
import argparse,sys,tempfile,unittest
from pathlib import Path
from registry import ROOT,folder
def run(group):
 d=ROOT/'IntradayLab'/folder(group);sys.path.insert(0,str(d))
 original=tempfile.TemporaryDirectory
 def scratch(*a,**k):k['dir']='/workspace/work';return original(*a,**k)
 tempfile.TemporaryDirectory=scratch
 suite=unittest.defaultTestLoader.discover(str(d),pattern='test*.py')
 result=unittest.TextTestRunner(verbosity=1).run(suite)
 assert result.wasSuccessful()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--group',required=True);a=p.parse_args();run(a.group)
