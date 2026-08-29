import pandas as pd
from typing import Tuple, Dict, Any

class DataCleaner:
    @staticmethod
    def clean(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        report = {
            "initial_rows": len(df),
            "duplicates_removed": 0,
            "missing_values_handled": 0,
            "invalid_rows_removed": 0,
            "final_rows": 0,
            "status": "SUCCESS"
        }

        if df.empty:
            report["status"] = "EMPTY_DATAFRAME"
            return df, report

        cleaned_df = df.copy()

        initial_count = len(cleaned_df)
        cleaned_df = cleaned_df[~cleaned_df.index.duplicated(keep="first")]
        report["duplicates_removed"] = initial_count - len(cleaned_df)

        cleaned_df = cleaned_df.sort_index()

        price_cols = [c for c in ["Open", "High", "Low", "Close"] if c in cleaned_df.columns]
        invalid_mask = (cleaned_df[price_cols] <= 0).any(axis=1)
        if "Volume" in cleaned_df.columns:
            invalid_mask = invalid_mask | (cleaned_df["Volume"] < 0)

        invalid_count = int(invalid_mask.sum())
        if invalid_count > 0:
            cleaned_df = cleaned_df[~invalid_mask]
            report["invalid_rows_removed"] = invalid_count

        present_cols = price_cols + (["Volume"] if "Volume" in cleaned_df.columns else [])
        null_count = int(cleaned_df[present_cols].isnull().sum().sum())
        report["missing_values_handled"] = null_count

        if null_count > 0:
            cleaned_df[present_cols] = cleaned_df[present_cols].ffill().bfill()

        report["final_rows"] = len(cleaned_df)
        return cleaned_df, report
