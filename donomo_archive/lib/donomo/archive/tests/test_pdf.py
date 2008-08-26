import unittest
from glob import glob
import os
import shutil

# ----------------------------------------------------------------------------

class TestPdf(unittest.TestCase):
    """
    Unit test for the pdf utility module
    """
    def test_split_pages(self):
        """
        Split pages

        """
        from donomo.archive.utils import pdf

        source_file = os.path.join(
            os.path.dirname(__file__),
            'data',
            '2008_06_26_15_57_07.pdf' )

        output_dir = pdf.split_pages(source_file)
        input_files  = glob(os.path.join(output_dir, '*.pdf'))
        output_files = [ pdf.convert(f) for f in input_files ]

        self.assertEqual(len(input_files), len(output_files))
        shutil.rmtree(output_dir)


# ----------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
