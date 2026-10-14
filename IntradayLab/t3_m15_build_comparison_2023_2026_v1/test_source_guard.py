"""Cutoff reader regression: excluded OHLC suffix must remain unread."""
import io,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import worker

class Guard(unittest.TestCase):
 def test_exclusive_completion_cutoff_both_readers(self):
  data=(b'Ticker;Datetime;Open;High;Low;Close;Volume\n'
        b'X;2026-10-12 23:30:00;100;101;99;100;1\n'
        b'X;2026-10-12 23:45:00;FORBIDDEN_SUFFIX_MUST_REMAIN_UNREAD\n')
  boundary=data.index(b'FORBIDDEN_SUFFIX')
  class Spy(io.BytesIO):
   def close(self):pass
  for scalar in (False,True):
   spy=Spy(data)
   with patch.object(worker,'open',return_value=spy,create=True):rows,receipt=worker.source(Path('synthetic.csv'),scalar)
   self.assertEqual(len(rows),1);self.assertEqual(spy.tell(),boundary)
   self.assertFalse(receipt['excluded_suffix_read']);self.assertFalse(receipt['EOF'])
   self.assertEqual(receipt['last_close'].isoformat(),'2026-10-12T23:45:00+03:00')
 def test_invalid_ohlc_and_out_of_order_rejected(self):
  prefix=b'Ticker;Datetime;Open;High;Low;Close;Volume\n'
  for data in (prefix+b'X;2026-01-05 09:00:00;100;99;98;100;1\n',prefix+b'X;2026-01-05 09:00:00;100;101;99;100;1\nX;2026-01-05 09:00:00;100;101;99;100;1\n'):
   for scalar in (False,True):
    with patch.object(worker,'open',return_value=io.BytesIO(data),create=True),self.assertRaises(AssertionError):worker.source(Path('synthetic.csv'),scalar)
if __name__=='__main__':unittest.main()
