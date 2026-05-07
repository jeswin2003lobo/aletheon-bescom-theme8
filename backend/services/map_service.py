from services import data_loader
from utils.helpers import df_to_records, filter_df
from utils.nan_cleaner import clean_for_json


def get_meter_map_data(zone: str = None, locality: str = None, priority: str = None):
    scores = data_loader.get_anomaly_scores()
    cols = [
        "meter_id_hash", "latitude_grid", "longitude_grid",
        "locality", "zone", "risk_tier", "priority",
        "risk_score", "consumer_category", "feeder_id_hash", "dt_id_hash",
    ]
    df = scores[[c for c in cols if c in scores.columns]].copy()
    df = filter_df(df, {"zone": zone, "locality": locality, "priority": priority})
    df = df.dropna(subset=["latitude_grid", "longitude_grid"])
    return clean_for_json(df_to_records(df))


def get_feeder_map_data():
    grid = data_loader.get_grid_stress()
    gis = data_loader.get_network_gis()
    feeder_coords = gis.groupby("feeder_id_hash").agg(
        latitude_grid=("latitude_grid", "mean"),
        longitude_grid=("longitude_grid", "mean"),
    ).reset_index()
    merged = grid.merge(feeder_coords, on="feeder_id_hash", how="left")
    return clean_for_json(df_to_records(merged))


def get_dt_map_data(feeder_id: str = None):
    cap = data_loader.get_capacity()
    gis = data_loader.get_network_gis()
    dts = cap[cap["asset_type"] == "DT"].copy()
    if feeder_id:
        dts = dts[dts["feeder_id_hash"] == feeder_id]
    dt_coords = gis.groupby("dt_id_hash").agg(
        latitude_grid=("latitude_grid", "mean"),
        longitude_grid=("longitude_grid", "mean"),
    ).reset_index()
    merged = dts.merge(dt_coords, on="dt_id_hash", how="left")
    return clean_for_json(df_to_records(merged))
