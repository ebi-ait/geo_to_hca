import os
import sys
import unittest
from unittest.mock import patch

import pandas as pd
from assertpy import soft_assertions

from geo_to_hca import geo_to_hca
from tests.table_comparator import assert_equal_ordered


class CharacteristicTest(unittest.TestCase):
    output_dir = 'output'
    expected_dir = 'tests/data/expected'
    accession_list = [
        # 'GSE104276',
        # 'GSE121611',
        # 'GSE122960',
        'GSE132509',
        'GSE134174',
        # 'GSE138669',
        'GSE144236',
        'GSE144239',
        'GSE144240',
        # 'GSE147482',
        # 'GSE147944',
        # 'GSE151091',
        # 'GSE156456',
        'GSE162122',
        # 'GSE163530',
        'GSE167597',
        'GSE171668',
        'GSE192721',
        'GSE195719',
        'GSE202210',
        # 'GSE202601',
        # 'GSE205642',
        # 'GSE97168',
    ]

    def test_no_runtime_errors(self):
        for accession in self.accession_list:
            with self.subTest(accession=accession):
                self._test_geo_to_hca(accession, self.output_dir)

    def test_consistent_output(self):
        for accession in self.accession_list:
            expected_file = os.path.join(self.expected_dir, f'{accession}.xlsx')
            if os.path.exists(expected_file):
                with self.subTest(accession=accession):
                    self.check_output(accession, self.expected_dir, self.output_dir)

    def _test_geo_to_hca(self, accession, output_dir):
        try:
            self.run_geo_to_hca(accession, output_dir)
        except Exception as e:
            self.fail(f"geo_to_hca failed for accession {accession} {str(e)}")

    def run_geo_to_hca(self, accession, output_dir):
        cli_args = ['geo_to_hca.py',
                    '--accession', accession,
                    '--output_dir', output_dir]
        with patch.object(sys, 'argv', cli_args):
            env_vars = {"IS_INTERACTIVE": "false", "DEBUG": "true"}
            with patch.dict(os.environ, env_vars):
                try:
                    geo_to_hca.main()
                except AssertionError as e:
                    self.fail(f'accession {accession}: assertion error: {e}')
                except Exception as e:
                    self.fail(f'accession {accession}: exception: {e}')

    def check_output(self, accession, expected_dir, output_dir):
        expected_file = os.path.join(expected_dir, f'{accession}.xlsx')
        expected_sheets = pd.read_excel(expected_file, sheet_name=None, engine='openpyxl')
        actual_file = os.path.join(output_dir, f'{accession}.xlsx')
        actual_sheets = pd.read_excel(actual_file, sheet_name=None, engine='openpyxl')

        with soft_assertions():
            for sheet in expected_sheets.keys():
                print(f'comparing sheet {sheet}')
                expected_df = expected_sheets[sheet]
                actual_df = actual_sheets[sheet]
                assert_equal_ordered(actual_df,
                                     expected_df,
                                     ignore_cols=['Unnamed: \\d+'],
                                     description=f'diff in sheet {sheet}')


if __name__ == '__main__':
    unittest.main()
