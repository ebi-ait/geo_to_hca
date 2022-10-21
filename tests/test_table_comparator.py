from unittest import TestCase

import numpy as np
import pandas as pd
import table_comparator


class TestTableComparator(TestCase):
    df1 = pd.DataFrame(
        {
            "Name": [
                "Braund, Mr. Owen Harris",
                "Allen, Mr. William Henry",
                "Bonnell, Miss. Elizabeth",
            ],
            "Age": [22, 35, 58],
            "Sex": ["male", "male", np.NaN],
        }
    )

    def test_compare_ordered(self):
        df2 = self.df1.copy()

        # generate different dataframe
        df2['Age'][1] = df2['Age'][1]*2
        # df2['Sex'][2] = 'male'
        table_comparator.assert_equal_ordered(self.df1, df2)
