/**
 * Format a number as Indian Rupees
 */
export const formatINR = (n) => {
  if (n === null || n === undefined || isNaN(n)) return '—';
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: 'INR',
    maximumFractionDigits: 0,
  }).format(n);
};

/**
 * Format as percentage
 */
export const formatPercent = (n, decimals = 1) => {
  if (n === null || n === undefined || isNaN(n)) return '—';
  return `${Number(n).toFixed(decimals)}%`;
};

/**
 * Format number with Indian grouping
 */
export const formatNumber = (n) => {
  if (n === null || n === undefined || isNaN(n)) return '—';
  return new Intl.NumberFormat('en-IN').format(n);
};

/**
 * Display value — returns dash for null/undefined/NaN
 */
export const displayValue = (v) => {
  if (v === null || v === undefined || (typeof v === 'number' && isNaN(v))) return '—';
  if (typeof v === 'number') return Number.isInteger(v) ? String(v) : v.toFixed(4);
  return String(v);
};

/**
 * Truncate hash string
 */
export const truncateHash = (s, len = 8) => {
  if (!s) return '—';
  if (s.length <= len) return s;
  return s.substring(0, len) + '...';
};

/**
 * Convert signal key to display name
 */
export const signalDisplayName = (s) => {
  if (!s) return '—';
  const map = {
    sig_peer_drift: 'Peer Drift',
    sig_sudden_drop: 'Sudden Drop',
    sig_billing_cycle_drop: 'Billing Cycle Drop',
    sig_tamper_event: 'Tamper Event',
    sig_after_hours_commercial: 'After Hours',
    sig_comm_failure: 'Comm Failure',
    sig_reading_plateau: 'Reading Plateau',
    sig_pf_register: 'Power Factor',
    sig_genuine_low_usage_context: 'Genuine Low Usage',
    sig_solar_export_normal: 'Solar Export',
    sig_ev_consistent_night_pattern: 'EV Night Pattern',
  };
  return map[s] || s.replace(/^sig_/, '').replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

/**
 * Clean tier name for display
 */
export const cleanTierName = (s) => {
  if (!s) return '—';
  return s.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
};

/**
 * Get priority color
 */
export const getPriorityColor = (priority) => {
  switch (priority?.toUpperCase()) {
    case 'P1': return '#EF4444';
    case 'P2': return '#F59E0B';
    case 'P3': return '#3B82F6';
    default: return '#A0A0A0';
  }
};

/**
 * Get grid band color
 */
export const getBandColor = (band) => {
  switch (band?.toUpperCase()) {
    case 'RED': return '#EF4444';
    case 'AMBER': return '#F59E0B';
    case 'GREEN': return '#22C55E';
    default: return '#A0A0A0';
  }
};
