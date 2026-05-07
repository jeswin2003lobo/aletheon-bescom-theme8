import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { TranslationProvider } from './context/TranslationContext';
import Layout from './components/Layout';
import CommandCenter from './pages/CommandCenter';
import AnomalyDetection from './pages/AnomalyDetection';
import GridWatch from './pages/GridWatch';
import EvidenceCards from './pages/EvidenceCards';
import MapView from './pages/MapView';
import Settings from './pages/Settings';
import './App.css';

function App() {
  return (
    <TranslationProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route path="/" element={<CommandCenter />} />
            <Route path="/anomaly" element={<AnomalyDetection />} />
            <Route path="/grid" element={<GridWatch />} />
            <Route path="/evidence" element={<EvidenceCards />} />
            <Route path="/map" element={<MapView />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </TranslationProvider>
  );
}

export default App;
