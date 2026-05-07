import React, { useState, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useTranslation } from '../context/TranslationContext';
import { useApiData } from '../hooks/useApiData';
import { getGridOverview, getBaselines, getFeatureImportance, getFeederForecast } from '../api/client';
import { TableSkeleton, ChartSkeleton } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import { truncateHash, getBandColor, displayValue } from '../utils/formatters';
import { Line, XAxis, YAxis, Tooltip, ResponsiveContainer, Area, ReferenceLine, BarChart, Bar, Cell, ComposedChart } from 'recharts';
import { ChevronDown } from 'lucide-react';

export default function GridWatch() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const initialFeeder = searchParams.get('feeder');
  const [selectedFeeder, setSelectedFeeder] = useState(initialFeeder || null);
  const [testOnly, setTestOnly] = useState(true);

  const { data: gridData, loading: gridLoading, error: gridError, retry: gridRetry } = useApiData(getGridOverview);
  const { data: baselines, loading: blLoading, error: blError, retry: blRetry } = useApiData(getBaselines);
  const { data: features, loading: ftLoading, error: ftError, retry: ftRetry } = useApiData(getFeatureImportance);

  const fetchForecast = useCallback(() => {
    if (!selectedFeeder) return Promise.resolve(null);
    return getFeederForecast(selectedFeeder, testOnly);
  }, [selectedFeeder, testOnly]);
  const { data: forecast, loading: fcLoading, error: fcError, retry: fcRetry } = useApiData(fetchForecast, [selectedFeeder, testOnly], { immediate: !!selectedFeeder });

  // Sort feeders by band
  const sortedFeeders = useMemo(() => {
    if (!gridData?.feeders) return [];
    const order = { RED: 0, AMBER: 1, GREEN: 2 };
    return [...gridData.feeders].sort((a, b) => (order[a.grid_risk_band] ?? 3) - (order[b.grid_risk_band] ?? 3));
  }, [gridData]);

  // Feature importance (top 10)
  const topFeatures = useMemo(() => {
    if (!features) return [];
    return [...features].sort((a, b) => (b.importance_gain || 0) - (a.importance_gain || 0)).slice(0, 10);
  }, [features]);

  const summary = gridData?.summary;

  return (
    <div className="space-y-12 animate-fadeIn">
      {/* Stress Summary */}
      <section data-testid="stress-summary">
        {gridLoading ? (
          <div className="animate-pulse h-10 bg-[#222222] w-80 rounded-sm" />
        ) : gridError ? (
          <ErrorState message={gridError} onRetry={gridRetry} />
        ) : summary ? (
          <div>
            <div className="text-2xl font-light tracking-tight">
              <span className="text-[#EF4444]">{summary.red_count} RED</span>
              <span className="text-[#808080] mx-3">·</span>
              <span className="text-[#F59E0B]">{summary.amber_count} AMBER</span>
              <span className="text-[#808080] mx-3">·</span>
              <span className="text-[#22C55E]">{summary.green_count} GREEN</span>
            </div>
            <p className="text-xs text-[#808080] mt-1 font-mono">Forecast-driven · {summary.total_feeders} feeders · LightGBM</p>
          </div>
        ) : null}
      </section>

      {/* Feeder Grid */}
      <section>
        <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">Feeders</h2>
        {gridLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 9 }).map((_, i) => <div key={i} className="animate-pulse bg-[#111111] border border-[#333333] h-24 rounded-sm" />)}
          </div>
        ) : sortedFeeders.length === 0 ? (
          <EmptyState message="No feeder data" />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {sortedFeeders.slice(0, 15).map((f, i) => {
              const isExpanded = selectedFeeder === f.feeder_id_hash;
              return (
                <div
                  key={f.feeder_id_hash || i}
                  className={`bg-[#111111] border transition-all duration-300 opacity-0 animate-fadeIn ${
                    isExpanded ? 'border-white md:col-span-2 lg:col-span-3' : 'border-[#333333] hover:border-[#444444]'
                  } ${f.grid_risk_band === 'RED' ? 'border-l-2 border-l-[#EF4444]' : ''}`}
                  style={{ animationDelay: `${i * 30}ms`, animationFillMode: 'forwards' }}
                  data-testid={`feeder-card-${i}`}
                >
                  <div
                    className="p-4 cursor-pointer hover:bg-[#1A1A1A] transition-colors"
                    onClick={() => setSelectedFeeder(isExpanded ? null : f.feeder_id_hash)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-mono text-xs text-[#FAFAFA]">{truncateHash(f.feeder_id_hash, 10)}</span>
                      <span className="flex items-center gap-2">
                        <span className="flex items-center gap-1.5">
                          <span className="w-2 h-2 rounded-full" style={{ backgroundColor: getBandColor(f.grid_risk_band) }} />
                          <span className="text-xs font-mono" style={{ color: getBandColor(f.grid_risk_band) }}>{f.grid_risk_band}</span>
                        </span>
                        <ChevronDown className={`w-4 h-4 text-white transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`} />
                      </span>
                    </div>
                    <p className="text-xs text-[#999999] mb-2">{f.locality || '\u2014'}</p>
                    <div className="h-1.5 bg-[#222222] rounded-sm overflow-hidden">
                      <div
                        className="h-full rounded-sm transition-all duration-500"
                        style={{
                          width: `${Math.min(f.peak_load_pct || 0, 100)}%`,
                          backgroundColor: getBandColor(f.grid_risk_band),
                        }}
                      />
                    </div>
                    <span className="text-xs text-[#808080] mt-1 block">Peak: {f.peak_time_ist || '\u2014'}</span>
                  </div>

                  {isExpanded && (
                    <div className="px-4 pb-4 pt-2 border-t border-[#333333] animate-slideDown" data-testid="forecast-chart">
                      <div className="flex items-center justify-between mb-4">
                        <h3 className="text-sm font-mono text-[#FAFAFA]">Forecast: {truncateHash(f.feeder_id_hash, 12)}</h3>
                        <div className="flex gap-2">
                          <button
                            onClick={(e) => { e.stopPropagation(); setTestOnly(true); }}
                            className={`text-xs px-3 py-1 border transition-colors ${testOnly ? 'border-white text-white' : 'border-[#333333] text-[#999999] hover:text-white'}`}
                          >
                            Test Period
                          </button>
                          <button
                            onClick={(e) => { e.stopPropagation(); setTestOnly(false); }}
                            className={`text-xs px-3 py-1 border transition-colors ${!testOnly ? 'border-white text-white' : 'border-[#333333] text-[#999999] hover:text-white'}`}
                          >
                            Full History
                          </button>
                        </div>
                      </div>
                      {fcLoading ? (
                        <ChartSkeleton height="h-64" />
                      ) : fcError ? (
                        <ErrorState message={fcError} onRetry={fcRetry} />
                      ) : !forecast || forecast.length === 0 ? (
                        <EmptyState message="No forecast data for this feeder" />
                      ) : (
                        <div className="h-56 md:h-72">
                          <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={forecast} margin={{ top: 5, right: 16, bottom: 20, left: 5 }}>
                              <XAxis
                                dataKey="timestamp_hour_ist"
                                stroke="#333333"
                                tick={{ fontSize: 10, fill: '#808080' }}
                                tickFormatter={(v) => v ? new Date(v).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' }) : ''}
                                interval="preserveStartEnd"
                              />
                              <YAxis stroke="#333333" tick={{ fontSize: 10, fill: '#808080' }} label={{ value: 'kWh', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: '#808080' } }} />
                              <Tooltip
                                contentStyle={{ backgroundColor: '#111111', border: '1px solid #333333', fontSize: 11 }} itemStyle={{ color: '#FAFAFA' }}
                                labelStyle={{ color: '#FAFAFA' }}
                                labelFormatter={(v) => v ? new Date(v).toLocaleString('en-IN') : ''}
                              />
                              <Area dataKey="forecast_p90" stroke="none" fill="#3B82F6" fillOpacity={0.1} />
                              <Area dataKey="forecast_p10" stroke="none" fill="#000000" fillOpacity={1} />
                              <Line type="monotone" dataKey="actual_kwh" stroke="#FAFAFA" strokeWidth={1.5} dot={false} animationDuration={1200} />
                              <Line type="monotone" dataKey="forecast_kwh" stroke="#3B82F6" strokeWidth={1.5} dot={false} animationDuration={1200} />
                              <Line type="monotone" dataKey="baseline_prev_day" stroke="#555555" strokeWidth={1} strokeDasharray="4 4" dot={false} />
                              <Line type="monotone" dataKey="baseline_prev_week" stroke="#555555" strokeWidth={1} strokeDasharray="2 4" dot={false} />
                              {forecast[0]?.feeder_capacity_kw && (
                                <ReferenceLine y={forecast[0].feeder_capacity_kw} stroke="#EF4444" strokeDasharray="4 4" label={{ value: 'Capacity', fill: '#EF4444', fontSize: 10 }} />
                              )}
                            </ComposedChart>
                          </ResponsiveContainer>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </section>

      {/* Baselines + Feature Importance */}
      <section className="grid grid-cols-1 lg:grid-cols-2 gap-10">
        {/* Baselines */}
        <div>
          <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">{t('Baseline Comparison')}</h2>
          {blLoading ? (
            <TableSkeleton rows={4} cols={4} />
          ) : blError ? (
            <ErrorState message={blError} onRetry={blRetry} />
          ) : !baselines || baselines.length === 0 ? (
            <EmptyState message="No baseline data" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-[#808080] text-xs uppercase tracking-wide border-b border-[#333333]">
                    <th className="text-left py-2 font-normal">Model</th>
                    <th className="text-right py-2 font-normal">MAE (kWh)</th>
                    <th className="text-right py-2 font-normal">RMSE (kWh)</th>
                    <th className="text-right py-2 font-normal">WMAPE (%)</th>
                  </tr>
                </thead>
                <tbody>
                  {baselines.map((b, i) => (
                    <tr key={i} className={`border-b border-[#333333] ${i === 0 ? 'text-white' : 'text-[#999999]'}`}>
                      <td className="py-2.5 text-xs">{b.model_or_baseline}</td>
                      <td className="py-2.5 text-right font-mono text-xs">{displayValue(b.MAE_kWh)}</td>
                      <td className="py-2.5 text-right font-mono text-xs">{displayValue(b.RMSE_kWh)}</td>
                      <td className="py-2.5 text-right font-mono text-xs">{displayValue(b.WMAPE_pct)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {baselines[0]?.improvement_vs_prev_day_pct && (
                <p className="text-xs text-[#22C55E] mt-2 font-mono">+{Number(baselines[0].improvement_vs_prev_day_pct).toFixed(4)}% vs Previous Day</p>
              )}
            </div>
          )}
        </div>

        {/* Feature Importance */}
        <div>
          <h2 className="text-xs text-[#808080] uppercase tracking-widest font-mono mb-5">{t('Feature Importance')}</h2>
          {ftLoading ? (
            <ChartSkeleton height="h-64" />
          ) : ftError ? (
            <ErrorState message={ftError} onRetry={ftRetry} />
          ) : topFeatures.length === 0 ? (
            <EmptyState message="No feature data" />
          ) : (
            <div className="h-56 md:h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={topFeatures} layout="vertical" margin={{ left: 90, right: 16, top: 5, bottom: 5 }}>
                  <XAxis type="number" stroke="#555555" tick={{ fontSize: 10, fill: '#999999' }} />
                  <YAxis type="category" dataKey="feature_name" stroke="#333333" tick={{ fontSize: 10, fill: '#999999' }} width={85} />
                  <Tooltip contentStyle={{ backgroundColor: '#111111', border: '1px solid #333333', fontSize: 11 }} labelStyle={{ color: '#FAFAFA' }} itemStyle={{ color: '#FAFAFA' }} />
                  <Bar dataKey="importance_gain" radius={[0, 2, 2, 0]} animationDuration={800}>
                    {topFeatures.map((_, i) => (
                      <Cell key={i} fill={i === 0 ? '#FAFAFA' : '#737373'} fillOpacity={1 - i * 0.07} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
