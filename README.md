# Aletheon — BESCOM Smart Meter Intelligence & Loss Detection

<p align="center">
  <img src="https://img.shields.io/badge/Theme_8-BESCOM_Smart_Meters-ED1C24?style=for-the-badge" alt="Theme 8">
  <img src="https://img.shields.io/badge/PAN_IIT-AI_for_Bharat-1E3A5F?style=for-the-badge" alt="PAN IIT">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/React-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/LightGBM-02569B?style=for-the-badge" alt="LightGBM">
</p>

<p align="center">
  <strong>AI-powered decision-support layer for BESCOM smart meter data — localized demand prediction, anomaly & theft detection, and actionable field intelligence for 360 meters across 15 feeders and 12 Bangalore localities.</strong>
</p>

---

## Live Demo

<table align="center">
<tr>
<td align="center" width="50%">
<strong>Frontend Dashboard</strong><br>
<a href="https://frontend-phi-neon-div55goz4n.vercel.app">frontend-phi-neon-div55goz4n.vercel.app</a><br>
<sub>React + Tailwind CSS on Vercel</sub>
</td>
<td align="center" width="50%">
<strong>Backend API</strong><br>
<a href="https://aletheon-bescom-theme8.onrender.com">aletheon-bescom-theme8.onrender.com</a><br>
<sub>FastAPI + 39 endpoints on Render</sub>
</td>
</tr>
</table>

> **Note:** Backend is on Render free tier — first request may take ~30s for cold start.

---

## Key Metrics

<table align="center">
<tr>
<td align="center" width="16%">
<strong>96.43%</strong><br>
<sub>Forecast Accuracy<br>(WMAPE 3.57%)</sub>
</td>
<td align="center" width="16%">
<strong>47</strong><br>
<sub>Anomaly Cases<br>(25 P1 / 5 P2 / 17 P3)</sub>
</td>
<td align="center" width="16%">
<strong>103/360</strong><br>
<sub>False Positives<br>Prevented (GJ+Solar+EV)</sub>
</td>
<td align="center" width="16%">
<strong>4.1M</strong><br>
<sub>AMI Readings<br>(15-min intervals)</sub>
</td>
<td align="center" width="16%">
<strong>11+3</strong><br>
<sub>Signal Detectors<br>+ Suppressors</sub>
</td>
<td align="center" width="16%">
<strong>39</strong><br>
<sub>API Endpoints<br>(REST)</sub>
</td>
</tr>
</table>

---

## Features

<table>
<tr>
<td width="50%">

### Part A — Demand Prediction
- **LightGBM Forecasting** — Feeder-level hourly demand with lag features (1h, 24h, 168h), weather, holidays
- **Baseline Comparison** — Beats Previous Day (+23.4%) and Previous Week (+19.7%) baselines
- **Grid Stress Bands** — RED / AMBER / GREEN risk classification per feeder
- **Demand Alerts** — CRITICAL (>90%), WARNING (>80%), WATCH (>75%) load predictions with context (temperature, holiday, peak hour)
- **Feature Importance** — 21 features ranked by LightGBM gain

</td>
<td width="50%">

### Part B — Anomaly & Theft Detection
- **8 Detector Signals** — Peer drift, sudden drop, billing cycle drop, tamper events, after-hours commercial, comm failure, reading plateau, power factor
- **3 Suppressor Signals** — Gruha Jyothi, solar export, EV night charging
- **Isolation Forest** — Unsupervised statistical outlier detection (contamination=0.12)
- **Multi-Signal Confirmation** — P1 requires 2+ independent signals, not single indicators
- **Evidence Cards** — Section 65B compliant, SHA-256 hash-chained audit trail for legal prosecution

</td>
</tr>
</table>

---

## Architecture

```
aletheon-bescom-theme8/
├── backend/                    FastAPI + Python ML Pipeline
│   ├── api/routes/             39 REST endpoints (grid, anomaly, forecast, evidence, map, kpi, notify)
│   ├── services/               Business logic (anomaly_service, forecast_service, grid_service, etc.)
│   ├── notebooks/              Full ML pipeline (M0-M4)
│   │   ├── 00_build_features_from_raw_interval.py    Feature engineering from 4.1M readings
│   │   ├── 01_anomaly_detection.py                   11 signals + Isolation Forest + tier assignment
│   │   ├── 02_demand_forecast.py                     LightGBM training + baseline comparison
│   │   ├── 03_evaluation_and_outputs.py              Evidence cards, revenue impact, KPI
│   │   └── 04_run_full_pipeline.py                   End-to-end runner
│   ├── data/                   33 data files across 5 directories
│   │   ├── raw_ami_mdm/        15 files — meter intervals, events, master tables, network GIS
│   │   ├── model_inputs/       3 files — feature-engineered inputs
│   │   ├── model_outputs/      14 files — anomaly scores, forecasts, evidence cards
│   │   ├── external_enrichment/  3 files — weather, holidays, tariff
│   │   └── synthetic_truth_and_feedback/  2 files — ground truth for evaluation
│   ├── Dockerfile              Production container
│   └── main.py                 FastAPI entrypoint
│
├── frontend/                   React Dashboard (6 pages)
│   ├── src/pages/
│   │   ├── CommandCenter.js    Overview — KPIs, demand alerts, scale projections
│   │   ├── AnomalyDetection.js Action sheet, meter scores, signal analysis
│   │   ├── GridWatch.js        Feeder forecasts, stress bands, baselines
│   │   ├── EvidenceCards.js    Section 65B cards with hash chain
│   │   ├── MapView.js          Leaflet map — meters, feeders, DTs
│   │   └── Settings.js         Evaluation, thresholds, feedback, notifications, deployment roadmap
│   └── src/api/client.js       API client (39 endpoints)
│
└── README.md
```

---

## Tech Stack

<table align="center">
<tr>
<td align="center" width="120">
<strong>FastAPI</strong><br>
<sub>Backend API</sub>
</td>
<td align="center" width="120">
<strong>LightGBM</strong><br>
<sub>Demand Forecast</sub>
</td>
<td align="center" width="120">
<strong>scikit-learn</strong><br>
<sub>Isolation Forest</sub>
</td>
<td align="center" width="120">
<strong>pandas</strong><br>
<sub>Data Pipeline</sub>
</td>
<td align="center" width="120">
<strong>React</strong><br>
<sub>Dashboard</sub>
</td>
<td align="center" width="120">
<strong>Tailwind CSS</strong><br>
<sub>Dark Theme UI</sub>
</td>
</tr>
<tr>
<td align="center" width="120">
<strong>Recharts</strong><br>
<sub>Visualizations</sub>
</td>
<td align="center" width="120">
<strong>React-Leaflet</strong><br>
<sub>Map View</sub>
</td>
<td align="center" width="120">
<strong>Fast2SMS</strong><br>
<sub>SMS Alerts</sub>
</td>
<td align="center" width="120">
<strong>Calendarific</strong><br>
<sub>Holiday API</sub>
</td>
<td align="center" width="120">
<strong>deep-translator</strong><br>
<sub>Kannada (ಕನ್ನಡ)</sub>
</td>
<td align="center" width="120">
<strong>SQLite</strong><br>
<sub>Feedback DB</sub>
</td>
</tr>
</table>

---

## Anomaly Detection Pipeline

<table>
<tr>
<th width="200">Signal</th>
<th width="80">Type</th>
<th>Threshold</th>
<th>Rationale</th>
</tr>
<tr><td><code>sig_peer_drift</code></td><td>Detector</td><td>Peer rank drop >= 30 pts</td><td>Meter diverges from similar consumers in same locality</td></tr>
<tr><td><code>sig_sudden_drop</code></td><td>Detector</td><td>Consumption drop >= 40%</td><td>First-to-last 30-day window comparison</td></tr>
<tr><td><code>sig_billing_cycle_drop</code></td><td>Detector</td><td>Last cycle < 50% of first</td><td>Delta-based billing boundary analysis</td></tr>
<tr><td><code>sig_tamper_event</code></td><td>Detector</td><td>>= 2 tamper events</td><td>TAMPER/COVER_OPEN/MAGNETIC events from meter logs</td></tr>
<tr><td><code>sig_after_hours_commercial</code></td><td>Detector</td><td>After-hours ratio > 1.5</td><td>Commercial premises consuming more after business hours</td></tr>
<tr><td><code>sig_comm_failure</code></td><td>Detector</td><td>Ping < 85% OR missed > 30</td><td>Communication module may be tampered</td></tr>
<tr><td><code>sig_reading_plateau</code></td><td>Detector</td><td>>= 40 identical readings</td><td>Stuck meter (10+ hours of identical values)</td></tr>
<tr><td><code>sig_pf_register</code></td><td>Detector</td><td>Min PF < 0.85</td><td>Supporting signal — high FP rate alone</td></tr>
<tr><td><code>sig_genuine_low_usage_context</code></td><td>Suppressor</td><td>Gruha Jyothi + low baseline</td><td>Karnataka subsidy recipients with legitimately low usage</td></tr>
<tr><td><code>sig_solar_export_normal</code></td><td>Suppressor</td><td>Solar + net metering</td><td>Low net import due to solar generation</td></tr>
<tr><td><code>sig_ev_consistent_night_pattern</code></td><td>Suppressor</td><td>EV flag active</td><td>Unusual night patterns explained by EV charging</td></tr>
</table>

### Priority Assignment

| Condition | Tier | Priority | Action |
|---|---|---|---|
| 2+ strong signals | MULTI_SIGNAL_CONFIRMED | **P1** | Field inspection within 7 days |
| 1 strong + 1 weak | MULTI_SIGNAL_CONFIRMED | **P1** | Field inspection within 7 days |
| 1 strong signal + IF >= 60 | SINGLE_SIGNAL_PROBABLE | **P2** | Desk review |
| 1 strong signal | SINGLE_SIGNAL_REVIEW | **P2** | Desk review |
| Cluster watchlist + signal | CLUSTER_WATCHLIST | **P3** | Monitor |
| IF >= 75 + no signals | STATISTICAL_OUTLIER_ONLY | **P3** | Monitor |
| Suppressor active + no strong | FALSE_POSITIVE_PREVENTED | None | Not flagged |

---

## Demand Forecasting

| Model | MAE (kWh) | RMSE (kWh) | WMAPE (%) | vs Previous Day |
|---|---|---|---|---|
| **Aletheon LightGBM** | **11.92** | **17.09** | **3.57** | **+23.39%** |
| Previous Day Same Hour | 15.57 | 22.66 | 4.66 | baseline |
| Previous Week Same Hour | 14.79 | 21.22 | 4.43 | +4.94% |
| Historical Average | 10.48 | 15.05 | 3.14 | +32.62% |

**Top Features:** lag_24h, lag_168h, lag_1h, hour, temperature, rolling_mean_24h, rolling_std_24h

---

## Constraint Compliance (Theme 8 Non-Negotiables)

<table>
<tr>
<td width="30">&#9989;</td>
<td><strong>No hosted LLM on sensitive data</strong> — All detection is statistical + rule-based. Explainable by design.</td>
</tr>
<tr>
<td>&#9989;</td>
<td><strong>Read-only decision layer</strong> — Zero writes to BESCOM MDMS/billing systems. Parallel intelligence overlay.</td>
</tr>
<tr>
<td>&#9989;</td>
<td><strong>Masked consumer identity</strong> — All meter IDs SHA-256 hashed. No PII. Reversible only by BESCOM DBA.</td>
</tr>
<tr>
<td>&#9989;</td>
<td><strong>Explainable & auditable outputs</strong> — Every alert has signal breakdown, hash chain, and Section 65B metadata.</td>
</tr>
<tr>
<td>&#9989;</td>
<td><strong>False positives minimized & visible</strong> — 3 suppressors, FP rate tracked per signal, Gruha Jyothi prevents 103/360 wrongful flags.</td>
</tr>
<tr>
<td>&#9989;</td>
<td><strong>No modification to existing systems</strong> — Works as standalone overlay. SMS is the only external dependency.</td>
</tr>
</table>

---

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python main.py
# API available at http://localhost:8000
# Loads 33/33 data files, 1,083,084 records
```

### Frontend
```bash
cd frontend
npm install
REACT_APP_BACKEND_URL=http://localhost:8000 npm start
# Dashboard at http://localhost:3000
```

### ML Pipeline (to regenerate outputs from raw data)
```bash
cd backend/notebooks
pip install -r requirements_ml.txt
python 04_run_full_pipeline.py
# Runs M0 → M1 → M2 → M3 sequentially
# Requires: data/raw_ami_mdm/matrix_parts/*.npz (4.1M readings)
```

---

## Scale Projections

| Phase | Scope | Meters | Est. Annual Recovery |
|---|---|---|---|
| **Pilot** (current) | 1 subdivision | 360 | ~Rs.4.9L |
| **Division** | Indiranagar division | ~5,000 | ~Rs.68L |
| **Bangalore Urban** | Full circle | ~28,000 | ~Rs.3.8Cr |
| **Full BESCOM** | All 4 circles | 3,20,000+ | ~Rs.43Cr |

---

## Deployment Roadmap

| Phase | Timeline | Key Milestones |
|---|---|---|
| **Phase 1** — Subdivision Validation | Week 1-4 | Deploy on BESCOM intranet, validate P1 alerts, calibrate thresholds, target <15% FP rate |
| **Phase 2** — Division Rollout | Week 5-10 | BESCOM MDMS API integration, bilingual SMS alerts, field staff training |
| **Phase 3** — Bangalore Urban | Week 11-18 | Kubernetes scaling, weekly model retrain, CRM integration, prosecution evidence |
| **Phase 4** — Full BESCOM + Multi-DISCOM | Month 5-8 | Multi-tenant architecture, per-DISCOM model federation, API gateway for audit firms |

---

<div align="center">

**Aletheon** — Turning smart meter data into actionable intelligence for BESCOM

**Team Scriptators_404:** Jeswin Jacob Lobo & Glen Elric Fernandes

PAN IIT AI for Bharat Hackathon | Theme 8 | May 2026

</div>
