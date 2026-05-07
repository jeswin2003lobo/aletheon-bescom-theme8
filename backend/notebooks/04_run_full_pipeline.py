"""
Session M4 — Full Pipeline Runner
Runs M0 → M1 → M2 → M3 in sequence, validates all outputs.
"""

import subprocess
import sys
import time
from pathlib import Path

NOTEBOOKS_DIR = Path(__file__).parent
DATA_PATH = NOTEBOOKS_DIR.parent / "data"
OUTPUT_PATH = DATA_PATH / "model_outputs"
GENERATED_PATH = DATA_PATH / "model_inputs_generated"


def run_script(script_name):
    print(f"\n{'='*60}")
    print(f"RUNNING: {script_name}")
    print(f"{'='*60}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, NOTEBOOKS_DIR / script_name],
        capture_output=False,
    )
    elapsed = time.time() - start
    if result.returncode != 0:
        print(f"FAILED: {script_name} (exit code {result.returncode})")
        sys.exit(1)
    print(f"COMPLETED: {script_name} in {elapsed:.1f}s")
    return elapsed


print("ALETHEON ML PIPELINE v4.0")
print("=" * 60)

t0 = run_script("00_build_features_from_raw_interval.py")
t1 = run_script("01_anomaly_detection.py")
t2 = run_script("02_demand_forecast.py")
t3 = run_script("03_evaluation_and_outputs.py")

total = t0 + t1 + t2 + t3
print(f"\n{'='*60}")
print(f"ALL 4 PIPELINE STAGES COMPLETE")
print(f"Total time: {total:.1f}s")
print(f"{'='*60}")

# ── Validate all expected outputs ────────────────────────────────────────────

expected_outputs = [
    "anomaly_scores.csv",
    "action_sheet.csv",
    "evidence_cards.csv",
    "demand_forecast_and_baselines.csv.gz",
    "grid_stress_risk_bands.csv",
    "baseline_results.csv",
    "forecast_feature_importance.csv",
    "revenue_impact_estimate.csv",
    "false_positive_audit.csv",
    "false_positive_rate_by_signal.csv",
    "anomaly_evaluation_results.csv",
    "subdivision_kpi_summary.csv",
    "threshold_recalibration_log.csv",
    "demo_story_cases.csv",
]

expected_generated = [
    "meter_summary_features_generated.csv",
    "feeder_hourly_energy_balance_generated.csv.gz",
]

print(f"\nVALIDATING OUTPUT FILES:")
missing = []
for f in expected_outputs:
    path = OUTPUT_PATH / f
    if path.exists():
        size = path.stat().st_size
        print(f"  OK  {f} ({size:,} bytes)")
    else:
        print(f"  MISSING  {f}")
        missing.append(f)

print(f"\nVALIDATING GENERATED FEATURES:")
for f in expected_generated:
    path = GENERATED_PATH / f
    if path.exists():
        size = path.stat().st_size
        print(f"  OK  {f} ({size:,} bytes)")
    else:
        print(f"  MISSING  {f}")
        missing.append(f)

if missing:
    print(f"\nERROR: {len(missing)} files missing!")
    sys.exit(1)
else:
    print(f"\nALL {len(expected_outputs) + len(expected_generated)} FILES VERIFIED")

# ── Print summary statistics ─────────────────────────────────────────────────

import pandas as pd

scores = pd.read_csv(OUTPUT_PATH / "anomaly_scores.csv")
action = pd.read_csv(OUTPUT_PATH / "action_sheet.csv")
baseline = pd.read_csv(OUTPUT_PATH / "baseline_results.csv")
grid = pd.read_csv(OUTPUT_PATH / "grid_stress_risk_bands.csv")

print(f"\nANOMALY DETECTION:")
print(f"  Total meters: {len(scores)}")
print(f"  P1 cases: {len(action[action['priority']=='P1'])}")
print(f"  P2 cases: {len(action[action['priority']=='P2'])}")
print(f"  P3 cases: {len(action[action['priority']=='P3'])}")

print(f"\nDEMAND FORECAST:")
our = baseline[baseline["model_or_baseline"] == "Aletheon_LightGBM"]
if not our.empty:
    print(f"  WMAPE: {our.iloc[0].get('WMAPE_pct', 'N/A')}%")
    print(f"  MAE: {our.iloc[0].get('MAE_kWh', 'N/A')} kWh")

print(f"\nGRID STRESS:")
print(f"  RED feeders: {len(grid[grid['grid_risk_band']=='RED'])}")
print(f"  AMBER feeders: {len(grid[grid['grid_risk_band']=='AMBER'])}")
print(f"  GREEN feeders: {len(grid[grid['grid_risk_band']=='GREEN'])}")

print(f"\nPIPELINE TIMING:")
print(f"  M0 Feature Engineering: {t0:.1f}s")
print(f"  M1 Anomaly Detection:   {t1:.1f}s")
print(f"  M2 Demand Forecast:     {t2:.1f}s")
print(f"  M3 Evaluation/Outputs:  {t3:.1f}s")
print(f"  TOTAL:                   {total:.1f}s")

print(f"\n{'='*60}")
print("ALETHEON ML PIPELINE v4.0 — COMPLETE")
print(f"{'='*60}")
