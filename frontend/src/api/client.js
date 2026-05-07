import axios from 'axios';

const BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for consistent error handling
api.interceptors.response.use(
  (response) => {
    // Check for API-level errors (200 with { error: "..." })
    if (response.data && response.data.error && !response.data.data) {
      return Promise.reject({
        message: response.data.error,
        isApiError: true,
        response,
      });
    }
    return response;
  },
  (error) => {
    const message = error.response?.data?.error || error.response?.data?.detail || error.message || 'Network error';
    return Promise.reject({ message, isApiError: false, response: error.response });
  }
);

// ==================== GRID ====================
export const getGridOverview = () => api.get('/api/grid/overview').then(r => r.data);
export const getGridStress = (params = {}) => api.get('/api/grid/stress', { params }).then(r => r.data);
export const getGridStressFeeder = (feederId) => api.get(`/api/grid/stress/${feederId}`).then(r => r.data);

// ==================== ANOMALY ====================
export const getAnomalyOverview = () => api.get('/api/anomaly/overview').then(r => r.data);
export const getAnomalyScores = (params = {}) => api.get('/api/anomaly/scores', { params }).then(r => r.data);
export const getAnomalyScoresMeter = (meterId) => api.get(`/api/anomaly/scores/${meterId}`).then(r => r.data);
export const getActionSheet = (params = {}) => api.get('/api/anomaly/action-sheet', { params }).then(r => r.data);
export const getActionSheetCase = (caseId) => api.get(`/api/anomaly/action-sheet/${caseId}`).then(r => r.data);
export const getSignalSummary = () => api.get('/api/anomaly/signals').then(r => r.data);

// ==================== EVIDENCE ====================
export const getEvidenceCards = (params = {}) => api.get('/api/evidence/cards', { params }).then(r => r.data);
export const getEvidenceCard = (caseId) => api.get(`/api/evidence/cards/${caseId}`).then(r => r.data);
export const getEvidenceMeter = (meterId) => api.get(`/api/evidence/meter/${meterId}`).then(r => r.data);

// ==================== FORECAST ====================
export const getForecastOverview = () => api.get('/api/forecast/overview').then(r => r.data);
export const getFeederForecast = (feederId, testOnly = false) => api.get(`/api/forecast/feeder/${feederId}`, { params: { test_only: testOnly } }).then(r => r.data);
export const getForecastTimeseries = (params = {}) => api.get('/api/forecast/timeseries', { params }).then(r => r.data);
export const getBaselines = () => api.get('/api/forecast/baselines').then(r => r.data);
export const getFeatureImportance = () => api.get('/api/forecast/feature-importance').then(r => r.data);
export const getDemandAlerts = () => api.get('/api/forecast/demand-alerts').then(r => r.data);

// ==================== KPI ====================
export const getKPIDashboard = () => api.get('/api/kpi/dashboard').then(r => r.data);
export const getFPAudit = () => api.get('/api/kpi/false-positive-audit').then(r => r.data);
export const getFPRateBySignal = () => api.get('/api/kpi/fp-rate-by-signal').then(r => r.data);
export const getEvaluation = () => api.get('/api/kpi/evaluation').then(r => r.data);
export const getRevenueImpact = () => api.get('/api/kpi/revenue-impact').then(r => r.data);
export const getThresholds = () => api.get('/api/kpi/thresholds').then(r => r.data);

// ==================== MAP ====================
export const getMapMeters = (params = {}) => api.get('/api/map/meters', { params }).then(r => r.data);
export const getMapFeeders = () => api.get('/api/map/feeders').then(r => r.data);
export const getMapDTs = (params = {}) => api.get('/api/map/dts', { params }).then(r => r.data);

// ==================== CALENDAR ====================
export const getHolidays = (params = {}) => api.get('/api/calendar/holidays', { params }).then(r => r.data);

// ==================== NOTIFY ====================
export const sendSMS = (data) => api.post('/api/notify/sms', data).then(r => r.data);
export const sendAlert = (data) => api.post('/api/notify/alert', data).then(r => r.data);

// ==================== FEEDBACK ====================
export const submitFeedback = (data) => api.post('/api/feedback/submit', data).then(r => r.data);
export const getFeedbackList = (params = {}) => api.get('/api/feedback/list', { params }).then(r => r.data);
export const getFeedbackStats = () => api.get('/api/feedback/stats').then(r => r.data);

// ==================== TRANSLATIONS ====================
export const translateToKannada = (text) => api.post('/api/translations/kannada', { text }).then(r => r.data);
export const translateBatch = (texts) => api.post('/api/translations/kannada/batch', { texts }).then(r => r.data);
export const getTranslationCacheStats = () => api.get('/api/translations/cache-stats').then(r => r.data);

// ==================== DEMO ====================
export const getDemoCases = () => api.get('/api/demo/cases').then(r => r.data);
export const getAuditTrail = (caseId) => api.get(`/api/demo/audit-trail/${caseId}`).then(r => r.data);
export const getPipelineSummary = () => api.get('/api/demo/pipeline-summary').then(r => r.data);
export const getDataHealth = () => api.get('/api/demo/data-health').then(r => r.data);

export default api;
