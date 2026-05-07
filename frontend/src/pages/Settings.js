import React, { useState } from 'react';
import { useApiData } from '../hooks/useApiData';
import {
  getEvaluation, getFPAudit, getFPRateBySignal, getThresholds,
  getFeedbackStats, getFeedbackList, submitFeedback,
  sendSMS, sendAlert
} from '../api/client';
import { TableSkeleton, ChartSkeleton } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { displayValue, signalDisplayName, truncateHash } from '../utils/formatters';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Check, AlertCircle } from 'lucide-react';

const TABS = ['Evaluation', 'Thresholds', 'Feedback', 'Notifications', 'Deployment'];

export default function Settings() {
  const [activeTab, setActiveTab] = useState('Evaluation');

  return (
    <div className="space-y-10 animate-fadeIn">
      {/* Tabs */}
      <div className="flex gap-8 border-b border-[#333333]">
        {TABS.map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`pb-2 text-sm transition-colors ${activeTab === tab ? 'text-white border-b border-white' : 'text-[#999999] hover:text-[#FAFAFA]'}`}
            data-testid={`settings-tab-${tab.toLowerCase()}`}
          >
            {tab}
          </button>
        ))}
      </div>

      {activeTab === 'Evaluation' && <EvaluationTab />}
      {activeTab === 'Thresholds' && <ThresholdsTab />}
      {activeTab === 'Feedback' && <FeedbackTab />}
      {activeTab === 'Notifications' && <NotificationsTab />}
      {activeTab === 'Deployment' && <DeploymentTab />}
    </div>
  );
}

function EvaluationTab() {
  const { data: evalData, loading: evalLoading, error: evalError, retry: evalRetry } = useApiData(getEvaluation);
  const { data: fpAudit, loading: fpLoading, error: fpError, retry: fpRetry } = useApiData(getFPAudit);
  const { data: fpRate, loading: frLoading, error: frError, retry: frRetry } = useApiData(getFPRateBySignal);

  const bestF1 = evalData ? Math.max(...evalData.map(e => e.f1_score || 0)) : 0;

  return (
    <div className="space-y-10">
      {/* Evaluation Table */}
      <div>
        <h3 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-4">Model Evaluation</h3>
        {evalLoading ? <TableSkeleton rows={6} cols={7} /> : evalError ? <ErrorState message={evalError} onRetry={evalRetry} /> : !evalData?.length ? <EmptyState message="No evaluation data" /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[#808080] text-xs uppercase border-b border-[#333333]">
                  <th className="text-left py-2 font-normal">Slice</th>
                  <th className="text-right py-2 font-normal">Precision</th>
                  <th className="text-right py-2 font-normal">Recall</th>
                  <th className="text-right py-2 font-normal">F1</th>
                  <th className="text-right py-2 font-normal">TP</th>
                  <th className="text-right py-2 font-normal">FP</th>
                  <th className="text-right py-2 font-normal">FN</th>
                </tr>
              </thead>
              <tbody>
                {evalData.map((row, i) => (
                  <tr key={i} className={`border-b border-[#333333] ${row.f1_score === bestF1 ? 'text-white' : 'text-[#999999]'}`}>
                    <td className="py-2.5 text-xs">{displayValue(row.evaluation_slice)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.precision)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.recall)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.f1_score)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.true_positives)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.false_positives)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.false_negatives)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* FP Audit */}
      <div>
        <h3 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-4">False Positive Audit</h3>
        {fpLoading ? <TableSkeleton rows={4} cols={4} /> : fpError ? <ErrorState message={fpError} onRetry={fpRetry} /> : !fpAudit?.length ? <EmptyState message="No FP audit data" /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[#808080] text-xs uppercase border-b border-[#333333]">
                  <th className="text-left py-2 font-normal">Bucket</th>
                  <th className="text-right py-2 font-normal">Count</th>
                  <th className="text-right py-2 font-normal">%</th>
                  <th className="text-left py-2 font-normal">Proves</th>
                </tr>
              </thead>
              <tbody>
                {fpAudit.map((row, i) => (
                  <tr key={i} className="border-b border-[#333333] text-[#999999]">
                    <td className="py-2.5 text-xs text-[#FAFAFA]">{displayValue(row.bucket)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.count)}</td>
                    <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.percentage)}%</td>
                    <td className="py-2.5 text-xs">{displayValue(row.what_it_proves)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* FP Rate by Signal */}
      <div>
        <h3 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-4">FP Rate by Signal</h3>
        {frLoading ? <ChartSkeleton height="h-48" /> : frError ? <ErrorState message={frError} onRetry={frRetry} /> : !fpRate?.length ? <EmptyState message="No FP rate data" /> : (
          <div className="h-48">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={fpRate.map(r => ({ ...r, name: signalDisplayName(r.signal_name) }))} layout="vertical" margin={{ left: 100, right: 20 }}>
                <XAxis type="number" stroke="#555555" tick={{ fontSize: 10, fill: '#999999' }} />
                <YAxis type="category" dataKey="name" stroke="#333333" tick={{ fontSize: 10, fill: '#999999' }} width={95} />
                <Tooltip contentStyle={{ backgroundColor: '#111111', border: '1px solid #333333', fontSize: 11 }} labelStyle={{ color: '#FAFAFA' }} itemStyle={{ color: '#FAFAFA' }} />
                <Bar dataKey="false_positive_rate_pct" radius={[0, 2, 2, 0]} fill="#737373" animationDuration={600} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
}

function ThresholdsTab() {
  const { data, loading, error, retry } = useApiData(getThresholds);

  return (
    <div>
      <h3 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-4">Signal Thresholds</h3>
      {loading ? <TableSkeleton rows={8} cols={6} /> : error ? <ErrorState message={error} onRetry={retry} /> : !data?.length ? <EmptyState message="No threshold data" /> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-[#808080] text-xs uppercase border-b border-[#333333]">
                <th className="text-left py-2 font-normal">Signal</th>
                <th className="text-right py-2 font-normal">Old</th>
                <th className="text-right py-2 font-normal">New</th>
                <th className="text-left py-2 font-normal">Reason</th>
                <th className="text-left py-2 font-normal">Changed By</th>
                <th className="text-left py-2 font-normal">Date</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row, i) => (
                <tr key={i} className="border-b border-[#333333] text-[#999999]">
                  <td className="py-2.5 text-xs text-[#FAFAFA]">{signalDisplayName(row.signal_name)}</td>
                  <td className="py-2.5 text-right font-mono text-xs">{displayValue(row.old_threshold)}</td>
                  <td className="py-2.5 text-right font-mono text-xs text-[#FAFAFA]">{displayValue(row.new_threshold)}</td>
                  <td className="py-2.5 text-xs">{displayValue(row.reason)}</td>
                  <td className="py-2.5 text-xs">{displayValue(row.changed_by)}</td>
                  <td className="py-2.5 text-xs font-mono">{row.changed_at ? new Date(row.changed_at).toLocaleDateString() : '\u2014'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function FeedbackTab() {
  const { data: stats, loading: sLoading } = useApiData(getFeedbackStats);
  const { data: list, loading: lLoading, error: lError, retry: lRetry, refetch } = useApiData(getFeedbackList);
  const [form, setForm] = useState({ case_id: '', meter_id_hash: '', inspector_id: '', feedback_type: 'CONFIRMED_THEFT', finding: '', notes: '' });
  const [submitting, setSubmitting] = useState(false);
  const [submitResult, setSubmitResult] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setSubmitResult(null);
    try {
      const result = await submitFeedback(form);
      setSubmitResult({ success: true, message: `Submitted: ${result.case_id || form.case_id}` });
      setForm({ case_id: '', meter_id_hash: '', inspector_id: '', feedback_type: 'CONFIRMED_THEFT', finding: '', notes: '' });
      refetch();
    } catch (e) {
      setSubmitResult({ success: false, message: e.message || 'Failed to submit' });
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Stats */}
      {stats && (
        <div className="flex gap-4 text-sm font-mono">
          <span className="text-[#999999]">Total: <span className="text-[#FAFAFA]">{stats.total_feedback}</span></span>
          {stats.by_type && Object.entries(stats.by_type).map(([k, v]) => (
            <span key={k} className="text-[#808080]">{k}: {v}</span>
          ))}
        </div>
      )}

      {/* Submit Form */}
      <form onSubmit={handleSubmit} className="border border-[#333333] p-4 space-y-3">
        <h4 className="text-sm text-[#999999] uppercase tracking-wide font-mono">Submit Feedback</h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          <input placeholder="Case ID" value={form.case_id} onChange={e => setForm(prev => ({ ...prev, case_id: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" required />
          <input placeholder="Meter ID" value={form.meter_id_hash} onChange={e => setForm(prev => ({ ...prev, meter_id_hash: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" required />
          <input placeholder="Inspector ID" value={form.inspector_id} onChange={e => setForm(prev => ({ ...prev, inspector_id: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" />
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <select value={form.feedback_type} onChange={e => setForm(prev => ({ ...prev, feedback_type: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none">
            <option value="CONFIRMED_THEFT">Confirmed Theft</option>
            <option value="FALSE_POSITIVE">False Positive</option>
            <option value="NEEDS_REVIEW">Needs Review</option>
            <option value="METER_FAULT">Meter Fault</option>
            <option value="LEGITIMATE_USE">Legitimate Use</option>
          </select>
          <input placeholder="Finding" value={form.finding} onChange={e => setForm(prev => ({ ...prev, finding: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" required />
        </div>
        <textarea placeholder="Notes (optional)" value={form.notes} onChange={e => setForm(prev => ({ ...prev, notes: e.target.value }))} className="w-full bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252] h-20 resize-none" />
        <div className="flex items-center gap-3">
          <button type="submit" disabled={submitting} className="text-xs px-4 py-2 bg-white text-black hover:bg-[#E0E0E0] disabled:opacity-50 transition-colors">
            {submitting ? 'Submitting...' : 'Submit Feedback'}
          </button>
          {submitResult && (
            <span className={`text-xs flex items-center gap-1 ${submitResult.success ? 'text-[#22C55E]' : 'text-[#EF4444]'}`}>
              {submitResult.success ? <Check className="w-3 h-3" /> : <AlertCircle className="w-3 h-3" />}
              {submitResult.message}
            </span>
          )}
        </div>
      </form>

      {/* Recent Feedback */}
      <div>
        <h4 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-4">Recent Feedback</h4>
        {lLoading ? <TableSkeleton rows={5} cols={5} /> : lError ? <ErrorState message={lError} onRetry={lRetry} /> : !list?.length ? <EmptyState message="No feedback yet" /> : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-[#808080] text-xs uppercase border-b border-[#333333]">
                  <th className="text-left py-2 font-normal">Case</th>
                  <th className="text-left py-2 font-normal">Type</th>
                  <th className="text-left py-2 font-normal">Finding</th>
                  <th className="text-left py-2 font-normal">Inspector</th>
                  <th className="text-left py-2 font-normal">Date</th>
                </tr>
              </thead>
              <tbody>
                {(Array.isArray(list) ? list : []).slice(0, 20).map((row, i) => (
                  <tr key={i} className="border-b border-[#333333] text-[#999999]">
                    <td className="py-2 text-xs font-mono text-[#FAFAFA]">{truncateHash(row.case_id, 10)}</td>
                    <td className="py-2 text-xs">{displayValue(row.feedback_type)}</td>
                    <td className="py-2 text-xs">{displayValue(row.finding)}</td>
                    <td className="py-2 text-xs">{displayValue(row.inspector_id)}</td>
                    <td className="py-2 text-xs font-mono">{row.created_at ? new Date(row.created_at).toLocaleDateString() : '\u2014'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

function NotificationsTab() {
  const [smsForm, setSmsForm] = useState({ message: '', phone_numbers: '' });
  const [alertForm, setAlertForm] = useState({ case_id: '', meter_id: '', priority: 'P1', reason: '' });
  const [smsResult, setSmsResult] = useState(null);
  const [alertResult, setAlertResult] = useState(null);
  const [smsSending, setSmsSending] = useState(false);
  const [alertSending, setAlertSending] = useState(false);

  const handleSMS = async (e) => {
    e.preventDefault();
    setSmsSending(true);
    setSmsResult(null);
    try {
      const result = await sendSMS(smsForm);
      setSmsResult({ success: result.sent !== false, message: result.error || `Message sent: "${result.message_sent}"` });
    } catch (e) {
      setSmsResult({ success: false, message: e.message });
    } finally {
      setSmsSending(false);
    }
  };

  const handleAlert = async (e) => {
    e.preventDefault();
    setAlertSending(true);
    setAlertResult(null);
    try {
      const result = await sendAlert(alertForm);
      setAlertResult({ success: result.sent !== false, message: result.error || 'Alert sent successfully' });
    } catch (e) {
      setAlertResult({ success: false, message: e.message });
    } finally {
      setAlertSending(false);
    }
  };

  return (
    <div className="space-y-10">
      {/* SMS Form */}
      <form onSubmit={handleSMS} className="border border-[#333333] p-4 space-y-3">
        <h4 className="text-sm text-[#999999] uppercase tracking-wide font-mono">Send SMS</h4>
        <textarea placeholder="Message" value={smsForm.message} onChange={e => setSmsForm(prev => ({ ...prev, message: e.target.value }))} className="w-full bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252] h-20 resize-none" required />
        <input placeholder="Phone numbers (optional, comma-separated)" value={smsForm.phone_numbers} onChange={e => setSmsForm(prev => ({ ...prev, phone_numbers: e.target.value }))} className="w-full bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" />
        <div className="flex items-center gap-3">
          <button type="submit" disabled={smsSending} className="text-xs px-4 py-2 bg-white text-black hover:bg-[#E0E0E0] disabled:opacity-50 transition-colors">{smsSending ? 'Sending...' : 'Send SMS'}</button>
          {smsResult && (
            <span className={`text-xs ${smsResult.success ? 'text-[#22C55E]' : 'text-[#F59E0B]'}`}>{smsResult.message}</span>
          )}
        </div>
      </form>

      {/* Alert Form */}
      <form onSubmit={handleAlert} className="border border-[#333333] p-4 space-y-3">
        <h4 className="text-sm text-[#999999] uppercase tracking-wide font-mono">Send Alert</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          <input placeholder="Case ID" value={alertForm.case_id} onChange={e => setAlertForm(prev => ({ ...prev, case_id: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" required />
          <input placeholder="Meter ID" value={alertForm.meter_id} onChange={e => setAlertForm(prev => ({ ...prev, meter_id: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" required />
          <select value={alertForm.priority} onChange={e => setAlertForm(prev => ({ ...prev, priority: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none">
            <option value="P1">P1</option>
            <option value="P2">P2</option>
            <option value="P3">P3</option>
          </select>
          <input placeholder="Reason" value={alertForm.reason} onChange={e => setAlertForm(prev => ({ ...prev, reason: e.target.value }))} className="bg-[#0D0D0D] border border-[#333333] text-sm text-[#FAFAFA] px-3 py-2 outline-none focus:border-[#525252]" required />
        </div>
        <div className="flex items-center gap-3">
          <button type="submit" disabled={alertSending} className="text-xs px-4 py-2 bg-white text-black hover:bg-[#E0E0E0] disabled:opacity-50 transition-colors">{alertSending ? 'Sending...' : 'Send Alert'}</button>
          {alertResult && (
            <span className={`text-xs ${alertResult.success ? 'text-[#22C55E]' : 'text-[#F59E0B]'}`}>{alertResult.message}</span>
          )}
        </div>
      </form>
    </div>
  );
}

const DEPLOYMENT_PHASES = [
  {
    phase: 'Phase 1',
    title: 'Subdivision Validation',
    duration: 'Week 1–4',
    scope: '1 subdivision · 360 meters · 15 feeders',
    color: '#FAFAFA',
    tasks: [
      'Deploy on BESCOM intranet (Docker + PostgreSQL)',
      'Validate P1 alerts against field inspection outcomes',
      'Calibrate signal thresholds using inspector feedback loop',
      'Measure false positive rate — target: <15%',
      'Gruha Jyothi suppressor validation with AEE team',
    ],
    outcome: 'Validated detection accuracy on real outcomes',
    cost: '₹0 (existing infra)',
  },
  {
    phase: 'Phase 2',
    title: 'Division Rollout',
    duration: 'Week 5–10',
    scope: '1 division · ~5,000 meters · ~200 feeders',
    color: '#3B82F6',
    tasks: [
      'Scale data pipeline to ingest 5K meters at 15-min intervals',
      'Integrate BESCOM MDMS API for live AMI data',
      'Deploy bilingual SMS alerts to field inspectors (Fast2SMS)',
      'Train AEE/JE staff on action sheet triage workflow',
      'DT energy balance cross-check at division level',
    ],
    outcome: 'Field-tested with BESCOM staff using real workflows',
    cost: '₹15,000/mo (cloud + SMS)',
  },
  {
    phase: 'Phase 3',
    title: 'Bangalore Urban Circle',
    duration: 'Week 11–18',
    scope: '~28,000 meters · ~1,200 feeders · 8 divisions',
    color: '#F59E0B',
    tasks: [
      'Horizontal scaling: Kubernetes cluster for parallel feeder processing',
      'LightGBM retraining pipeline (weekly automated retrain)',
      'Evidence card generation for Section 135/138 prosecution cases',
      'Integration with BESCOM\'s existing billing + CRM systems',
      'Holiday-aware demand forecasting (Calendarific + Deepavali/Ugadi)',
    ],
    outcome: 'Production system covering full Bangalore Urban',
    cost: '₹45,000/mo (cloud + SMS + ops)',
  },
  {
    phase: 'Phase 4',
    title: 'Full BESCOM + Multi-DISCOM',
    duration: 'Month 5–8',
    scope: '3,20,000+ meters · All 4 circles · Template for HESCOM/GESCOM/CESC/MESCOM',
    color: '#22C55E',
    tasks: [
      'Deploy across Rural, Mysuru, and Davanagere circles',
      'Multi-tenant architecture: each DISCOM as isolated tenant',
      'Federated model: retrain per-DISCOM while sharing signal weights',
      'API gateway for third-party audit firms (legal compliance)',
      'Dashboard white-labeling per DISCOM branding',
    ],
    outcome: 'Karnataka-wide smart meter intelligence platform',
    cost: '₹1.2L/mo at scale (ROI: estimated ₹43Cr/yr recovery)',
  },
];

const ARCHITECTURE_CHOICES = [
  { label: 'No LLM on meter data', desc: 'All detection is statistical + rule-based. Compliant with Theme 8 constraint. Explainable by design.', status: 'compliant' },
  { label: 'Read-only decision layer', desc: 'Zero writes to BESCOM MDMS/billing. Operates as parallel intelligence overlay.', status: 'compliant' },
  { label: 'Masked consumer identity', desc: 'All meter IDs are SHA-256 hashed. No PII in the system. Reversible only by BESCOM DBA.', status: 'compliant' },
  { label: 'Auditable outputs', desc: 'Every alert has SHA-256 hash chain, signal breakdown, and Section 65B metadata.', status: 'compliant' },
  { label: 'False positive visibility', desc: 'FP rate tracked per signal. Gruha Jyothi suppressor prevents 103/360 wrongful flags.', status: 'compliant' },
  { label: 'Offline-capable', desc: 'Once data is loaded, all analytics run without internet. SMS is the only external dependency.', status: 'compliant' },
];

function DeploymentTab() {
  return (
    <div className="space-y-10">
      <div>
        <h3 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-2">BESCOM Deployment Roadmap</h3>
        <p className="text-xs text-[#808080] mb-6">Phased rollout from pilot validation to Karnataka-wide deployment</p>

        <div className="space-y-6">
          {DEPLOYMENT_PHASES.map((p, i) => (
            <div
              key={i}
              className="border border-[#333333] bg-[#111111] p-5 opacity-0 animate-fadeIn"
              style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'forwards' }}
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <span className="text-xs font-mono font-semibold" style={{ color: p.color }}>{p.phase}</span>
                  <h4 className="text-sm text-white mt-1">{p.title}</h4>
                  <p className="text-xs text-[#808080] mt-0.5">{p.duration} · {p.scope}</p>
                </div>
                <span className="text-xs font-mono text-[#999999] border border-[#333333] px-2 py-1">{p.cost}</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-1.5">
                {p.tasks.map((task, j) => (
                  <div key={j} className="flex items-start gap-2 text-xs text-[#999999]">
                    <span className="mt-0.5 w-1 h-1 rounded-full flex-shrink-0" style={{ backgroundColor: p.color }} />
                    {task}
                  </div>
                ))}
              </div>
              <div className="mt-3 pt-3 border-t border-[#333333] flex items-center justify-between">
                <span className="text-xs text-[#808080]">Outcome:</span>
                <span className="text-xs font-mono text-[#FAFAFA]">{p.outcome}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <h3 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-4">Constraint Compliance</h3>
        <div className="space-y-2">
          {ARCHITECTURE_CHOICES.map((c, i) => (
            <div key={i} className="flex items-start gap-3 p-3 border border-[#333333] bg-[#111111]">
              <span className="w-1.5 h-1.5 rounded-full bg-[#22C55E] mt-1.5 flex-shrink-0" />
              <div>
                <p className="text-xs text-[#FAFAFA] font-mono">{c.label}</p>
                <p className="text-xs text-[#808080] mt-0.5">{c.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
