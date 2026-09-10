import io
import json
import math
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'scripts/research_hillclimb'))
from prepare_colmap import read_images

class ColmapSplitTests(unittest.TestCase):
    def test_binary_order_and_capture_group_are_preserved(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'images.bin'
            names=['view_00003_perspective_00000000.jpg','view_00001_perspective_00000001.jpg','00_00/capture.jpg','00_01/capture.jpg']
            payload=struct.pack('<Q',len(names))
            for i,name in enumerate(names):
                payload+=struct.pack('<i4d3di',i+1,1,0,0,0,0,0,0,1)+name.encode()+b'\0'+struct.pack('<Q',0)
            p.write_bytes(payload)
            r=read_images(p)
            self.assertEqual([x['name'] for x in r],names)
            self.assertEqual(r[2]['group'],r[3]['group'])
            self.assertEqual(r[0]['group'],'view_00003')
            self.assertEqual(b''.join(x['raw'] for x in r),payload[8:])

    def test_unterminated_image_name_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'images.bin'
            p.write_bytes(struct.pack('<Qi4d3di',1,1,1,0,0,0,0,0,0,1)+b'bad-name')
            with self.assertRaises((ValueError,EOFError,RuntimeError)):
                read_images(p)

if __name__=='__main__': unittest.main()
