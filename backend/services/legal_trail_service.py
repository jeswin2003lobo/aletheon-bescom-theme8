import hashlib
from datetime import datetime
from services import data_loader
from utils.helpers import df_to_records
from utils.nan_cleaner import clean_for_json


def get_audit_trail(case_id: str):
    evidence = data_loader.get_evidence_cards()
    row = evidence[evidence["case_id"] == case_id]
    if row.empty:
        return None

    card = df_to_records(row)[0]
    content = f"{card.get('case_id')}{card.get('meter_id_hash')}{card.get('triggered_signals')}"
    integrity_hash = hashlib.sha256(content.encode()).hexdigest()

    return clean_for_json({
        "case_id": card.get("case_id"),
        "meter_id_hash": card.get("meter_id_hash"),
        "evidence_summary": {
            "expected_vs_actual": card.get("expected_vs_actual_summary"),
            "peer_comparison": card.get("peer_comparison"),
            "communication_check": card.get("communication_check"),
            "event_log": card.get("event_log_summary"),
            "triggered_signals": card.get("triggered_signals"),
            "signal_count": card.get("signal_count"),
            "confidence_pct": card.get("confidence_pct"),
        },
        "legal_compliance": {
            "act": "Indian Evidence Act, Section 65B",
            "integrity_hash_sha256": integrity_hash,
            "generated_at": datetime.now().isoformat(),
            "system": "Aletheon v4.0",
            "record_type": "read_only",
            "audit_note": card.get("audit_note"),
        },
        "recommended_action": card.get("recommended_action"),
        "estimated_loss": {
            "monthly_low_inr": card.get("estimated_monthly_loss_inr_low"),
            "monthly_high_inr": card.get("estimated_monthly_loss_inr_high"),
        },
    })


def get_all_audit_trails():
    evidence = data_loader.get_evidence_cards()
    case_ids = evidence["case_id"].tolist()
    return [get_audit_trail(cid) for cid in case_ids]
