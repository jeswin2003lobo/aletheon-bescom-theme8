from services import data_loader
from utils.helpers import df_to_records, paginate
from utils.nan_cleaner import clean_for_json


def get_evidence_cards(page: int = 1, page_size: int = 20):
    df = data_loader.get_evidence_cards()
    page_df, pagination = paginate(df, page, page_size)
    return clean_for_json({"data": df_to_records(page_df), "pagination": pagination})


def get_evidence_by_case(case_id: str):
    df = data_loader.get_evidence_cards()
    row = df[df["case_id"] == case_id]
    if row.empty:
        return None
    return clean_for_json(df_to_records(row)[0])


def get_evidence_by_meter(meter_id: str):
    df = data_loader.get_evidence_cards()
    rows = df[df["meter_id_hash"] == meter_id]
    if rows.empty:
        return None
    return clean_for_json(df_to_records(rows))
