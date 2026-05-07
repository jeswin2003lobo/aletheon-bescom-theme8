from services import data_loader
from utils.helpers import df_to_records, filter_df, paginate
from utils.nan_cleaner import clean_for_json


def get_grid_overview():
    df = data_loader.get_grid_stress()
    summary = {
        "total_feeders": len(df),
        "red_count": int((df["grid_risk_band"] == "RED").sum()),
        "amber_count": int((df["grid_risk_band"] == "AMBER").sum()),
        "green_count": int((df["grid_risk_band"] == "GREEN").sum()),
    }
    records = df_to_records(df.sort_values("peak_load_pct", ascending=False))
    return clean_for_json({"summary": summary, "feeders": records})


def get_grid_stress_by_feeder(feeder_id: str):
    df = data_loader.get_grid_stress()
    row = df[df["feeder_id_hash"] == feeder_id]
    if row.empty:
        return None
    return clean_for_json(df_to_records(row)[0])


def get_grid_stress_list(zone: str = None, band: str = None, page: int = 1, page_size: int = 50):
    df = data_loader.get_grid_stress()
    df = filter_df(df, {"zone": zone, "grid_risk_band": band})
    page_df, pagination = paginate(df, page, page_size)
    return clean_for_json({"data": df_to_records(page_df), "pagination": pagination})
