import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../context/TranslationContext';
import { useApiData } from '../hooks/useApiData';
import { useCountUp } from '../hooks/useCountUp';
import { getPipelineSummary, getAnomalyOverview, getGridOverview, getDataHealth, getDemoCases, getDemandAlerts } from '../api/client';
import { KPISkeleton, TableSkeleton } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { formatINR, truncateHash, getBandColor, cleanTierName, displayValue } from '../utils/formatters';

function KPICard({ label, value, accent = '#FAFAFA', delay = 0 }) {
  const animatedValue = useCountUp(typeof value === 'number' ? value : null, 800);
  const displayVal = typeof value === 'number' ? animatedValue : value;

  return (
    <div
      className="bg-[#111111] border border-[#333333] p-8 flex flex-col justify-between min-h-[130px] opacity-0 animate-fadeIn"
      style={{ animationDelay: `${delay}ms`, animationFillMode: 'forwards' }}
    >
      <span className="text-xs uppercase tracking-widest text-[#808080] font-mono">{label}</span>
      <span className="text-4xl font-light font-mono mt-4" style={{ color: accent }}>
        {displayVal ?? '\u2014'}
      </span>
    </div>
  );
}

export default function CommandCenter() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { data: pipeline, loading: pipeLoading, error: pipeError, retry: pipeRetry } = useApiData(getPipelineSummary);
  const { data: anomaly, loading: anomLoading, error: anomError, retry: anomRetry } = useApiData(getAnomalyOverview);
  const { data: grid, loading: gridLoading, error: gridError, retry: gridRetry } = useApiData(getGridOverview);
  const { data: health } = useApiData(getDataHealth);
  const { data: demoCases, loading: demoLoading, error: demoError, retry: demoRetry } = useApiData(getDemoCases);
  const { data: demandAlerts, loading: alertsLoading } = useApiData(getDemandAlerts);
  const [expandedStory, setExpandedStory] = useState(null);

  // Derive KPI values from pipeline
  const kpis = pipeline ? [
    { label: t('Total Meters'), value: pipeline.anomaly_detection?.total_meters, accent: '#FAFAFA' },
    { label: 'P1 Alerts', value: pipeline.anomaly_detection?.p1_cases, accent: '#EF4444' },
    { label: 'P2 Review', value: pipeline.anomaly_detection?.p2_cases, accent: '#F59E0B' },
    { label: 'Stressed Feeders', value: (pipeline.grid_stress?.red_feeders || 0) + (pipeline.grid_stress?.amber_feeders || 0), accent: pipeline.grid_stress?.red_feeders > 0 ? '#EF4444' : '#F59E0B' },
    { label: t('Revenue at Risk'), value: pipeline.revenue_at_risk_monthly_inr ? formatINR(pipeline.revenue_at_risk_monthly_inr) + '/mo' : '\u2014', accent: '#FAFAFA' },
    { label: 'Forecast Accuracy', value: pipeline.demand_forecast?.wmape_pct != null ? (100 - pipeline.demand_forecast.wmape_pct).toFixed(4) + '%' : '\u2014', accent: '#FAFAFA' },
  ] : [];

  // Sort feeders: RED > AMBER > GREEN
  const sortedFeeders = grid?.feeders ? [...grid.feeders].sort((a, b) => {
    const order = { RED: 0, AMBER: 1, GREEN: 2 };
    return (order[a.grid_risk_band] ?? 3) - (order[b.grid_risk_band] ?? 3);
  }).slice(0, 15) : [];

  // Tier distribution from anomaly
  const tierDist = anomaly?.tier_distribution ? Object.entries(anomaly.tier_distribution) : [];
  const maxTier = tierDist.length > 0 ? Math.max(...tierDist.map(([, v]) => v)) : 1;

  return (
    <div className="space-y-12 animate-fadeIn">
      {/* KPI Strip */}
      <section data-testid="kpi-strip">
        {pipeLoading ? (
          <KPISkeleton count={6} />
        ) : pipeError ? (
          <ErrorState message={pipeError} onRetry={pipeRetry} />
        ) : (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-5">
            {kpis.map((kpi, i) => (
              <KPICard key={i} label={kpi.label} value={kpi.value} accent={kpi.accent} delay={i * 50} />
            ))}
          </div>
        )}
      </section>

      {/* Two columns: Grid Stress + Risk Distribution */}
      <section className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        {/* Grid Stress Table - 60% */}
        <div className="lg:col-span-3 min-w-0">
          <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">{t('Grid Stress')}</h2>
          {gridLoading ? (
            <TableSkeleton rows={8} cols={5} />
          ) : gridError ? (
            <ErrorState message={gridError} onRetry={gridRetry} />
          ) : sortedFeeders.length === 0 ? (
            <EmptyState message="No feeder data available" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[#808080] text-xs uppercase tracking-wide border-b border-[#333333]">
                    <th className="text-left py-2 font-normal">Feeder</th>
                    <th className="text-left py-2 font-normal">Locality</th>
                    <th className="text-left py-2 font-normal">Band</th>
                    <th className="text-right py-2 font-normal">Peak Load %</th>
                    <th className="text-right py-2 font-normal">Peak Time</th>
                  </tr>
                </thead>
                <tbody>
                  {sortedFeeders.map((f, i) => (
                    <tr
                      key={f.feeder_id_hash || i}
                      className="border-b border-[#333333] hover:bg-[#1A1A1A] cursor-pointer transition-colors duration-150 opacity-0 animate-fadeIn"
                      style={{ animationDelay: `${i * 30}ms`, animationFillMode: 'forwards' }}
                      onClick={() => navigate(`/grid?feeder=${f.feeder_id_hash}`)}
                      data-testid={`feeder-row-${i}`}
                    >
                      <td className="py-2.5 font-mono text-xs text-[#FAFAFA]">{truncateHash(f.feeder_id_hash)}</td>
                      <td className="py-2.5 text-[#999999]">{f.locality || '\u2014'}</td>
                      <td className="py-2.5">
                        <span className="flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: getBandColor(f.grid_risk_band) }} />
                          <span style={{ color: getBandColor(f.grid_risk_band) }} className="text-xs font-mono">{f.grid_risk_band}</span>
                        </span>
                      </td>
                      <td className="py-2.5 text-right font-mono text-[#FAFAFA]">{f.peak_load_pct != null ? `${f.peak_load_pct.toFixed(4)}%` : '\u2014'}</td>
                      <td className="py-2.5 text-right text-[#999999] text-xs">{f.peak_time_ist || '\u2014'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Risk Distribution - 40% */}
        <div className="lg:col-span-2">
          <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">Risk Distribution</h2>
          {anomLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="animate-pulse bg-[#222222] h-8 rounded-sm" />
              ))}
            </div>
          ) : anomError ? (
            <ErrorState message={anomError} onRetry={anomRetry} />
          ) : tierDist.length === 0 ? (
            <EmptyState message="No tier data available" />
          ) : (
            <div className="space-y-4">
              {tierDist.map(([tier, count], i) => (
                <div key={tier} className="opacity-0 animate-fadeIn" style={{ animationDelay: `${i * 60}ms`, animationFillMode: 'forwards' }}>
                  <div className="flex items-center justify-between text-xs mb-1.5">
                    <span className="text-[#999999]">{cleanTierName(tier)}</span>
                    <span className="font-mono text-[#FAFAFA]">{count}</span>
                  </div>
                  <div className="h-2 bg-[#222222] rounded-sm overflow-hidden">
                    <div
                      className="h-full rounded-sm transition-all duration-700 ease-out"
                      style={{
                        width: `${(count / maxTier) * 100}%`,
                        backgroundColor: tier.includes('MULTI_SIGNAL') ? '#EF4444' : '#FAFAFA',
                        opacity: tier.includes('MULTI_SIGNAL') ? 1 : 0.6,
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </section>

      {/* Demand Alerts */}
      <section>
        <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">{t('Demand Alerts')}</h2>
        {alertsLoading ? (
          <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="animate-pulse bg-[#111111] border border-[#333333] h-16" />
            ))}
          </div>
        ) : !demandAlerts || demandAlerts.length === 0 ? (
          <EmptyState message="No demand alerts" />
        ) : (
          <div className="space-y-2">
            {demandAlerts.slice(0, 10).map((alert, i) => {
              const severityColor = alert.severity === 'CRITICAL' ? '#EF4444' : alert.severity === 'WARNING' ? '#F59E0B' : '#3B82F6';
              return (
                <div
                  key={alert.feeder_id_hash || i}
                  className="bg-[#111111] border border-[#333333] px-5 py-3.5 flex items-center gap-4 opacity-0 animate-fadeIn hover:bg-[#1A1A1A] cursor-pointer transition-colors"
                  style={{ animationDelay: `${i * 40}ms`, animationFillMode: 'forwards' }}
                  onClick={() => navigate(`/grid?feeder=${alert.feeder_id_hash}`)}
                >
                  <span
                    className="text-xs font-mono px-2 py-0.5 rounded-sm flex-shrink-0"
                    style={{ backgroundColor: severityColor + '20', color: severityColor }}
                  >
                    {alert.severity}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-[#FAFAFA]">{alert.locality || truncateHash(alert.feeder_id_hash)}</span>
                      <span className="text-xs text-[#808080]">{alert.zone}</span>
                    </div>
                    <p className="text-xs text-[#808080] mt-0.5">
                      Peak {alert.peak_time?.substring(11, 16) || '—'} · {displayValue(alert.peak_forecast_kwh)} kWh / {displayValue(alert.capacity_kw)} kW capacity
                      {alert.context && <span className="text-[#999999]"> · {alert.context}</span>}
                    </p>
                  </div>
                  <div className="text-right flex-shrink-0">
                    <span className="text-lg font-mono" style={{ color: severityColor }}>{alert.peak_load_pct != null ? alert.peak_load_pct.toFixed(1) : '—'}%</span>
                    <p className="text-xs text-[#808080]">{alert.red_hours}h RED · {alert.amber_hours}h AMBER</p>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Case Highlights */}
      <section>
        <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">Case Highlights</h2>
        {demoLoading ? (
          <div className="flex gap-4 overflow-x-auto pb-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="animate-pulse bg-[#111111] border border-[#333333] min-w-[300px] h-48 rounded-sm" />
            ))}
          </div>
        ) : demoError ? (
          <ErrorState message={demoError} onRetry={demoRetry} />
        ) : !demoCases || demoCases.length === 0 ? (
          <EmptyState message="No demo cases available" />
        ) : (
          <div className="flex gap-5 overflow-x-auto pb-4 scrollbar-thin">
            {demoCases.map((c, i) => (
              <div
                key={c.case_id || i}
                className="bg-[#111111] border border-[#333333] p-6 min-w-[320px] max-w-[360px] flex-shrink-0 flex flex-col opacity-0 animate-fadeIn hover:-translate-y-[1px] hover:border-[#333333] transition-all duration-200"
                style={{ animationDelay: `${i * 50}ms`, animationFillMode: 'forwards' }}
              >
                <span className="text-xs font-mono text-[#808080] uppercase tracking-wide">{c.case_tag}</span>
                <h3 className="text-base text-white mt-3 mb-3 leading-snug">{c.demo_title}</h3>
                <p className={`text-sm text-[#999999] flex-1 ${expandedStory === c.case_id ? '' : 'line-clamp-3'}`}>
                  {c.demo_narrative}
                </p>
                {c.demo_narrative && c.demo_narrative.length > 120 && (
                  <button
                    onClick={() => setExpandedStory(expandedStory === c.case_id ? null : c.case_id)}
                    className="text-xs text-[#999999] hover:text-[#FAFAFA] mt-2 text-left transition-colors"
                  >
                    {expandedStory === c.case_id ? 'Show less' : 'Read more'}
                  </button>
                )}
                <p className="text-xs text-[#808080] italic mt-3 border-t border-[#333333] pt-3">{c.what_to_show_judge}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Scale Projections */}
      {pipeline && (
        <section className="border border-[#333333] bg-[#111111] p-6">
          <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">Scale Projection</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            {[
              { label: 'Pilot (Current)', meters: '360', feeders: '15', localities: '12', revenue: formatINR(pipeline.revenue_at_risk_monthly_inr * 12), accent: '#FAFAFA' },
              { label: 'Bangalore Urban', meters: '28,000', feeders: '~1,200', localities: '~180', revenue: formatINR(pipeline.revenue_at_risk_monthly_inr * 12 * (28000 / 360)), accent: '#3B82F6' },
              { label: 'Full BESCOM', meters: '3,20,000', feeders: '~12,000', localities: '~2,400', revenue: formatINR(pipeline.revenue_at_risk_monthly_inr * 12 * (320000 / 360)), accent: '#F59E0B' },
              { label: 'Karnataka (5 DISCOMs)', meters: '12,00,000', feeders: '~48,000', localities: '~9,600', revenue: formatINR(pipeline.revenue_at_risk_monthly_inr * 12 * (1200000 / 360)), accent: '#22C55E' },
            ].map((tier, i) => (
              <div key={i} className="opacity-0 animate-fadeIn" style={{ animationDelay: `${i * 80}ms`, animationFillMode: 'forwards' }}>
                <p className="text-xs font-mono uppercase tracking-wide mb-3" style={{ color: tier.accent }}>{tier.label}</p>
                <div className="space-y-1.5 text-xs">
                  <div className="flex justify-between"><span className="text-[#808080]">Meters</span><span className="font-mono text-[#FAFAFA]">{tier.meters}</span></div>
                  <div className="flex justify-between"><span className="text-[#808080]">Feeders</span><span className="font-mono text-[#FAFAFA]">{tier.feeders}</span></div>
                  <div className="flex justify-between"><span className="text-[#808080]">Localities</span><span className="font-mono text-[#FAFAFA]">{tier.localities}</span></div>
                  <div className="flex justify-between border-t border-[#333333] pt-1.5 mt-1.5"><span className="text-[#808080]">Annual Recovery</span><span className="font-mono" style={{ color: tier.accent }}>{tier.revenue}</span></div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-[#808080] mt-4 font-mono">Extrapolated from pilot: {pipeline.anomaly_detection?.p1_cases} P1 cases across {pipeline.anomaly_detection?.total_meters} meters at {formatINR(pipeline.revenue_at_risk_monthly_inr)}/mo</p>
        </section>
      )}

      {/* Health Status Footer */}
      <section className="border-t border-[#333333] pt-4" data-testid="health-status">
        {health ? (
          <div className="flex items-center gap-2 text-xs text-[#808080]">
            <div className={`w-1.5 h-1.5 rounded-full ${!health.errors || health.errors.length === 0 ? 'bg-[#22C55E]' : 'bg-[#EF4444]'}`} />
            <span>System: {health.files_loaded}/{health.total_files} files · {health.total_records?.toLocaleString()} records · {health.load_time_seconds?.toFixed(4)}s</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 text-xs text-[#808080]">
            <div className="w-1.5 h-1.5 rounded-full bg-[#525252]" />
            <span>System status unavailable</span>
          </div>
        )}
      </section>
    </div>
  );
}
