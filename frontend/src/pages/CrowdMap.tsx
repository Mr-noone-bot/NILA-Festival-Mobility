import { useState } from 'react';
import {
  Bus,
  Clock,
  Compass,
  Filter,
  Layers,
  Navigation,
  RotateCcw,
  ShieldAlert,
  Users,
} from 'lucide-react';
import MapCanvas from '../components/MapCanvas';
import type { BusMove, CrowdPoint, Festival, RiskLevel, Stop } from '../types/nila';
import { formatNumber, riskLabel, toRiskClass } from '../utils/format';

interface CrowdMapProps {
  festival: Festival;
  stops: Stop[];
  points: CrowdPoint[];
  move?: BusMove | null;
  selectedStop: Stop | null;
  onSelectStop: (stop: Stop) => void;
  routeGeometry?: [number, number][] | null;
}

export default function CrowdMap({
  festival,
  stops,
  points,
  move,
  selectedStop,
  onSelectStop,
  routeGeometry,
}: CrowdMapProps) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [showRoute, setShowRoute] = useState(true);
  const [riskFilter, setRiskFilter] = useState<RiskLevel | 'ALL'>('ALL');

  const filteredStops = stops.filter((stop) => {
    if (riskFilter === 'ALL') return true;
    return stop.risk === riskFilter;
  });

  return (
    <div className="space-y-6">
      {/* Top Map Control Bar */}
      <div className="bg-white border border-sky-200 rounded-2xl p-4 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sky-700">
            Geospatial Intelligence
          </div>
          <h2 className="text-lg font-black text-slate-900 flex items-center gap-2">
            Festival Transit & Crowd Density Map
            <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-sky-100 text-sky-800 border border-sky-200">
              {festival.city}
            </span>
          </h2>
        </div>

        {/* Toggles */}
        <div className="flex flex-wrap items-center gap-2 w-full md:w-auto">
          <button
            onClick={() => setShowHeatmap((prev) => !prev)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 border transition-all ${
              showHeatmap
                ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Layers size={15} /> Crowd Heatmap: {showHeatmap ? 'ON' : 'OFF'}
          </button>

          <button
            onClick={() => setShowRoute((prev) => !prev)}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5 border transition-all ${
              showRoute
                ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Navigation size={15} /> Repositioning Corridor: {showRoute ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Main Map View & Inspector Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Large Map Area (2 cols) */}
        <div className="lg:col-span-2 bg-white border border-sky-100 rounded-2xl p-4 shadow-sm flex flex-col">
          <div className="h-[560px] w-full rounded-xl overflow-hidden border border-sky-200 relative shadow-inner">
            <MapCanvas
              center={festival.coordinates}
              stops={filteredStops}
              points={points}
              route={showRoute && move ? { from: move.sourceStop, to: move.destinationStop } : null}
              routeGeometry={routeGeometry}
              showHeatmap={showHeatmap}
              onStopSelect={onSelectStop}
            />
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 text-xs text-slate-600 px-1">
            <div className="flex items-center gap-2">
              <Compass size={14} className="text-sky-600" />
              <span>Center: {festival.temple}</span>
            </div>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5 font-semibold text-slate-800">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Critical Risk Stop
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-slate-800">
                <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Moderate Risk Stop
              </span>
              <span className="flex items-center gap-1.5 font-semibold text-slate-800">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" /> Normal Buffer Stop
              </span>
            </div>
          </div>
        </div>

        {/* Right Rail: Stop Inspector & Risk Filtering */}
        <div className="space-y-6">
          {/* Risk Level Filter Chips */}
          <div className="bg-white border border-sky-100 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700 flex items-center gap-1.5">
                <Filter size={14} className="text-sky-600" /> Filter Terminals by Risk
              </h4>
              {riskFilter !== 'ALL' && (
                <button
                  onClick={() => setRiskFilter('ALL')}
                  className="text-[11px] font-semibold text-sky-600 hover:underline flex items-center gap-1"
                >
                  <RotateCcw size={11} /> Reset
                </button>
              )}
            </div>

            <div className="flex flex-wrap gap-1.5">
              {(['ALL', 'CRITICAL', 'HIGH', 'MODERATE', 'LOW'] as const).map((lvl) => (
                <button
                  key={lvl}
                  onClick={() => setRiskFilter(lvl)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    riskFilter === lvl
                      ? 'bg-sky-600 text-white shadow-sm'
                      : 'bg-slate-100 hover:bg-sky-50 text-slate-700'
                  }`}
                >
                  {lvl === 'ALL' ? 'All Terminals' : riskLabel(lvl)}
                </button>
              ))}
            </div>
          </div>

          {/* Inspected Stop Card */}
          <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-bold text-sky-700 uppercase tracking-wider">
                  Terminal Detailed Audit
                </span>
                <h3 className="text-xl font-black text-slate-900 mt-1">
                  {selectedStop ? selectedStop.name : 'Click any map pin'}
                </h3>
              </div>
              {selectedStop && (
                <span className={`risk-pill ${toRiskClass(selectedStop.risk)}`}>
                  <span className="risk-dot" />
                  {riskLabel(selectedStop.risk)}
                </span>
              )}
            </div>

            {selectedStop ? (
              <div className="space-y-3 pt-2 border-t border-slate-100">
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="p-3 bg-sky-50/70 rounded-xl border border-sky-100">
                    <div className="text-slate-500 flex items-center gap-1 mb-1">
                      <Users size={12} /> Modeled Queue
                    </div>
                    <div className="text-lg font-black text-slate-900">
                      {formatNumber(selectedStop.crowd)}
                    </div>
                    <div className="text-[11px] text-slate-500">waiting pilgrims</div>
                  </div>

                  <div className="p-3 bg-sky-50/70 rounded-xl border border-sky-100">
                    <div className="text-slate-500 flex items-center gap-1 mb-1">
                      <Bus size={12} /> Active Fleet
                    </div>
                    <div className="text-lg font-black text-sky-800">
                      {selectedStop.currentBuses}
                    </div>
                    <div className="text-[11px] text-slate-500">
                      rec: {selectedStop.recommendedBuses} buses
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 space-y-2 text-xs">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600 flex items-center gap-1">
                      <Clock size={12} /> Average Passenger Wait:
                    </span>
                    <strong className="text-slate-900">{selectedStop.waitMinutes} minutes</strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Terminal Safe Capacity:</span>
                    <strong className="text-slate-900">
                      {formatNumber(selectedStop.capacity)} passengers
                    </strong>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-600">Capacity Overload Ratio:</span>
                    <strong
                      className={
                        selectedStop.crowd > selectedStop.capacity
                          ? 'text-red-600'
                          : 'text-emerald-600'
                      }
                    >
                      {Math.round((selectedStop.crowd / selectedStop.capacity) * 100)}%
                    </strong>
                  </div>
                </div>

                {move && selectedStop.id === move.destinationStop && (
                  <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs text-emerald-900">
                    <div className="font-bold flex items-center gap-1 mb-0.5">
                      <Bus size={13} /> Receiving {move.buses} Reassigned Buses
                    </div>
                    Arriving at {move.arrival} to clear peak queue bottleneck.
                  </div>
                )}

                {move && selectedStop.id === move.sourceStop && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900">
                    <div className="font-bold flex items-center gap-1 mb-0.5">
                      <ShieldAlert size={13} /> Donor Terminal (-{move.buses} Buses)
                    </div>
                    Departs at {move.departure} with acceptable trade-off buffer.
                  </div>
                )}
              </div>
            ) : (
              <div className="text-xs text-slate-500 text-center py-8">
                Click any bus terminal dot on the interactive map or from the list below to inspect its operational metrics.
              </div>
            )}
          </div>

          {/* All Terminal List */}
          <div className="bg-white border border-sky-100 rounded-2xl p-5 shadow-sm space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-slate-700">
              Terminal Directory ({filteredStops.length})
            </h4>
            <div className="space-y-1.5 max-h-[180px] overflow-y-auto pr-1">
              {filteredStops.map((st) => (
                <button
                  key={st.id}
                  onClick={() => onSelectStop(st)}
                  className={`w-full text-left p-2 rounded-xl border text-xs flex items-center justify-between transition-colors ${
                    selectedStop?.id === st.id
                      ? 'border-sky-500 bg-sky-50 font-bold text-sky-950'
                      : 'border-slate-100 hover:border-sky-200 text-slate-700'
                  }`}
                >
                  <span className="truncate">{st.name}</span>
                  <span className="shrink-0 font-medium text-slate-500">
                    {st.currentBuses} buses
                  </span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
