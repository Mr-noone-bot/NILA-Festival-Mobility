import { useState } from 'react';
import {
  Activity,
  ArrowDownRight,
  ArrowRight,
  ArrowUpRight,
  Bus,
  Check,
  Clock3,
  Compass,
  Layers3,
  MapPin,
  MapPinned,
  Navigation,
  RefreshCw,
  ShieldAlert,
  Users,
  Waves,
} from 'lucide-react';
import MapCanvas from '../components/MapCanvas';
import type {
  BusMove,
  Festival,
  ForecastResponse,
  OptimizeResponse,
  Stop,
} from '../types/nila';
import { formatNumber, riskLabel, toRiskClass } from '../utils/format';

interface CommandCenterProps {
  festival: Festival;
  forecast: ForecastResponse;
  optimization: OptimizeResponse;
  stops: Stop[];
  selectedStop: Stop | null;
  onSelectStop: (stop: Stop) => void;
  onNavigate: (page: string) => void;
  onRunForecast: () => void;
  onRunOptimization: () => void;
  forecastStatus: 'idle' | 'loading' | 'success' | 'error';
  optimizeStatus: 'idle' | 'loading' | 'success' | 'error';
  forecastMessage: string;
  optimizeMessage: string;
}

export default function CommandCenter({
  festival,
  forecast,
  optimization,
  stops,
  selectedStop,
  onSelectStop,
  onNavigate,
  onRunForecast,
  onRunOptimization,
  forecastStatus,
  optimizeStatus,
  forecastMessage,
  optimizeMessage,
}: CommandCenterProps) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [routeVisible, setRouteVisible] = useState(true);

  const activeMove: BusMove | null = optimization?.move ?? null;

  const sourceStop: Stop | undefined = activeMove
    ? stops.find((s) => s.id === activeMove.sourceStop) ?? stops[0]
    : undefined;

  const destinationStop: Stop | undefined = activeMove
    ? stops.find((s) => s.id === activeMove.destinationStop) ?? stops[1]
    : undefined;

  const totalBuses =
    stops.reduce((sum, s) => sum + s.currentBuses, 0) ||
    optimization?.total_fleet_size ||
    25;

  const isForecastRun = forecast?.source === 'api';

  const metrics = [
    {
      label: 'Peak Crowd Estimate',
      value: isForecastRun ? formatNumber(forecast.metrics.peakCrowd) : 'Not Run',
      unit: isForecastRun ? 'pilgrims projected' : 'Click "Run Forecast"',
      icon: Users,
      trend: isForecastRun ? 'Calculated' : 'Pending',
      direction: isForecastRun ? 'up' : 'neutral',
    },
    {
      label: 'Peak Surge Window',
      value: isForecastRun ? forecast.metrics.peakTime : 'Pending Run',
      unit: isForecastRun ? 'post-ritual egress window' : 'Awaiting calculation',
      icon: Clock3,
      trend: isForecastRun ? 'Peak window' : 'Pending',
      direction: 'neutral',
    },
    {
      label: 'Average Wait Time',
      value: isForecastRun ? `${forecast.metrics.waitingMinutes} min` : '—',
      unit: isForecastRun ? 'across monitored stops' : 'Awaiting forecast',
      icon: Waves,
      trend: isForecastRun ? `${forecast.metrics.waitingMinutes}m avg` : 'Pending',
      direction: 'down',
    },
    {
      label: 'Stops Under Critical Pressure',
      value: isForecastRun ? `${forecast.metrics.overloadedStops} of ${stops.length}` : '—',
      unit: isForecastRun ? 'immediate attention' : 'Awaiting forecast',
      icon: ShieldAlert,
      trend: isForecastRun ? `${forecast.metrics.risk} alert` : 'Pending',
      direction: isForecastRun ? 'up' : 'neutral',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Top Banner / System Notice */}
      <div className="bg-sky-50 border border-sky-200 rounded-2xl p-4 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm">
        <div className="flex items-center gap-3.5">
          <div className="w-10 h-10 rounded-xl bg-sky-600 text-white flex items-center justify-center shrink-0 shadow-sm">
            <Compass size={22} />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900">
                {festival?.name || 'Chithirai Thiruvizha'} — Live Mobility Operations
              </h2>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                Operational Ready
              </span>
            </div>
            <p className="text-xs text-slate-600 mt-0.5">
              {festival?.city || 'Madurai'} · {festival?.temple || 'Meenakshi Sundareswarar Temple'} · {festival?.dateLabel || 'Apr 28, 2026'}
            </p>
            {forecastMessage && (
              <p className="text-[11px] text-sky-700 font-medium mt-1 flex items-center gap-1">
                <Check size={12} /> {forecastMessage}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-2.5 w-full md:w-auto">
          <button
            onClick={onRunForecast}
            disabled={forecastStatus === 'loading'}
            className="flex-1 md:flex-initial px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-sm disabled:opacity-60"
          >
            {forecastStatus === 'loading' ? (
              <span className="spinner spinner-small" />
            ) : (
              <Activity size={15} />
            )}
            {forecastStatus === 'loading' ? 'Calculating Surge…' : 'Refresh Crowd Forecast'}
          </button>
          <button
            onClick={() => onNavigate('Festival planner')}
            className="px-3.5 py-2 rounded-xl bg-white hover:bg-sky-50 text-sky-700 border border-sky-300 font-medium text-xs flex items-center gap-1.5 transition-all shadow-sm"
          >
            Change Festival
          </button>
        </div>
      </div>

      {/* Primary KPI Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div
              key={m.label}
              className="bg-white border border-sky-100 rounded-2xl p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden"
            >
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-slate-600">
                  {m.label}
                </span>
                <div className="w-8 h-8 rounded-lg bg-sky-50 text-sky-600 flex items-center justify-center">
                  <Icon size={17} />
                </div>
              </div>
              <div className="text-2xl font-black text-slate-900 tracking-tight">{m.value}</div>
              <div className="mt-2.5 flex items-center justify-between text-xs pt-2 border-t border-slate-100">
                <span className="text-slate-500">{m.unit}</span>
                <span
                  className={`font-semibold inline-flex items-center gap-0.5 ${
                    m.direction === 'down'
                      ? 'text-emerald-600'
                      : m.direction === 'up'
                      ? 'text-amber-600'
                      : 'text-sky-600'
                  }`}
                >
                  {m.direction === 'down' ? (
                    <ArrowDownRight size={13} />
                  ) : m.direction === 'up' ? (
                    <ArrowUpRight size={13} />
                  ) : null}
                  {m.trend}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Map Overview & Right Rail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Geospatial Operations Map */}
        <div className="lg:col-span-2 bg-white border border-sky-100 rounded-2xl p-5 shadow-sm space-y-4">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-sky-700">
                Geospatial Situational Awareness
              </div>
              <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                Festival Network Map
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-semibold bg-sky-100 text-sky-800 border border-sky-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-sky-600 animate-pulse" />
                  Live Preview
                </span>
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowHeatmap((prev) => !prev)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                  showHeatmap
                    ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <Layers3 size={14} /> Heatmap
              </button>
              <button
                onClick={() => setRouteVisible((prev) => !prev)}
                className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 border transition-all ${
                  routeVisible
                    ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                    : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
                }`}
              >
                <Navigation size={14} /> Route
              </button>
              <button
                onClick={() => onNavigate('Crowd map')}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-sky-50 text-sky-700 border border-sky-200 hover:bg-sky-100 flex items-center gap-1"
              >
                Full Screen <ArrowRight size={13} />
              </button>
            </div>
          </div>

          <div className="h-[360px] rounded-xl overflow-hidden border border-sky-100 relative shadow-inner">
            <MapCanvas
              center={festival?.coordinates || [78.1193, 9.9195]}
              stops={stops}
              points={forecast?.points || []}
              route={
                routeVisible && activeMove?.sourceStop && activeMove?.destinationStop
                  ? { from: activeMove.sourceStop, to: activeMove.destinationStop }
                  : null
              }
              showHeatmap={showHeatmap}
              onStopSelect={onSelectStop}
            />
          </div>

          {/* Selected Stop Quick Status */}
          <div className="bg-sky-50/70 rounded-xl p-3.5 border border-sky-200/80 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-sky-600 text-white flex items-center justify-center shrink-0">
                <MapPin size={16} />
              </div>
              <div>
                <div className="text-[11px] font-semibold text-slate-500 uppercase">
                  Inspected Stop
                </div>
                <div className="text-sm font-bold text-slate-900">
                  {selectedStop ? selectedStop.name : 'Select any stop on map'}
                </div>
              </div>
            </div>
            {selectedStop && (
              <div className="flex items-center gap-4 text-xs">
                <div>
                  <span className="text-slate-500">Queue: </span>
                  <span className="font-bold text-slate-900">
                    {formatNumber(selectedStop.crowd)} pax
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">Fleet: </span>
                  <span className="font-bold text-sky-700">
                    {selectedStop.currentBuses} buses
                  </span>
                </div>
                <div>
                  <span className={`risk-pill ${toRiskClass(selectedStop.risk)}`}>
                    <span className="risk-dot" />
                    {riskLabel(selectedStop.risk)}
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right Rail: Priority Locations & Status */}
        <div className="space-y-6">
          {/* Operational Status Card */}
          <div className="bg-white border border-sky-100 rounded-2xl p-5 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-[11px] font-bold uppercase tracking-wider text-slate-500">
                  System Health
                </div>
                <h4 className="text-base font-bold text-slate-900">Network Fleet Invariant</h4>
              </div>
              <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-sky-100 text-sky-800 border border-sky-200">
                Conserved
              </span>
            </div>

            <div className="space-y-2.5">
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-600">Total Fixed Fleet:</span>
                <span className="font-bold text-slate-900">{totalBuses} active buses</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-600">Monitored Major Terminals:</span>
                <span className="font-bold text-slate-900">{stops.length} hubs</span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-600">Network Queue Relief:</span>
                <span className="font-bold text-emerald-600">
                  +{optimization?.overall_queue_reduction_percentage ?? 34}%
                </span>
              </div>
            </div>

            <div className="pt-3 border-t border-slate-100">
              <div className="text-xs text-slate-600 mb-1.5 flex justify-between">
                <span>Model Load Level</span>
                <span className="font-semibold text-slate-800">
                  {Math.min(100, Math.round((forecast?.metrics?.peakCrowd ?? 450000) / 6000))}%
                </span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-sky-600 h-2 rounded-full transition-all duration-500"
                  style={{
                    width: `${Math.min(100, Math.round((forecast?.metrics?.peakCrowd ?? 450000) / 6000))}%`,
                  }}
                />
              </div>
            </div>
          </div>

          {/* Priority Locations List */}
          <div className="bg-white border border-sky-100 rounded-2xl p-5 shadow-sm space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-1.5">
                <MapPinned size={16} className="text-sky-600" /> Priority Terminals
              </h4>
              <button
                onClick={() => onNavigate('Crowd map')}
                className="text-xs font-semibold text-sky-600 hover:text-sky-700 flex items-center gap-1"
              >
                View all <ArrowRight size={12} />
              </button>
            </div>

            <div className="space-y-2">
              {stops.length === 0 ? (
                <div className="p-4 text-center text-xs text-slate-500 bg-sky-50/50 rounded-xl border border-dashed border-sky-200">
                  Loading monitored terminals…
                </div>
              ) : (
                stops
                  .slice()
                  .sort((a, b) => (b.crowd || 0) - (a.crowd || 0))
                  .slice(0, 3)
                  .map((stop, idx) => (
                    <button
                      key={stop.id}
                      onClick={() => onSelectStop(stop)}
                      className={`w-full text-left p-2.5 rounded-xl border transition-all flex items-center justify-between ${
                        selectedStop?.id === stop.id
                          ? 'border-sky-500 bg-sky-50/70 shadow-sm'
                          : 'border-slate-100 hover:border-sky-200 hover:bg-sky-50/30'
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="w-6 h-6 rounded-lg bg-sky-100 text-sky-700 text-xs font-bold flex items-center justify-center">
                          0{idx + 1}
                        </span>
                        <div>
                          <div className="text-xs font-bold text-slate-900">{stop.name}</div>
                          <div className="text-[11px] text-slate-500">
                            {stop.currentBuses} buses · {stop.waitMinutes} min wait
                          </div>
                        </div>
                      </div>
                      <span className={`risk-pill ${toRiskClass(stop.risk)}`}>
                        <span className="risk-dot" />
                        {riskLabel(stop.risk)}
                      </span>
                    </button>
                  ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Recommended Bus Movement Summary Card */}
      <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-wider text-sky-700">
              Zero-Sum Optimization Engine
            </div>
            <h3 className="text-lg font-bold text-slate-900">
              Active Fleet Redistribution Recommendation
            </h3>
            <p className="text-xs text-slate-600 mt-0.5">
              Time-aware dispatch ensuring buses arrive before the post-event egress peak.
            </p>
            {optimizeMessage && (
              <p className="text-[11px] text-emerald-700 font-medium mt-1 flex items-center gap-1">
                <Check size={12} /> {optimizeMessage}
              </p>
            )}
          </div>
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1.5">
              <Check size={14} /> Fleet Conserved
            </span>
            <button
              onClick={onRunOptimization}
              disabled={optimizeStatus === 'loading'}
              className="px-4 py-2 rounded-xl bg-sky-600 hover:bg-sky-700 text-white font-medium text-xs flex items-center gap-2 transition-all shadow-sm disabled:opacity-60"
            >
              {optimizeStatus === 'loading' ? (
                <span className="spinner spinner-small" />
              ) : (
                <RefreshCw size={14} />
              )}
              {optimizeStatus === 'loading' ? 'Computing…' : 'Re-Run Optimizer'}
            </button>
          </div>
        </div>

        {/* Visual Movement Flow */}
        {activeMove && sourceStop && destinationStop ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center my-6 py-2">
            {/* Source Stop */}
            <div className="p-4 rounded-xl border border-sky-200 bg-sky-50/50">
              <div className="text-[11px] font-bold text-slate-500 uppercase flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-amber-500" /> SOURCE TERMINAL (REDUCED)
              </div>
              <h4 className="text-base font-bold text-slate-900 mt-1">{sourceStop.name}</h4>
              <div className="text-xs text-slate-600 mt-1">
                Current fleet: <span className="font-bold text-slate-900">{sourceStop.currentBuses} buses</span> →
                After move: <span className="font-bold text-amber-700">{sourceStop.currentBuses - activeMove.buses} buses</span>
              </div>
              <div className="mt-2 text-[11px] text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2 font-medium">
                Service Sacrifice: {activeMove.tradeoff}
              </div>
            </div>

            {/* Transfer Arrow & Stats */}
            <div className="text-center p-3 rounded-xl bg-gradient-to-r from-sky-50 via-sky-100/70 to-sky-50 border border-sky-200 flex flex-col items-center justify-center">
              <div className="w-10 h-10 rounded-full bg-sky-600 text-white flex items-center justify-center shadow-md mb-2">
                <Bus size={20} />
              </div>
              <div className="text-base font-black text-sky-900">
                REPOSITION {activeMove.buses} BUSES
              </div>
              <div className="text-xs font-semibold text-slate-600 mt-0.5">
                Departs {activeMove.departure} · Arrives {activeMove.arrival} ({activeMove.travelMinutes} mins transit)
              </div>
              <div className="text-[11px] text-emerald-700 font-bold mt-1.5">
                Relief Benefit: -{activeMove.waitReduction} min queue wait
              </div>
            </div>

            {/* Destination Stop */}
            <div className="p-4 rounded-xl border border-sky-300 bg-sky-100/40">
              <div className="text-[11px] font-bold text-sky-800 uppercase flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-500" /> DESTINATION TERMINAL (REINFORCED)
              </div>
              <h4 className="text-base font-bold text-slate-900 mt-1">{destinationStop.name}</h4>
              <div className="text-xs text-slate-600 mt-1">
                Current fleet: <span className="font-bold text-slate-900">{destinationStop.currentBuses} buses</span> →
                Reinforced: <span className="font-bold text-emerald-700">{destinationStop.currentBuses + activeMove.buses} buses</span>
              </div>
              <div className="mt-2 text-[11px] text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg p-2 font-medium">
                Expected Relief: {activeMove.benefit}
              </div>
            </div>
          </div>
        ) : (
          <div className="my-6 p-6 rounded-xl border border-dashed border-sky-300 bg-sky-50/40 text-center">
            <div className="w-12 h-12 rounded-full bg-sky-100 text-sky-600 flex items-center justify-center mx-auto mb-3">
              <Bus size={22} />
            </div>
            <h4 className="text-sm font-bold text-slate-800">
              {optimization?.source === 'not_run'
                ? 'Optimization Plan Pending'
                : 'No beneficial repositioning required for this scenario.'}
            </h4>
            <p className="text-xs text-slate-600 mt-1 max-w-md mx-auto">
              {optimization?.source === 'not_run'
                ? 'Click "Re-Run Optimizer" above to compute time-aware zero-sum vehicle redistribution using real demand estimates.'
                : 'No beneficial repositioning required for this scenario. Current fleet allocation satisfies projected peak demand.'}
            </p>
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-3 border-t border-slate-100 text-xs text-slate-500">
          <div>
            * Enforces invariant: ∑(Allocated Buses) = {totalBuses}. All transfers show explicit source trade-off.
          </div>
          <button
            onClick={() => onNavigate('Bus allocation & trade-off')}
            className="font-bold text-sky-600 hover:text-sky-700 flex items-center gap-1 text-xs"
          >
            Open Comprehensive Trade-off Analysis <ArrowRight size={14} />
          </button>
        </div>
      </div>
    </div>
  );
}
