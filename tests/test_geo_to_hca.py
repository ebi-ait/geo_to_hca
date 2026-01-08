import os
import sys
from functools import partial
from typing import NamedTuple
from unittest.mock import patch

import pandas as pd
import pytest
from assertpy import soft_assertions, fail

from geo_to_hca import geo_to_hca
from geo_to_hca.utils.handle_errors import NotFoundInSRAException, TermNotFoundException, NoStudyForGeoAccession
from tests.table_comparator import assert_equal_ordered


class TestScenario(NamedTuple):
    accession: str
    expected_errors: list = []

@pytest.fixture
def output_dir():
    return 'output'

@pytest.fixture
def expected_dir():
    return 'tests/data/expected'

test_dataset = [
    TestScenario('GSE104276'),
    TestScenario('GSE121611'),
    TestScenario('GSE122960', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE132509', expected_errors=[NotFoundInSRAException]),
    TestScenario('GSE119945'),
    TestScenario('GSE134174'),
    TestScenario('GSE138669'),
    TestScenario('GSE144236'),
    TestScenario('GSE144239', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE144240', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE147482'),
    TestScenario('GSE147944', expected_errors=[NoStudyForGeoAccession]),
    # HumanMelanocyteDevelopment
    # TODO: list of people in ingest is completely different then geo-to-hca
    # https://contribute.data.humancellatlas.org/projects/detail?uuid=a4f154f8-5cc9-40b5-b8d7-af90afce8a8f
    TestScenario('GSE151091'),
    # humanTrophoblastCulture
    # https://contribute.data.humancellatlas.org/projects/detail?uuid=9ac53858-606a-4b89-af49-804ccedaa660
    TestScenario('GSE156456'),
    TestScenario('GSE162122', expected_errors=[TermNotFoundException]),
    TestScenario('GSE163530', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE167597'),
    TestScenario('GSE171668', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE192721', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE195719', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE202210', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE202601', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE205642', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE97168'),
    TestScenario('GSE168453'),  # dcp-902
    TestScenario('GSE119945'),  # dcp-878
    TestScenario('ERP116235', expected_errors=[NoStudyForGeoAccession]),  # dcp-879
    TestScenario('GSE132065'),
    TestScenario('GSE103892'),
    TestScenario('GSE162610'),
    TestScenario('GSE117211'),
    TestScenario('PRJNA705464', expected_errors=[ValueError]),
    TestScenario('GSE145927'),
    TestScenario('GSE145173', expected_errors=[NoStudyForGeoAccession]),
    TestScenario('GSE151671'),
    TestScenario('GSE171314'),
    TestScenario('SRP344429'),
    TestScenario('GSE187515'),
    TestScenario('GSE130708'),  # ebi-ait/geo_to_hca#29
    TestScenario('GSE183904', expected_errors=[NoStudyForGeoAccession]),  # dcp-905
]

def idfn(val):
    if isinstance(val, (TestScenario,)):
        return val.accession
@pytest.mark.parametrize("test_scenario", test_dataset, ids=idfn)
def test_consistent_output(test_scenario, output_dir, expected_dir):
    expected_file = os.path.join(expected_dir, f'{test_scenario.accession}.xlsx')
    if os.path.exists(expected_file):
        if not test_scenario.expected_errors:
            check_output(test_scenario, expected_dir, output_dir)

@pytest.mark.parametrize("test_scenario", test_dataset, ids=idfn)
def test_no_runtime_errors(test_scenario: TestScenario, output_dir):
    try:
        run_geo_to_hca(test_scenario.accession, output_dir)
    except AssertionError as e:
        fail(f'geo_to_hca failed for accession {test_scenario.accession}: assertion error: {e}')
    except Exception as e:
        actual_error = getattr(e.__cause__, '__cause__', None)
        if any([err for err in test_scenario.expected_errors if type(actual_error) == err]):
            print(f'found expected error: {type(e)=}: {e=}')
        else:
            fail(f"geo_to_hca failed for accession {test_scenario.accession}. "
                      f"Expected {test_scenario.expected_errors or 'no'} error, but found {actual_error}")


def run_geo_to_hca(accession, output_dir):
    cli_args = ['geo_to_hca.py',
                '--accession', accession,
                '--output_dir', output_dir]
    with patch.object(sys, 'argv', cli_args):
        env_vars = {"IS_INTERACTIVE": "false", "DEBUG": "true"}
        with patch.dict(os.environ, env_vars):
            geo_to_hca.main()


def check_output(test_scenario, expected_dir, output_dir):
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
                                 description=f'comparison of sheet [{sheet}]')


def sort_by_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    return df.sort_values(by=list(filter(lambda s: 'Required' in s, df.columns)))
