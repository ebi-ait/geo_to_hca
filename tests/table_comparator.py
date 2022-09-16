import re

import pandas as pd
from assertpy import soft_assertions, assert_that


def assert_equal_ordered(left: pd.DataFrame,
                         right: pd.DataFrame,
                         description=None,
                         ignore_cols=None):
    with soft_assertions():
        left_filtered = filter_columns(ignore_cols, left)
        right_filtered = filter_columns(ignore_cols, right)

        for i in range(0, len(left)):
            msg = f'diff in line {i}'
            if description:
                msg = f'{description} {msg}'
            assert_that(left_filtered.iloc[i].to_dict(),
                        description=msg) \
                .is_equal_to(right_filtered.iloc[i].to_dict())


def filter_columns(ignore_cols, df):
    df_filtered = df.copy(deep=True)
    if ignore_cols:
        for pattern in ignore_cols:
            for col in df.columns:
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
        raise AssertionError(f'difference found\n{diff}')


def assert_pandas_frame_equal(left: pd.DataFrame, right: pd.DataFrame):
    pd.assert_frame_equal(left, right)