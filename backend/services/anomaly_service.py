from services import data_loader
from utils.helpers import df_to_records, filter_df, paginate
from utils.nan_cleaner import clean_for_json


def get_anomaly_overview():
    df = data_loader.get_anomaly_scores()
    action = data_loader.get_action_sheet()
    return clean_for_json({
        "total_meters": len(df),
        "active_meters": int((df["is_active_meter"] == 1).sum()),
        "p1_cases": int((action["priority"] == "P1").sum()),
        "p2_cases": int((action["priority"] == "P2").sum()),
        "p3_cases": int((action["priority"] == "P3").sum()),
        "tier_distribution": df["risk_tier"].value_counts().to_dict(),
        "team_distribution": action["recommended_team"].value_counts().to_dict(),
    })


def get_anomaly_scores(
    zone: str = None, locality: str = None, priority: str = None,
    risk_tier: str = None, page: int = 1, page_size: int = 50,
):
    df = data_loader.get_anomaly_scores()
    df = filter_df(df, {"zone": zone, "locality": locality, "priority": priority, "risk_tier": risk_tier})
    df = df.sort_values("risk_score", ascending=False)
    page_df, pagination = paginate(df, page, page_size)
    return clean_for_json({"data": df_to_records(page_df), "pagination": pagination})


def get_meter_anomaly(meter_id: str):
    df = data_loader.get_anomaly_scores()
    row = df[df["meter_id_hash"] == meter_id]
    if row.empty:
        return None
    return clean_for_json(df_to_records(row)[0])


def get_action_sheet(priority: str = None, team: str = None, page: int = 1, page_size: int = 50):
    df = data_loader.get_action_sheet()
    df = filter_df(df, {"priority": priority, "recommended_team": team})
    page_df, pagination = paginate(df, page, page_size)
    return clean_for_json({"data": df_to_records(page_df), "pagination": pagination})


def get_action_by_case(case_id: str):
    df = data_loader.get_action_sheet()
    row = df[df["case_id"] == case_id]
    if row.empty:
        return None
    return clean_for_json(df_to_records(row)[0])


def get_signal_summary():
    df = data_loader.get_anomaly_scores()
    sig_cols = [c for c in df.columns if c.startswith("sig_")]
    result = {}
    for col in sig_cols:
        result[col] = int(df[col].sum())
    return clean_for_json(result)
