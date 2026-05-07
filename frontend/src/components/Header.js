import React from 'react';
import { useLocation } from 'react-router-dom';
import { useTranslation } from '../context/TranslationContext';
import { useApiData } from '../hooks/useApiData';
import { getDataHealth } from '../api/client';
import { Menu } from 'lucide-react';

const pageTitles = {
  '/': 'Command Center',
  '/anomaly': 'Anomaly Detection',
  '/grid': 'Grid Watch',
  '/evidence': 'Evidence Cards',
  '/map': 'Map View',
  '/settings': 'Settings',
};

export default function Header({ onMenuOpen }) {
  const { t, lang, toggleLanguage, loading: translating } = useTranslation();
  const location = useLocation();
  const { data: health } = useApiData(getDataHealth, []);

  const title = pageTitles[location.pathname] || 'Aletheon';
  const isHealthy = health && (!health.errors || health.errors.length === 0);

  return (
    <header className="h-14 flex items-center justify-between px-4 md:px-6 border-b border-[#333333] bg-[#060606] flex-shrink-0">
      <div className="flex items-center gap-3">
        {/* Mobile hamburger */}
        <button
          onClick={onMenuOpen}
          className="lg:hidden text-[#999999] hover:text-white p-1"
          data-testid="mobile-menu-button"
        >
          <Menu className="w-5 h-5" />
        </button>
        <h1 className="text-base md:text-lg font-light tracking-tight text-[#FAFAFA]" data-testid="page-title">
          {t(title)}
        </h1>
      </div>
      <div className="flex items-center gap-3 md:gap-4">
        {/* Health dot */}
        <div className="flex items-center gap-2">
          <div
            className={`w-1.5 h-1.5 rounded-full ${isHealthy === true ? 'bg-[#22C55E]' : isHealthy === false ? 'bg-[#EF4444]' : 'bg-[#525252]'}`}
            title={isHealthy ? 'System healthy' : 'System status unknown'}
          />
        </div>
        {/* Language toggle */}
        <button
          onClick={toggleLanguage}
          disabled={translating}
          className="text-sm px-3 py-1.5 border border-[#444444] hover:border-white text-[#FAFAFA] hover:text-white transition-all duration-200 font-mono rounded-sm"
          data-testid="lang-toggle"
        >
          {lang === 'en' ? (
            <span><span className="text-white font-medium">EN</span> <span className="text-[#666666] mx-0.5">|</span> <span className="text-[#808080]">ಕನ್ನಡ</span></span>
          ) : (
            <span><span className="text-[#808080]">EN</span> <span className="text-[#666666] mx-0.5">|</span> <span className="text-white font-medium">ಕನ್ನಡ</span></span>
          )}
        </button>
      </div>
    </header>
  );
}
