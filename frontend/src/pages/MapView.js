import React, { useState, useMemo, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApiData } from '../hooks/useApiData';
import { getMapMeters, getMapFeeders } from '../api/client';
import { ErrorState } from '../components/ErrorState';
import { getPriorityColor, getBandColor, truncateHash, displayValue } from '../utils/formatters';
import { MapContainer, TileLayer, CircleMarker, Popup, useMap } from 'react-leaflet';
import { ChevronLeft } from 'lucide-react';
import 'leaflet/dist/leaflet.css';

function MapResizer() {
  const map = useMap();
  useEffect(() => {
    setTimeout(() => map.invalidateSize(), 100);
  }, [map]);
  return null;
}

function FlyTo({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) map.flyTo(center, zoom, { duration: 0.8 });
  }, [map, center, zoom]);
  return null;
}

export default function MapView() {
  const [searchParams] = useSearchParams();
  const highlightMeter = searchParams.get('meter');
  const [zoneFilter, setZoneFilter] = useState('');
  const [localityFilter, setLocalityFilter] = useState('');
  const [priorityFilter, setPriorityFilter] = useState('');
  const [showMeters, setShowMeters] = useState(true);
  const [showFeeders, setShowFeeders] = useState(true);
  const [selectedSubdivision, setSelectedSubdivision] = useState(null);

  const { data: meters, loading: mLoading, error: mError, retry: mRetry } = useApiData(getMapMeters);
  const { data: feeders, loading: fLoading, error: fError, retry: fRetry } = useApiData(getMapFeeders);

  const zones = useMemo(() => meters ? [...new Set(meters.map(m => m.zone).filter(Boolean))] : [], [meters]);
  const localities = useMemo(() => meters ? [...new Set(meters.map(m => m.locality).filter(Boolean))] : [], [meters]);

  const subdivisionClusters = useMemo(() => {
    if (!meters) return [];
    const groups = {};
    meters.forEach(m => {
      const loc = m.locality || 'Unknown';
      if (!groups[loc]) groups[loc] = { locality: loc, zone: m.zone, meters: [], lat: 0, lng: 0, p1: 0, p2: 0, p3: 0, total: 0 };
      groups[loc].meters.push(m);
      groups[loc].total++;
      if (m.priority === 'P1') groups[loc].p1++;
      else if (m.priority === 'P2') groups[loc].p2++;
      else if (m.priority === 'P3') groups[loc].p3++;
    });
    return Object.values(groups).map(g => {
      const validMeters = g.meters.filter(m => m.latitude_grid && m.longitude_grid);
      if (validMeters.length === 0) return null;
      g.lat = validMeters.reduce((s, m) => s + m.latitude_grid, 0) / validMeters.length;
      g.lng = validMeters.reduce((s, m) => s + m.longitude_grid, 0) / validMeters.length;
      return g;
    }).filter(Boolean);
  }, [meters]);

  const filteredMeters = useMemo(() => {
    if (!meters) return [];
    return meters.filter(m => {
      if (zoneFilter && m.zone !== zoneFilter) return false;
      if (selectedSubdivision && m.locality !== selectedSubdivision) return false;
      else if (localityFilter && m.locality !== localityFilter) return false;
      if (priorityFilter && m.priority !== priorityFilter) return false;
      return true;
    });
  }, [meters, zoneFilter, localityFilter, priorityFilter, selectedSubdivision]);

  const p1Count = filteredMeters.filter(m => m.priority === 'P1').length;
  const redFeeders = feeders ? feeders.filter(f => f.grid_risk_band === 'RED').length : 0;

  const loading = mLoading || fLoading;
  const error = mError || fError;

  const isSubdivisionView = !selectedSubdivision;

  const mapCenter = useMemo(() => {
    if (selectedSubdivision) {
      const cluster = subdivisionClusters.find(c => c.locality === selectedSubdivision);
      if (cluster) return [cluster.lat, cluster.lng];
    }
    return [12.97, 77.59];
  }, [selectedSubdivision, subdivisionClusters]);

  const mapZoom = selectedSubdivision ? 14 : 12;

  return (
    <div className="h-[calc(100vh-112px)] md:h-[calc(100vh-112px)] relative animate-fadeIn" data-testid="map-view">
      {error && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-[#000000]/80">
          <ErrorState message={error} onRetry={mError ? mRetry : fRetry} />
        </div>
      )}

      {/* Overlay Controls */}
      <div className="absolute top-3 left-3 md:top-4 md:left-4 z-[1000] space-y-2" data-testid="map-controls">
        <div className="bg-[#111111]/95 border border-[#333333] p-3 md:p-4 space-y-3">
          {selectedSubdivision && (
            <button
              onClick={() => setSelectedSubdivision(null)}
              className="flex items-center gap-1.5 text-sm text-white hover:text-[#FAFAFA] transition-colors mb-1"
            >
              <ChevronLeft className="w-4 h-4" />
              <span className="font-mono">{selectedSubdivision}</span>
            </button>
          )}
          {!selectedSubdivision && (
            <p className="text-xs text-[#808080] font-mono uppercase tracking-widest">Subdivision View</p>
          )}
          <select
            value={zoneFilter}
            onChange={(e) => setZoneFilter(e.target.value)}
            className="block w-full bg-[#000000] border border-[#333333] text-sm text-[#FAFAFA] px-2.5 py-1.5 outline-none"
          >
            <option value="">All Zones</option>
            {zones.map(z => <option key={z} value={z}>{z}</option>)}
          </select>
          {selectedSubdivision && (
            <select
              value={priorityFilter}
              onChange={(e) => setPriorityFilter(e.target.value)}
              className="block w-full bg-[#000000] border border-[#333333] text-sm text-[#FAFAFA] px-2.5 py-1.5 outline-none"
            >
              <option value="">All Priority</option>
              <option value="P1">P1</option>
              <option value="P2">P2</option>
              <option value="P3">P3</option>
            </select>
          )}
          {selectedSubdivision && (
            <div className="flex gap-3 pt-1 text-xs text-[#999999]">
              <label className="flex items-center gap-1 cursor-pointer">
                <input type="checkbox" checked={showMeters} onChange={(e) => setShowMeters(e.target.checked)} className="accent-white w-3 h-3" />
                Meters
              </label>
              <label className="flex items-center gap-1 cursor-pointer">
                <input type="checkbox" checked={showFeeders} onChange={(e) => setShowFeeders(e.target.checked)} className="accent-white w-3 h-3" />
                Feeders
              </label>
            </div>
          )}
        </div>
      </div>

      {/* Bottom Stats */}
      <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-[1000] bg-[#000000]/80 border border-[#333333] px-5 py-2.5 text-sm text-white font-mono">
        {selectedSubdivision
          ? <>{filteredMeters.length} meters &middot; {p1Count} P1 alerts &middot; {redFeeders} RED feeders</>
          : <>{subdivisionClusters.length} subdivisions &middot; {meters?.length || 0} total meters &middot; Click to drill down</>
        }
      </div>

      {/* Map */}
      {loading ? (
        <div className="h-full bg-[#111111] flex items-center justify-center">
          <div className="animate-pulse text-[#808080] text-sm">Loading map data...</div>
        </div>
      ) : (
        <MapContainer
          center={[12.97, 77.59]}
          zoom={12}
          className="h-full w-full"
          style={{ background: '#000000' }}
          zoomControl={false}
        >
          <MapResizer />
          <FlyTo center={mapCenter} zoom={mapZoom} />
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/">CARTO</a>'
          />

          {/* Subdivision clusters (overview mode) */}
          {isSubdivisionView && subdivisionClusters
            .filter(c => !zoneFilter || c.zone === zoneFilter)
            .map((cluster, i) => {
              const hasP1 = cluster.p1 > 0;
              const radius = Math.max(18, Math.min(35, cluster.total / 3));
              return (
                <CircleMarker
                  key={`sub-${i}`}
                  center={[cluster.lat, cluster.lng]}
                  radius={radius}
                  pathOptions={{
                    color: hasP1 ? '#EF4444' : '#FAFAFA',
                    fillColor: hasP1 ? '#EF4444' : '#FAFAFA',
                    fillOpacity: 0.15,
                    weight: 1.5,
                  }}
                  eventHandlers={{
                    click: () => setSelectedSubdivision(cluster.locality),
                  }}
                >
                  <Popup>
                    <div className="text-xs space-y-1.5 text-[#FAFAFA] min-w-[140px]">
                      <p className="font-mono font-bold text-sm">{cluster.locality}</p>
                      <p className="text-[#999999]">{cluster.zone}</p>
                      <p>{cluster.total} meters</p>
                      {cluster.p1 > 0 && <p className="text-[#EF4444]">{cluster.p1} P1 alerts</p>}
                      {cluster.p2 > 0 && <p className="text-[#F59E0B]">{cluster.p2} P2 alerts</p>}
                      {cluster.p3 > 0 && <p className="text-[#3B82F6]">{cluster.p3} P3 alerts</p>}
                      <p className="text-[#808080] italic mt-1">Click to drill down</p>
                    </div>
                  </Popup>
                </CircleMarker>
              );
            })}

          {/* Individual meters (drill-down mode) */}
          {!isSubdivisionView && showMeters && filteredMeters.map((m, i) => {
            if (!m.latitude_grid || !m.longitude_grid) return null;
            const color = getPriorityColor(m.priority);
            const radius = m.priority === 'P1' ? 8 : m.priority === 'P2' ? 7 : m.priority === 'P3' ? 6 : 4;
            const isHighlighted = highlightMeter && m.meter_id_hash === highlightMeter;
            return (
              <CircleMarker
                key={`m-${i}`}
                center={[m.latitude_grid, m.longitude_grid]}
                radius={isHighlighted ? 10 : radius}
                pathOptions={{
                  color: isHighlighted ? '#FFFFFF' : color,
                  fillColor: color,
                  fillOpacity: 0.7,
                  weight: isHighlighted ? 2 : 1,
                }}
              >
                <Popup>
                  <div className="text-xs space-y-1 text-[#FAFAFA]">
                    <p className="font-mono font-bold">{truncateHash(m.meter_id_hash, 12)}</p>
                    <p>Priority: {m.priority || 'None'}</p>
                    <p>Risk: {displayValue(m.risk_score)}</p>
                    <p>Locality: {displayValue(m.locality)}</p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}

          {/* Feeder markers (drill-down mode) */}
          {!isSubdivisionView && showFeeders && feeders && feeders
            .filter(f => !selectedSubdivision || f.locality === selectedSubdivision)
            .map((f, i) => {
            if (!f.latitude_grid || !f.longitude_grid) return null;
            const color = getBandColor(f.grid_risk_band);
            return (
              <CircleMarker
                key={`f-${i}`}
                center={[f.latitude_grid, f.longitude_grid]}
                radius={9}
                pathOptions={{
                  color: color,
                  fillColor: color,
                  fillOpacity: 0.7,
                  weight: 2,
                }}
              >
                <Popup>
                  <div className="text-xs space-y-1 text-[#FAFAFA]">
                    <p className="font-mono font-bold">{truncateHash(f.feeder_id_hash, 12)}</p>
                    <p>Band: {f.grid_risk_band}</p>
                    <p>Peak: {f.peak_load_pct ? `${Number(f.peak_load_pct).toFixed(4)}%` : '—'}</p>
                    <p>Locality: {displayValue(f.locality)}</p>
                  </div>
                </Popup>
              </CircleMarker>
            );
          })}
        </MapContainer>
      )}
    </div>
  );
}
