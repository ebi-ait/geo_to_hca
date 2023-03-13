import re
from itertools import product

import pandas as pd
from assertpy import soft_assertions, assert_that, soft_fail, fail
from pandas._testing import assert_frame_equal


def assert_equal_ordered(left: pd.DataFrame,
                         right: pd.DataFrame,
                         left_tag='',
                         right_tag='',
                         description=None,
                         ignore_cols=None):
    with soft_assertions():
        left_filtered = filter_columns(ignore_cols, left)
        right_filtered = filter_columns(ignore_cols, right)

        if len(left) != len(right):
            soft_fail(f'problem during {description}: different table length: {left_tag}: {len(left)}, {right_tag}: {len(right)}')
        else:
            for i in range(0, min(len(left), len(right))):
                msg = f'diff in line {i}'
                if description:
                    msg = f'{description} {msg}'
                try:
                    assert_frame_equal(left_filtered.iloc[[i]], right_filtered.iloc[[i]])
                except AssertionError as e:
                    soft_fail(f'problem during {description}: comparing line {i} failed: {str(e)}')


def filter_columns(ignore_cols, df):
    df_filtered = df.copy(deep=True)
    if ignore_cols:
        for pattern, col in product(ignore_cols, df.columns):
            if re.fullmatch(pattern, col):
                df_filtered.drop(columns=col, inplace=True)
    return df_filtered


def assert_equal_unordered(left: pd.DataFrame,
                           right: pd.DataFrame,
                           left_label='left',
                           right_label='right',
                           side_label='side'):
    left[side_label] = left_label
    right[side_label] = right_label
    original_columns = [col for col in right.columns if col != side_label]
    diff = pd.concat([right, left]) \
             .drop_duplicates(subset=original_columns,
                              keep=False)
    if len(diff) > 0:
        fail(f'difference found\n{diff}')


def assert_pandas_frame_equal(left: pd.DataFrame, right: pd.DataFrame):
    pd.assert_frame_equal(left, right)