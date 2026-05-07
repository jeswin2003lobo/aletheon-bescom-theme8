from fastapi import APIRouter
from services import kpi_service

router = APIRouter(prefix="/api/kpi", tags=["KPI"])


@router.get("/dashboard")
def kpi_dashboard():
    return kpi_service.get_kpi_dashboard()


@router.get("/false-positive-audit")
def false_positive_audit():
    return kpi_service.get_false_positive_audit()


@router.get("/fp-rate-by-signal")
def fp_rate_by_signal():
    return kpi_service.get_fp_rate_by_signal()


@router.get("/evaluation")
def evaluation_results():
    return kpi_service.get_evaluation_results()


@router.get("/revenue-impact")
def revenue_impact():
    return kpi_service.get_revenue_impact()


@router.get("/thresholds")
def threshold_log():
    return kpi_service.get_threshold_log()
