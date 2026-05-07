import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Search, Zap, FileText, MapPin, Settings, X } from 'lucide-react';
import { useTranslation } from '../context/TranslationContext';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Command Center' },
  { path: '/anomaly', icon: Search, label: 'Anomaly Detection' },
  { path: '/grid', icon: Zap, label: 'Grid Watch' },
  { path: '/evidence', icon: FileText, label: 'Evidence Cards' },
  { path: '/map', icon: MapPin, label: 'Map View' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function MobileNav({ open, onClose }) {
  const { t } = useTranslation();
  const location = useLocation();

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 lg:hidden" data-testid="mobile-nav">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/70" onClick={onClose} />

      {/* Drawer */}
      <nav className="absolute left-0 top-0 bottom-0 w-[260px] bg-[#060606] border-r border-[#333333] flex flex-col animate-slideInLeft">
        {/* Header */}
        <div className="h-14 flex items-center justify-between px-4 border-b border-[#333333]">
          <span className="text-xs font-mono tracking-[0.2em] uppercase text-white font-semibold">ALETHEON</span>
          <button onClick={onClose} className="text-[#999999] hover:text-white p-1">
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Links */}
        <div className="flex-1 py-4 space-y-1">
          {navItems.map(({ path, icon: Icon, label }) => {
            const isActive = path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);
            return (
              <NavLink
                key={path}
                to={path}
                onClick={onClose}
                className={`group flex items-center gap-3 px-4 py-3 relative transition-colors duration-200 ${
                  isActive ? 'text-white' : 'text-[#999999] hover:text-[#FAFAFA]'
                }`}
              >
                {isActive && (
                  <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-5 bg-white" />
                )}
                <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-white' : 'text-[#808080]'}`} />
                <span className="text-sm">{t(label)}</span>
              </NavLink>
            );
          })}
        </div>

        {/* Footer */}
        <div className="px-4 py-3 border-t border-[#333333]">
          <span className="text-xs text-[#808080]">v4.0 · BESCOM Theme 8</span>
        </div>
      </nav>
    </div>
  );
}
