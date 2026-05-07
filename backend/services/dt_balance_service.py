from services import data_loader
from utils.helpers import df_to_records, filter_df
from utils.nan_cleaner import clean_for_json


def get_dt_balance_overview():
    cap = data_loader.get_capacity()
    dts = cap[cap["asset_type"] == "DT"]
    return clean_for_json({
        "total_dts": len(dts),
        "total_feeders": int(dts["feeder_id_hash"].nunique()),
        "zones": sorted(dts["zone"].unique().tolist()),
        "localities": sorted(dts["locality"].unique().tolist()),
    })


def get_dt_capacity(feeder_id: str = None, locality: str = None):
    cap = data_loader.get_capacity()
    dts = cap[cap["asset_type"] == "DT"]
    dts = filter_df(dts, {"feeder_id_hash": feeder_id, "locality": locality})
    return clean_for_json(df_to_records(dts))


def get_feeder_capacity():
    cap = data_loader.get_capacity()
    feeders = cap[cap["asset_type"] == "FEEDER"]
    return clean_for_json(df_to_records(feeders))
