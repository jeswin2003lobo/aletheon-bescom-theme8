import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { LayoutDashboard, Search, Zap, FileText, MapPin, Settings, PanelLeftClose, PanelLeft } from 'lucide-react';
import { useTranslation } from '../context/TranslationContext';

const navItems = [
  { path: '/', icon: LayoutDashboard, label: 'Command Center' },
  { path: '/anomaly', icon: Search, label: 'Anomaly Detection' },
  { path: '/grid', icon: Zap, label: 'Grid Watch' },
  { path: '/evidence', icon: FileText, label: 'Evidence Cards' },
  { path: '/map', icon: MapPin, label: 'Map View' },
  { path: '/settings', icon: Settings, label: 'Settings' },
];

export default function Sidebar({ collapsed, onToggle }) {
  const { t } = useTranslation();
  const location = useLocation();

  return (
    <aside
      className={`hidden lg:flex flex-col border-r border-[#333333] bg-[#060606] transition-all duration-300 ${
        collapsed ? 'w-[60px]' : 'w-[240px]'
      }`}
      data-testid="sidebar"
    >
      {/* Logo */}
      <div className="h-14 flex items-center px-4 border-b border-[#333333]">
        {collapsed ? (
          <span className="text-xs font-mono tracking-[0.2em] text-white font-semibold mx-auto">A</span>
        ) : (
          <span className="text-xs font-mono tracking-[0.2em] uppercase text-white font-semibold">ALETHEON</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4 space-y-1">
        {navItems.map(({ path, icon: Icon, label }) => {
          const isActive = path === '/' ? location.pathname === '/' : location.pathname.startsWith(path);
          return (
            <NavLink
              key={path}
              to={path}
              className={`group flex items-center gap-3 px-4 py-2.5 relative transition-colors duration-200 ${
                isActive
                  ? 'text-white'
                  : 'text-[#999999] hover:text-[#FAFAFA]'
              }`}
              title={collapsed ? t(label) : undefined}
              data-testid={`nav-${path.replace('/', '') || 'home'}`}
            >
              {isActive && (
                <div className="absolute left-0 top-1/2 -translate-y-1/2 w-[2px] h-5 bg-white" />
              )}
              <Icon className={`w-4 h-4 flex-shrink-0 ${isActive ? 'text-white' : 'text-[#808080] group-hover:text-[#FAFAFA]'}`} />
              {!collapsed && (
                <span className="text-sm truncate">{t(label)}</span>
              )}
            </NavLink>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[#333333] flex items-center justify-between">
        {!collapsed && (
          <span className="text-xs text-[#808080]">v4.0 · BESCOM</span>
        )}
        <button
          onClick={onToggle}
          className="text-[#808080] hover:text-[#FAFAFA] transition-colors p-1"
          data-testid="sidebar-toggle"
        >
          {collapsed ? <PanelLeft className="w-4 h-4" /> : <PanelLeftClose className="w-4 h-4" />}
        </button>
      </div>
    </aside>
  );
}
