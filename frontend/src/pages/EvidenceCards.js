import React, { useState, useMemo, useCallback } from 'react';
import { useTranslation } from '../context/TranslationContext';
import { useApiData } from '../hooks/useApiData';
import { getEvidenceCards, getRevenueImpact, getActionSheet, getAuditTrail } from '../api/client';
import { TableSkeleton } from '../components/LoadingState';
import { ErrorState } from '../components/ErrorState';
import { EmptyState } from '../components/EmptyState';
import Pagination from '../components/Pagination';
import { formatINR, truncateHash, getPriorityColor, displayValue, signalDisplayName } from '../utils/formatters';
import { ChevronDown, ChevronUp, Shield } from 'lucide-react';

export default function EvidenceCards() {
  const { t } = useTranslation();
  const [page, setPage] = useState(1);
  const [expandedCard, setExpandedCard] = useState(null);
  const [auditData, setAuditData] = useState({});
  const [auditLoading, setAuditLoading] = useState({});
  const [showRevenue, setShowRevenue] = useState(false);

  const fetchCards = useCallback(() => getEvidenceCards({ page, page_size: 20 }), [page]);
  const { data: cardsData, loading: cardsLoading, error: cardsError, retry: cardsRetry } = useApiData(fetchCards, [page]);
  const { data: revenueData, loading: revLoading, error: revError, retry: revRetry } = useApiData(getRevenueImpact);
  // Fetch action sheet for priority mapping
  const fetchActionForPriority = useCallback(() => getActionSheet({ page: 1, page_size: 500 }), []);
  const { data: actionSheetData } = useApiData(fetchActionForPriority);

  // Build priority map from action sheet
  const priorityMap = useMemo(() => {
    const map = {};
    if (actionSheetData?.data) {
      actionSheetData.data.forEach(item => {
        if (item.case_id) map[item.case_id] = item.priority;
      });
    }
    return map;
  }, [actionSheetData]);

  // Aggregate revenue
  const aggregateRevenue = useMemo(() => {
    if (!revenueData) return null;
    return revenueData.find(r => r.case_id === 'AGGREGATE_PILOT_SUBDIVISION');
  }, [revenueData]);

  const sortedRevenue = useMemo(() => {
    if (!revenueData) return [];
    return [...revenueData]
      .filter(r => r.case_id !== 'AGGREGATE_PILOT_SUBDIVISION')
      .sort((a, b) => (b.monthly_loss_inr_high || 0) - (a.monthly_loss_inr_high || 0));
  }, [revenueData]);

  const maxRevenue = useMemo(() => {
    if (!sortedRevenue.length) return 1;
    return Math.max(...sortedRevenue.map(r => r.monthly_loss_inr_high || 0));
  }, [sortedRevenue]);

  // Handle audit trail
  const handleAuditTrail = async (caseId) => {
    if (auditData[caseId]) return;
    setAuditLoading(prev => ({ ...prev, [caseId]: true }));
    try {
      const data = await getAuditTrail(caseId);
      setAuditData(prev => ({ ...prev, [caseId]: data }));
    } catch (e) {
      setAuditData(prev => ({ ...prev, [caseId]: { error: e.message } }));
    } finally {
      setAuditLoading(prev => ({ ...prev, [caseId]: false }));
    }
  };

  const cards = cardsData?.data || [];

  return (
    <div className="space-y-10 animate-fadeIn">
      {/* Stat Strip */}
      <section className="flex flex-wrap items-center gap-5 md:gap-8 text-xs md:text-sm font-mono text-[#808080]" data-testid="evidence-stats">
        <span>Evidence Cards: <span className="text-[#FAFAFA]">{cardsData?.pagination?.total_records || '\u2014'}</span></span>
        <span className="text-[#808080]">·</span>
        <span>Section 65B Compliant</span>
        <span className="text-[#808080]">·</span>
        <span>SHA-256 Verified</span>
        <span className="text-[#808080]">·</span>
        <span>{t('Revenue at Risk')}: <span className="text-[#FAFAFA]">{aggregateRevenue ? `${formatINR(aggregateRevenue.monthly_loss_inr_high)}/mo` : '\u2014'}</span></span>
      </section>

      {/* Evidence Card List */}
      <section>
        {cardsLoading ? (
          <TableSkeleton rows={10} cols={6} />
        ) : cardsError ? (
          <ErrorState message={cardsError} onRetry={cardsRetry} />
        ) : cards.length === 0 ? (
          <EmptyState message="No evidence cards available" />
        ) : (
          <div className="space-y-2">
            {cards.map((card, i) => {
              const isExpanded = expandedCard === card.case_id;
              const priority = priorityMap[card.case_id];
              return (
                <div
                  key={card.case_id || i}
                  className="border border-[#333333] bg-[#111111] opacity-0 animate-fadeIn hover:border-[#444444] transition-all duration-200"
                  style={{ animationDelay: `${i * 30}ms`, animationFillMode: 'forwards' }}
                  data-testid={`evidence-card-${i}`}
                >
                  {/* Collapsed */}
                  <div
                    className="flex items-center gap-4 px-5 py-4 cursor-pointer hover:bg-[#1C1C1C] transition-all duration-200"
                    onClick={() => setExpandedCard(isExpanded ? null : card.case_id)}
                  >
                    {priority && (
                      <span
                        className="text-xs font-mono px-1.5 py-0.5 rounded-sm flex-shrink-0"
                        style={{ backgroundColor: getPriorityColor(priority) + '20', color: getPriorityColor(priority) }}
                      >
                        {priority}
                      </span>
                    )}
                    <span className="font-mono text-xs text-[#FAFAFA] flex-shrink-0">{truncateHash(card.case_id, 12)}</span>
                    <span className="text-xs text-[#999999] hidden md:block">{displayValue(card.locality)}</span>
                    <span className="text-xs text-[#808080] font-mono hidden lg:block">{truncateHash(card.alert_fingerprint, 12)}</span>
                    <span className="text-xs font-mono text-[#999999] hidden md:block">{card.confidence_pct ? `${Number(card.confidence_pct).toFixed(4)}%` : ''}</span>
                    <span className="text-xs font-mono text-[#FAFAFA] ml-auto flex-shrink-0">
                      {card.monthly_loss_inr_low && card.monthly_loss_inr_high ? `${formatINR(card.monthly_loss_inr_low)}\u2013${formatINR(card.monthly_loss_inr_high)}/mo` : '\u2014'}
                    </span>
                    {isExpanded ? <ChevronUp className="w-4 h-4 text-white flex-shrink-0" /> : <ChevronDown className="w-4 h-4 text-white flex-shrink-0" />}
                  </div>

                  {/* Expanded */}
                  {isExpanded && (
                    <div className="px-5 pb-5 pt-4 border-t border-[#333333] animate-slideDown">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-10 gap-y-4 text-sm">
                        <div><span className="text-[#808080] text-xs block">Expected vs Actual</span><span className="text-[#FAFAFA]">{displayValue(card.expected_vs_actual_summary)}</span></div>
                        <div><span className="text-[#808080] text-xs block">Peer Comparison</span><span className="text-[#FAFAFA]">{displayValue(card.peer_comparison)}</span></div>
                        <div><span className="text-[#808080] text-xs block">Communication</span><span className="text-[#FAFAFA]">{displayValue(card.communication_check)}</span></div>
                        <div><span className="text-[#808080] text-xs block">Events</span><span className="text-[#FAFAFA]">{displayValue(card.event_log_summary)}</span></div>
                        <div><span className="text-[#808080] text-xs block">Outage Overlap</span><span className="text-[#FAFAFA]">{displayValue(card.outage_check)}</span></div>
                        <div>
                          <span className="text-[#808080] text-xs block">Triggered Signals</span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {card.triggered_signals ? card.triggered_signals.split(',').map((s, j) => (
                              <span key={j} className="text-xs font-mono px-1.5 py-0.5 bg-[#222222] text-[#999999]">{signalDisplayName(s.trim())}</span>
                            )) : <span className="text-[#808080]">—</span>}
                          </div>
                        </div>
                        <div><span className="text-[#808080] text-xs block">Team</span><span className="text-[#FAFAFA]">{displayValue(card.recommended_team)}</span></div>
                        <div><span className="text-[#808080] text-xs block">Action</span><span className="text-[#FAFAFA]">{displayValue(card.recommended_action)}</span></div>
                      </div>

                      {/* Audit Trail Button */}
                      <div className="mt-4 pt-3 border-t border-[#333333]">
                        <button
                          onClick={() => handleAuditTrail(card.case_id)}
                          className="flex items-center gap-2 text-xs text-[#999999] hover:text-white transition-colors"
                        >
                          <Shield className="w-3 h-3" />
                          {t('Audit Trail')}
                        </button>
                        {auditLoading[card.case_id] && <div className="animate-pulse h-16 bg-[#222222] mt-2 rounded-sm" />}
                        {auditData[card.case_id] && !auditData[card.case_id].error && (
                          <div className="mt-3 p-3 border border-[#333333] bg-[#050505] text-xs space-y-2">
                            <p className="font-mono text-[#808080] break-all">SHA-256: {auditData[card.case_id].legal_compliance?.integrity_hash_sha256 || '\u2014'}</p>
                            <p className="text-[#999999]">Indian Evidence Act, Section 65B · {auditData[card.case_id].legal_compliance?.system || 'Aletheon v4.0'} · Read-only record</p>
                            <p className="text-[#808080]">{auditData[card.case_id].legal_compliance?.generated_at || ''}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
        <Pagination
          page={page}
          pageSize={20}
          totalRecords={cardsData?.pagination?.total_records}
          onPageChange={setPage}
        />
      </section>

      {/* Revenue Impact */}
      <section>
        <button
          onClick={() => setShowRevenue(!showRevenue)}
          className="flex items-center gap-2 text-sm text-[#999999] hover:text-[#FAFAFA] transition-colors mb-4"
        >
          {showRevenue ? <ChevronUp className="w-4 h-4 text-white" /> : <ChevronDown className="w-4 h-4 text-white" />}
          {t('Revenue Impact')} ({sortedRevenue.length} cases)
        </button>
        {showRevenue && (
          <div>
            {revLoading ? (
              <TableSkeleton rows={5} cols={3} />
            ) : revError ? (
              <ErrorState message={revError} onRetry={revRetry} />
            ) : sortedRevenue.length === 0 ? (
              <EmptyState message="No revenue data" />
            ) : (
              <div className="space-y-3">
                {sortedRevenue.slice(0, 20).map((r, i) => (
                  <div key={r.case_id || i} className="flex items-center gap-4">
                    <span className="text-xs font-mono text-[#999999] w-24 flex-shrink-0">{truncateHash(r.case_id, 8)}</span>
                    <div className="flex-1 h-2 bg-[#222222] rounded-sm overflow-hidden">
                      <div
                        className="h-full rounded-sm"
                        style={{
                          width: `${((r.monthly_loss_inr_high || 0) / maxRevenue) * 100}%`,
                          backgroundColor: priorityMap[r.case_id] === 'P1' ? '#EF4444' : '#FAFAFA',
                          opacity: 0.7,
                        }}
                      />
                    </div>
                    <span className="text-xs font-mono text-[#FAFAFA] w-28 text-right">{formatINR(r.monthly_loss_inr_high)}/mo</span>
                  </div>
                ))}
                {aggregateRevenue && (
                  <div className="flex items-center gap-3 pt-2 border-t border-[#333333] mt-2">
                    <span className="text-xs font-mono text-white w-24 flex-shrink-0">AGGREGATE</span>
                    <div className="flex-1" />
                    <span className="text-xs font-mono text-white w-28 text-right">{formatINR(aggregateRevenue.monthly_loss_inr_high)}/mo</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}
