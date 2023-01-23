import os
import sys
import unittest
from functools import partial
from typing import NamedTuple
from unittest.mock import patch

import pandas as pd
from assertpy import soft_assertions

from geo_to_hca import geo_to_hca
from geo_to_hca.utils.handle_errors import NotFoundInSRAException, TermNotFoundException
from tests.table_comparator import assert_equal_ordered


class TestScenario(NamedTuple):
    accession: str
    expected_errors: list = []


class CharacteristicTest(unittest.TestCase):
    output_dir = 'output'
    expected_dir = 'tests/data/expected'
    test_dataset = [
        # TestScenario('GSE104276'),
        # TestScenario('GSE121611'),
        # TestScenario('GSE122960'),
        # TestScenario('GSE132509', expected_errors=[NotFoundInSRAException]),
        # TestScenario('GSE119945'),
        # TestScenario('GSE134174'),
        # TestScenario('GSE138669'),
        # TestScenario('GSE144236'),
        # TestScenario('GSE144239', expected_errors=[NotFoundInSRAException]),
        # TestScenario('GSE144240', expected_errors=[NotFoundInSRAException]),
        # TestScenario('GSE147482'),
        # TestScenario('GSE147944'),
        # TestScenario('GSE151091'),
        # TestScenario('GSE156456'),
        # TestScenario('GSE162122', expected_errors=[TermNotFoundException]),
        # TestScenario('GSE163530'),
        # TestScenario('GSE167597'),
        # TestScenario('GSE171668'),
        # TestScenario('GSE192721'),
        # TestScenario('GSE195719'),
        # TestScenario('GSE202210'),
        # TestScenario('GSE202601'),
        # TestScenario('GSE205642'),
        # TestScenario('GSE97168'),
        # TestScenario('GSE168453'),  # dcp-902
        # TestScenario('GSE119945'),  # dcp-878
        # TestScenario('ERP116235'),  # dcp-879
        # TestScenario('GSE132065'),
        # TestScenario('GSE103892'),
        # TestScenario('GSE162610'),
        # TestScenario('GSE117211'),
        # TestScenario('PRJNA705464', expected_errors=[ValueError]),
        # TestScenario('GSE145927'),
        # TestScenario('GSE145173'),
        # TestScenario('GSE151671'),
        # TestScenario('GSE171314'),
        # TestScenario('SRP344429'),
        # TestScenario('GSE187515'),
        TestScenario('GSE130708'),  # dcp-29
    ]

    def test_no_runtime_errors(self):
        for test_scenario in self.test_dataset:
            with self.subTest(msg=test_scenario.accession, test_scenario=test_scenario):
                self._test_geo_to_hca(test_scenario, self.output_dir)

    def test_consistent_output(self):
        for test_scenario in self.test_dataset:
            expected_file = os.path.join(self.expected_dir, f'{test_scenario.accession}.xlsx')
            if os.path.exists(expected_file):
                with self.subTest(msg=test_scenario.accession, test_scenario=test_scenario):
                    self.check_output(test_scenario, self.expected_dir, self.output_dir)

    def _test_geo_to_hca(self, test_scenario: TestScenario, output_dir):
        try:
            self.run_geo_to_hca(test_scenario.accession, output_dir)
        except AssertionError as e:
            self.fail(f'geo_to_hca failed for accession {test_scenario.accession}: assertion error: {e}')
        except Exception as e:
            actual_error = getattr(e.__cause__, '__cause__', None)
            if any([err for err in test_scenario.expected_errors if type(actual_error) == err]):
                print(f'found expected error: {type(e)=}: {e=}')
            else:
                self.fail(f"geo_to_hca failed for accession {test_scenario.accession}. "
                          f"Expected {test_scenario.expected_errors or 'no'} error, but found {actual_error}")


    def run_geo_to_hca(self, accession, output_dir):
        cli_args = ['geo_to_hca.py',
                    '--accession', accession,
                    '--output_dir', output_dir]
        with patch.object(sys, 'argv', cli_args):
            env_vars = {"IS_INTERACTIVE": "false", "DEBUG": "true"}
            with patch.dict(os.environ, env_vars):
                geo_to_hca.main()


    def check_output(self, test_scenario, expected_dir, output_dir):
        read_excel = partial(pd.read_excel,
                             sheet_name=None,  # load all sheets
                             skiprows=range(1, 5),  # skip informative rows
                             engine='openpyxl')
        expected_file = os.path.join(expected_dir, f'{test_scenario.accession}.xlsx')
        expected_sheets = read_excel(expected_file)
        actual_file = os.path.join(output_dir, f'{test_scenario.accession}.xlsx')
        actual_sheets = read_excel(actual_file)

        with soft_assertions():
            for sheet in expected_sheets.keys():
                print(f'comparing sheet {sheet}')
                expected_df = sort_by_required_columns(expected_sheets[sheet])
                actual_df = sort_by_required_columns(actual_sheets[sheet])
                assert_equal_ordered(left=actual_df,
                                     right=expected_df,
                                     left_tag='actual',
                                     right_tag='expected',
                                     ignore_cols=['Unnamed: \\d+'],
                                     description=f'diff in sheet {sheet}')


def sort_by_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(by=list(filter(lambda s: 'Required' in s, df.columns)))


class RequestsCacheTest(unittest.TestCase):
    def test_that_cache_usage_is_consistent(self):
        self.fail('not implemented')


if __name__ == '__main__':
    unittest.main()
