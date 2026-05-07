from services import data_loader
from utils.helpers import df_to_records, filter_df, paginate
from utils.nan_cleaner import clean_for_json


def get_forecast_overview():
    baseline = data_loader.get_baseline_results()
    fi = data_loader.get_feature_importance()
    forecast = data_loader.get_demand_forecast()
    return clean_for_json({
        "total_rows": len(forecast),
        "unique_feeders": int(forecast["feeder_id_hash"].nunique()),
        "baselines": df_to_records(baseline),
        "top_features": df_to_records(fi.head(10)),
    })


def get_forecast_by_feeder(feeder_id: str, test_only: bool = False):
    df = data_loader.get_demand_forecast()
    df = df[df["feeder_id_hash"] == feeder_id]
    if test_only:
        df = df[df["is_test_set"] == 1]
    if df.empty:
        return None
    return clean_for_json(df_to_records(df))


def get_forecast_timeseries(feeder_id: str = None, page: int = 1, page_size: int = 200):
    df = data_loader.get_demand_forecast()
    if feeder_id:
        df = df[df["feeder_id_hash"] == feeder_id]
    df = df.sort_values("timestamp_hour_ist")
    page_df, pagination = paginate(df, page, page_size)
    return clean_for_json({"data": df_to_records(page_df), "pagination": pagination})


def get_baseline_comparison():
    return clean_for_json(df_to_records(data_loader.get_baseline_results()))


def get_feature_importance():
    return clean_for_json(df_to_records(data_loader.get_feature_importance()))


def get_demand_alerts():
    forecast = data_loader.get_demand_forecast()
    grid = data_loader.get_grid_stress()
    holidays_df = data_loader.get_holidays()

    if forecast.empty or grid.empty:
        return []

    holiday_dates = set()
    if not holidays_df.empty and "date" in holidays_df.columns:
        holiday_dates = set(holidays_df["date"].astype(str).str[:10].tolist())

    capacity_map = {}
    for _, row in grid.iterrows():
        fid = row.get("feeder_id_hash")
        if fid:
            capacity_map[fid] = {
                "capacity_kw": row.get("physical_feeder_capacity_kw") or row.get("effective_capacity_kw_for_risk"),
                "locality": row.get("locality"),
                "zone": row.get("zone"),
                "band": row.get("grid_risk_band"),
            }

    test_df = forecast[forecast.get("is_test_set", 0) == 1].copy() if "is_test_set" in forecast.columns else forecast.copy()

    alerts = []
    for feeder_id in test_df["feeder_id_hash"].unique():
        fdf = test_df[test_df["feeder_id_hash"] == feeder_id].copy()
        info = capacity_map.get(feeder_id, {})
        cap = info.get("capacity_kw")
        if not cap or cap <= 0:
            continue

        fdf["load_pct"] = (fdf["forecast_kwh"] / cap) * 100
        peak_row = fdf.loc[fdf["load_pct"].idxmax()]
        load_pct = float(peak_row["load_pct"])

        if load_pct < 75:
            continue

        ts = str(peak_row.get("timestamp_hour_ist", ""))
        date_str = ts[:10]
        is_holiday = int(peak_row.get("is_holiday", 0)) == 1 or date_str in holiday_dates

        if load_pct >= 90:
            severity = "CRITICAL"
        elif load_pct >= 80:
            severity = "WARNING"
        else:
            severity = "WATCH"

        temp = peak_row.get("temperature_2m_c")
        rain = peak_row.get("rain_mm")
        context_parts = []
        if is_holiday:
            context_parts.append("Holiday")
        if temp and temp > 35:
            context_parts.append(f"{temp:.1f}°C")
        if rain and rain > 0:
            context_parts.append(f"Rain {rain:.1f}mm")
        hour = peak_row.get("hour")
        if hour is not None:
            if 17 <= int(hour) <= 21:
                context_parts.append("Evening peak")
            elif 9 <= int(hour) <= 12:
                context_parts.append("Morning peak")

        alerts.append({
            "feeder_id_hash": feeder_id,
            "locality": info.get("locality", ""),
            "zone": info.get("zone", ""),
            "band": info.get("band", ""),
            "severity": severity,
            "peak_load_pct": round(load_pct, 4),
            "peak_forecast_kwh": round(float(peak_row["forecast_kwh"]), 4),
            "capacity_kw": round(float(cap), 4),
            "peak_time": ts,
            "temperature_c": round(float(temp), 1) if temp else None,
            "is_holiday": is_holiday,
            "context": " · ".join(context_parts) if context_parts else None,
            "red_hours": int(fdf[fdf["load_pct"] >= 90].shape[0]),
            "amber_hours": int(fdf[(fdf["load_pct"] >= 75) & (fdf["load_pct"] < 90)].shape[0]),
        })

    alerts.sort(key=lambda x: x["peak_load_pct"], reverse=True)
    return clean_for_json(alerts)
