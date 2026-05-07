from services import data_loader
from utils.helpers import df_to_records
from utils.nan_cleaner import clean_for_json


def get_kpi_dashboard():
    kpis = data_loader.get_kpi_summary()
    return clean_for_json(df_to_records(kpis))


def get_false_positive_audit():
    return clean_for_json(df_to_records(data_loader.get_false_positive_audit()))


def get_fp_rate_by_signal():
    return clean_for_json(df_to_records(data_loader.get_fp_rate_by_signal()))


def get_evaluation_results():
    return clean_for_json(df_to_records(data_loader.get_evaluation_results()))


def get_revenue_impact():
    return clean_for_json(df_to_records(data_loader.get_revenue_impact()))


def get_threshold_log():
    return clean_for_json(df_to_records(data_loader.get_threshold_log()))
