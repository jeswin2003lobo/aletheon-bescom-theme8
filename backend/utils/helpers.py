import pandas as pd
from typing import Optional


def paginate(df: pd.DataFrame, page: int = 1, page_size: int = 50) -> tuple[pd.DataFrame, dict]:
    total = len(df)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages))
    start = (page - 1) * page_size
    end = start + page_size
    return df.iloc[start:end], {
        "page": page,
        "page_size": page_size,
        "total_records": total,
        "total_pages": total_pages,
    }


def filter_df(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
    result = df
    for col, val in filters.items():
        if val is not None and col in result.columns:
            result = result[result[col] == val]
    return result


def df_to_records(df: pd.DataFrame) -> list[dict]:
    return df.where(df.notna(), None).to_dict(orient="records")


def safe_float(val, default: float = 0.0) -> float:
    try:
        v = float(val)
        if pd.isna(v):
            return default
        return v
    except (TypeError, ValueError):
        return default
