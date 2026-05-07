import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { translateBatch } from '../api/client';

const TranslationContext = createContext();

// Predefined UI label keys
const UI_LABELS = [
  'Command Center', 'Anomaly Detection', 'Grid Watch', 'Evidence Cards',
  'Map View', 'Settings', 'Priority', 'Risk Score', 'Confidence',
  'Revenue Impact', 'Recommended Team', 'Total Meters', 'Active Meters',
  'P1 Inspection Ready', 'P2 Desk Review', 'P3 Watchlist', 'Forecast',
  'Grid Stress', 'Healthy', 'Send Alert', 'Submit Feedback', 'Peer Drift',
  'Sudden Drop', 'Tamper Event', 'Billing Cycle Drop', 'Communication Failure',
  'Reading Plateau', 'Power Factor', 'After Hours', 'Vigilance', 'Metering',
  'Evidence Card', 'Audit Trail', 'Legal Compliance', 'Revenue at Risk',
  'False Positive Rate', 'Feature Importance', 'Baseline Comparison',
  'Karnataka Holidays', 'Field Feedback', 'Demand Alerts'
];

export function TranslationProvider({ children }) {
  const [lang, setLang] = useState('en');
  const [translations, setTranslations] = useState({});
  const [loading, setLoading] = useState(false);
  const fetchedRef = useRef(false);

  const toggleLanguage = useCallback(async () => {
    if (lang === 'en') {
      // Switch to Kannada
      if (!fetchedRef.current) {
        setLoading(true);
        try {
          const results = await translateBatch(UI_LABELS);
          const map = {};
          if (Array.isArray(results)) {
            results.forEach((item) => {
              if (item.english && item.kannada) {
                map[item.english] = item.kannada;
              }
            });
          }
          setTranslations(map);
          fetchedRef.current = true;
        } catch (e) {
          // Silently fall back to English
          console.warn('Translation API unavailable, using English fallback');
        } finally {
          setLoading(false);
        }
      }
      setLang('kn');
    } else {
      setLang('en');
    }
  }, [lang]);

  const t = useCallback((key) => {
    if (lang === 'kn' && translations[key]) {
      return translations[key];
    }
    return key;
  }, [lang, translations]);

  return (
    <TranslationContext.Provider value={{ lang, t, toggleLanguage, loading }}>
      {children}
    </TranslationContext.Provider>
  );
}

export function useTranslation() {
  const context = useContext(TranslationContext);
  if (!context) {
    throw new Error('useTranslation must be used within TranslationProvider');
  }
  return context;
}
