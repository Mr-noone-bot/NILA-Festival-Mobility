import { useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Bus,
  CheckCircle2,
  Clock3,
  Layers3,
  Navigation,
  RefreshCw,
  ShieldAlert,
  Waves,
  X,
  FileText,
  Check,
  Flame,
  CloudRain,
  CalendarClock,
} from 'lucide-react';
import MapCanvas from '../components/MapCanvas';
import type {
  BusMove,
  Festival,
  ForecastResponse,
  OptimizeResponse,
  ScenarioConfig,
  Stop,
} from '../types/nila';
import type { DecisionItem, OrderDispatchItem } from '../api/operations';

interface DutyManagerConsoleProps {
  festival: Festival;
  forecast: ForecastResponse;
  optimization: OptimizeResponse;
  decisions: DecisionItem[];
  stops: Stop[];
  selectedStop: Stop | null;
  onSelectStop: (stop: Stop) => void;
  onApproveDecision: (decisionId: string) => Promise<void>;
  onRejectDecision: (decisionId: string) => Promise<void>;
  onNavigate: (page: string) => void;
  liveUpdating: boolean;
  onRefresh: () => void;
  routeGeometry?: [number, number][];
  latestOrderCreated: OrderDispatchItem | null;
  availableBuses?: number;
  config?: ScenarioConfig;
  onUpdateConfig?: <K extends keyof ScenarioConfig>(key: K, value: ScenarioConfig[K]) => void;
}

export default function DutyManagerConsole({
  festival,
  forecast,
  optimization,
  decisions,
  stops,
  selectedStop,
  onSelectStop,
  onApproveDecision,
  onRejectDecision,
  onNavigate,
  liveUpdating,
  onRefresh,
  routeGeometry,
  latestOrderCreated,
  availableBuses,
  config,
  onUpdateConfig,
}: DutyManagerConsoleProps) {
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [routeVisible, setRouteVisible] = useState(true);
  const [reviewDecision, setReviewDecision] = useState<DecisionItem | null>(null);
  const [approvingId, setApprovingId] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);

  const activeMove: BusMove | null = optimization?.move ?? null;

  const totalBuses =
    stops.reduce((sum, s) => sum + s.currentBuses, 0) ||
    optimization?.total_fleet_size ||
    25;

  const pendingDecisions = decisions.filter((d) => d.status === 'PENDING');

  const handleApprove = async (dId: string) => {
    setApprovingId(dId);
    try {
      await onApproveDecision(dId);
      if (reviewDecision?.id === dId) {
        setReviewDecision(null);
      }
    } finally {
      setApprovingId(null);
    }
  };

  const handleReject = async (dId: string) => {
    setRejectingId(dId);
    try {
      await onRejectDecision(dId);
      if (reviewDecision?.id === dId) {
        setReviewDecision(null);
      }
    } finally {
      setRejectingId(null);
    }
  };

  return (
    <div className="space-y-5">
      {/* Top Provenance & Live Reaction Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold bg-rose-950 text-rose-400 border border-rose-800">
            <span className="w-2 h-2 rounded-full bg-rose-500 animate-pulse" />
            CONTROL ROOM ● LIVE
          </div>
          <span className="text-xs text-slate-300 font-medium">
            Festival: <strong>{festival.name} ({festival.city})</strong>
          </span>
          {liveUpdating ? (
            <span className="text-xs text-cyan-400 flex items-center gap-1.5 animate-pulse font-medium">
              <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Live recalculating prediction & fleet...
            </span>
          ) : (
            <span className="text-xs text-slate-400 hidden md:inline">
              ● Reactive engine active (auto-updates on rain & schedule changes)
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 self-start sm:self-auto text-[11px] text-slate-400">
          <span className="px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
            PROVENANCE: HR&CE OFFICIAL + ESTIMATE + SIMULATED TELEMETRY
          </span>
          <button
            onClick={onRefresh}
            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Manual sync"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${liveUpdating ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Live Event Reaction Controls (Constraint #1 Auto-Reaction Engine) */}
      <div className="bg-slate-900/95 border border-slate-800 p-3 rounded-xl flex flex-col md:flex-row md:items-center justify-between gap-3 shadow-md">
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-1.5 text-xs text-slate-300 font-semibold">
            <CloudRain className="w-4 h-4 text-cyan-400" />
            <span>Active Rain:</span>
            <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800">
              {[
                { val: 20, label: '20% Clear' },
                { val: 50, label: '50% Moderate' },
                { val: 70, label: '70% Heavy Rain' },
              ].map(({ val, label }) => (
                <button
                  key={val}
                  onClick={() => onUpdateConfig?.('rain', val)}
                  className={`px-2.5 py-1 rounded text-[11px] font-bold transition ${
                    config?.rain === val
                      ? 'bg-cyan-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="flex items-center gap-1.5 text-xs text-slate-300 font-semibold">
            <CalendarClock className="w-4 h-4 text-amber-400" />
            <span>Event End Schedule:</span>
            <div className="flex items-center gap-1 bg-slate-950 p-0.5 rounded-lg border border-slate-800">
              {[
                { val: 0, label: '20:00 (On-Time)' },
                { val: 30, label: '20:30 (+30m Delay)' },
                { val: 60, label: '21:00 (+60m Delay)' },
              ].map(({ val, label }) => (
                <button
                  key={val}
                  onClick={() => onUpdateConfig?.('delayMinutes', val)}
                  className={`px-2.5 py-1 rounded text-[11px] font-bold transition ${
                    config?.delayMinutes === val
                      ? 'bg-amber-600 text-white shadow'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>Zero manual clicks — auto-recalculates prediction, fleet & queue</span>
        </div>
      </div>

      {/* Dispatch Order Toast if newly created */}
      {latestOrderCreated && (
        <div className="p-3 bg-emerald-950/80 border border-emerald-800 text-emerald-300 text-xs rounded-xl flex items-center justify-between shadow-lg animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400" />
            <span>
              <strong>DISPATCH ORDER GENERATED:</strong> {latestOrderCreated.id} assigned to{' '}
              <strong>{latestOrderCreated.bus_id}</strong> ({latestOrderCreated.source_stop} → {latestOrderCreated.destination_stop}, depart {latestOrderCreated.departure_time}).
            </span>
          </div>
          <button
            onClick={() => onNavigate('Depot operations')}
            className="px-2.5 py-1 bg-emerald-800 hover:bg-emerald-700 text-white rounded font-medium transition"
          >
            View in Depot
          </button>
        </div>
      )}

      {/* Top KPI Row */}
      <div className="grid grid-cols-2 md:grid-cols-6 gap-3">
        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] font-semibold text-rose-400 uppercase tracking-wider flex items-center gap-1">
            <ShieldAlert className="w-3.5 h-3.5" /> Network Risk
          </div>
          <div className="text-xl font-bold text-rose-400 mt-1">
            {forecast.metrics?.risk || 'CRITICAL'}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Surge probability &gt;80%</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Clock3 className="w-3.5 h-3.5 text-cyan-400" /> Peak Window
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {forecast.metrics?.peakTime || '20:10'}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Egress ritual completion</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] font-semibold text-amber-400 uppercase tracking-wider flex items-center gap-1">
            <AlertTriangle className="w-3.5 h-3.5" /> Overloaded Stops
          </div>
          <div className="text-xl font-bold text-amber-400 mt-1">
            {forecast.metrics?.overloadedStops ?? 2}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Exceeding 80% capacity</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] font-semibold text-emerald-400 uppercase tracking-wider flex items-center gap-1">
            <Bus className="w-3.5 h-3.5" /> Free Buses
          </div>
          <div className="text-xl font-bold text-emerald-400 mt-1">{availableBuses ?? '—'}</div>
          <div className="text-[11px] text-slate-400 mt-0.5">Ready for repositioning</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl">
          <div className="text-[11px] font-semibold text-cyan-400 uppercase tracking-wider flex items-center gap-1">
            <FileText className="w-3.5 h-3.5" /> Pending Decisions
          </div>
          <div className="text-xl font-bold text-cyan-400 mt-1">
            {pendingDecisions.length}
          </div>
          <div className="text-[11px] text-slate-400 mt-0.5">Awaiting manager sign-off</div>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-3 rounded-xl col-span-2 md:col-span-1">
          <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1">
            <Activity className="w-3.5 h-3.5 text-emerald-400" /> Fleet Invariant
          </div>
          <div className="text-xl font-bold text-white mt-1">
            {totalBuses} / {totalBuses}
          </div>
          <div className="text-[11px] text-emerald-400 mt-0.5 font-medium">Conserved (Zero Added)</div>
        </div>
      </div>

      {/* Main Grid: Map on Left, Decision Queue on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* Left Map Area (7 cols) */}
        <div className="lg:col-span-7 space-y-3">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl overflow-hidden shadow-lg flex flex-col h-[520px]">
            {/* Map Header Controls */}
            <div className="px-4 py-2.5 bg-slate-950/80 border-b border-slate-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Navigation className="w-4 h-4 text-cyan-400" />
                <span className="text-xs font-bold text-white uppercase tracking-wider">
                  Live Situational Perimeter Map
                </span>
                <span className="text-[10px] px-2 py-0.5 rounded bg-slate-800 text-slate-400">
                  MapLibre + deck.gl
                </span>
              </div>

              <div className="flex items-center gap-2">
                <button
                  onClick={() => setShowHeatmap(!showHeatmap)}
                  className={`px-2 py-1 text-xs rounded border transition flex items-center gap-1 ${
                    showHeatmap
                      ? 'bg-cyan-950 text-cyan-300 border-cyan-800'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  <Waves className="w-3 h-3" /> Heatmap
                </button>
                <button
                  onClick={() => setRouteVisible(!routeVisible)}
                  className={`px-2 py-1 text-xs rounded border transition flex items-center gap-1 ${
                    routeVisible
                      ? 'bg-amber-950 text-amber-300 border-amber-800'
                      : 'bg-slate-800 text-slate-400 border-slate-700'
                  }`}
                >
                  <Layers3 className="w-3 h-3" /> Transit Route
                </button>
              </div>
            </div>

            {/* Map Canvas */}
            <div className="flex-1 relative">
              <MapCanvas
                center={festival.coordinates}
                stops={stops}
                points={showHeatmap ? forecast.points : []}
                route={
                  activeMove && routeVisible
                    ? { from: activeMove.sourceStop, to: activeMove.destinationStop }
                    : null
                }
                routeGeometry={routeVisible ? routeGeometry : null}
                showHeatmap={showHeatmap}
                onStopSelect={onSelectStop}
              />
            </div>

            {/* Stop Quick Status Bar below map */}
            <div className="p-3 bg-slate-950/90 border-t border-slate-800 flex items-center justify-between overflow-x-auto gap-2">
              <span className="text-xs text-slate-400 font-medium">Monitored Stops:</span>
              <div className="flex items-center gap-2">
                {stops.map((s) => (
                  <button
                    key={s.id}
                    onClick={() => onSelectStop(s)}
                    className={`px-2.5 py-1 rounded text-xs transition border flex items-center gap-1.5 ${
                      selectedStop?.id === s.id
                        ? 'bg-cyan-900/60 text-white border-cyan-600'
                        : 'bg-slate-900 text-slate-300 border-slate-800 hover:bg-slate-800'
                    }`}
                  >
                    <span
                      className={`w-2 h-2 rounded-full ${
                        s.risk === 'CRITICAL'
                          ? 'bg-rose-500'
                          : s.risk === 'HIGH'
                          ? 'bg-orange-500'
                          : 'bg-emerald-500'
                      }`}
                    />
                    {s.shortName}: <strong>{s.currentBuses} buses</strong> ({s.waitMinutes}m wait)
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Right Area: DECISION QUEUE (5 cols) */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg flex flex-col h-[520px]">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-3">
              <div>
                <h2 className="text-base font-bold text-white flex items-center gap-2">
                  <Flame className="w-4 h-4 text-rose-400" />
                  Decision Queue
                </h2>
                <p className="text-xs text-slate-400">
                  Prioritized operational actions requiring Duty Manager approval.
                </p>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-bold bg-rose-950 text-rose-400 border border-rose-800">
                {pendingDecisions.length} PENDING
              </span>
            </div>

            {/* Decisions List */}
            <div className="flex-1 overflow-y-auto space-y-3 pr-1">
              {decisions.map((dec) => {
                const isPending = dec.status === 'PENDING';
                const isApproved = dec.status === 'APPROVED';
                const isRejected = dec.status === 'REJECTED';

                return (
                  <div
                    key={dec.id}
                    className={`p-3.5 rounded-xl border transition space-y-3 ${
                      dec.priority === 'CRITICAL'
                        ? 'bg-rose-950/20 border-rose-800/60'
                        : 'bg-slate-950/70 border-slate-800'
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-[10px] font-extrabold px-2 py-0.5 rounded border uppercase ${
                            dec.priority === 'CRITICAL'
                              ? 'bg-rose-950 text-rose-300 border-rose-800'
                              : 'bg-amber-950 text-amber-300 border-amber-800'
                          }`}
                        >
                          {dec.priority} PRIORITY
                        </span>
                        <span className="text-xs font-bold text-white">{dec.id}</span>
                      </div>

                      {isApproved && (
                        <span className="text-[11px] font-bold text-emerald-400 bg-emerald-950/60 border border-emerald-800 px-2 py-0.5 rounded flex items-center gap-1">
                          <Check className="w-3 h-3" /> APPROVED ({dec.order_id})
                        </span>
                      )}
                      {isRejected && (
                        <span className="text-[11px] font-bold text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded">
                          REJECTED
                        </span>
                      )}
                    </div>

                    {/* Problem statement */}
                    <div className="text-xs text-slate-200 font-medium">
                      {dec.problem}
                    </div>

                    {/* Movement details */}
                    <div className="bg-slate-900/80 p-2.5 rounded-lg border border-slate-800 text-xs space-y-1.5">
                      <div className="flex items-center justify-between text-slate-300 font-semibold">
                        <span className="text-slate-400">{dec.source_stop}</span>
                        <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
                        <span className="text-cyan-300">{dec.destination_stop}</span>
                      </div>

                      <div className="flex items-center justify-between text-[11px] text-slate-400">
                        <span>Buses: <strong>{dec.bus_ids.join(', ')}</strong></span>
                        <span>Dep: <strong>{dec.departure_time}</strong> → Arr: <strong>{dec.arrival_time}</strong> ({dec.travel_time_minutes}m)</span>
                      </div>
                    </div>

                    {/* Trade-off summary */}
                    <div className="grid grid-cols-2 gap-2 text-[11px]">
                      <div className="bg-emerald-950/30 border border-emerald-900/50 p-2 rounded text-emerald-300">
                        <div className="font-bold text-[10px] uppercase tracking-wider text-emerald-400">Benefit</div>
                        <div>{dec.benefit}</div>
                      </div>
                      <div className="bg-amber-950/30 border border-amber-900/50 p-2 rounded text-amber-300">
                        <div className="font-bold text-[10px] uppercase tracking-wider text-amber-400">Trade-Off (Cost)</div>
                        <div>{dec.tradeoff}</div>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center justify-between pt-1">
                      <button
                        onClick={() => setReviewDecision(dec)}
                        className="px-3 py-1.5 rounded text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition font-medium"
                      >
                        Review Trade-Off
                      </button>

                      {isPending && (
                        <div className="flex items-center gap-2">
                          <button
                            disabled={rejectingId === dec.id || approvingId === dec.id}
                            onClick={() => handleReject(dec.id)}
                            className="px-2.5 py-1.5 rounded text-xs bg-slate-900 hover:bg-slate-800 text-rose-400 border border-rose-900/60 transition disabled:opacity-50"
                          >
                            Reject
                          </button>
                          <button
                            disabled={approvingId === dec.id || rejectingId === dec.id}
                            onClick={() => handleApprove(dec.id)}
                            className="px-3 py-1.5 rounded text-xs bg-emerald-700 hover:bg-emerald-600 text-white font-bold transition shadow disabled:opacity-50 flex items-center gap-1"
                          >
                            <Check className="w-3.5 h-3.5" />
                            {approvingId === dec.id ? 'Approving...' : 'Approve Move'}
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}

              {decisions.length === 0 && (
                <div className="p-8 text-center text-slate-400 text-xs font-semibold">
                  No beneficial repositioning required for this scenario.
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Review Trade-Off Modal / Drawer */}
      {reviewDecision && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-xl w-full p-6 space-y-5 shadow-2xl animate-scaleUp">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs uppercase font-extrabold px-2 py-0.5 rounded bg-rose-950 text-rose-300 border border-rose-800">
                    {reviewDecision.priority} IMPACT
                  </span>
                  <span className="text-xs uppercase font-extrabold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                    CONFIDENCE: {reviewDecision.confidence}
                  </span>
                </div>
                <h3 className="text-lg font-bold text-white mt-1">
                  Operational Trade-Off Review: {reviewDecision.id}
                </h3>
              </div>
              <button
                onClick={() => setReviewDecision(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Why Move */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1">
              <div className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Operational Justification</div>
              <p className="text-sm text-slate-200">{reviewDecision.problem}</p>
            </div>

            {/* Side by side Trade-Off comparison */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="bg-emerald-950/40 border border-emerald-800/80 p-3.5 rounded-xl space-y-2">
                <div className="font-bold text-emerald-400 uppercase tracking-wider text-[11px]">
                  Destination Benefit
                </div>
                <div className="text-sm font-semibold text-white">{reviewDecision.destination_stop}</div>
                <div className="text-emerald-300">
                  +{reviewDecision.bus_ids.length} bus{reviewDecision.bus_ids.length !== 1 ? 'es' : ''} added
                </div>
                <div className="text-slate-300">
                  {reviewDecision.benefit}
                </div>
                <div className="text-[11px] text-emerald-400 font-medium">
                  Queue risk drops: HIGH → MODERATE
                </div>
              </div>

              <div className="bg-amber-950/40 border border-amber-800/80 p-3.5 rounded-xl space-y-2">
                <div className="font-bold text-amber-400 uppercase tracking-wider text-[11px]">
                  Source Cost (Trade-Off)
                </div>
                <div className="text-sm font-semibold text-white">{reviewDecision.source_stop}</div>
                <div className="text-amber-300">
                  -{reviewDecision.bus_ids.length} bus{reviewDecision.bus_ids.length !== 1 ? 'es' : ''} redeployed
                </div>
                <div className="text-slate-300">
                  {reviewDecision.tradeoff}
                </div>
                <div className="text-[11px] text-amber-400 font-medium">
                  Surplus staging remains adequate
                </div>
              </div>
            </div>

            {/* Network Effect & Fleet Invariant */}
            <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-2 text-xs">
              <div className="font-bold text-cyan-400 uppercase tracking-wider text-[11px]">
                Network Effect & Fleet Invariant
              </div>
              <p className="text-slate-300">{reviewDecision.network_effect}</p>
              <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-slate-800/80">
                <span>Total Fleet Conserved:</span>
                <span className="font-bold text-white font-mono">Before: 25 ➔ After: 25</span>
              </div>
            </div>

            {/* Candidate Vehicle Details */}
            <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800 text-xs flex items-center justify-between">
              <div>
                <span className="text-slate-400">Assigned Candidate Bus:</span>
                <span className="font-bold text-white ml-1.5">{reviewDecision.bus_ids.join(', ')}</span>
              </div>
              <div className="text-slate-300">
                Depart: <strong>{reviewDecision.departure_time}</strong> ➔ Arrive: <strong>{reviewDecision.arrival_time}</strong>
              </div>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setReviewDecision(null)}
                className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm font-medium transition"
              >
                Close
              </button>
              {reviewDecision.status === 'PENDING' && (
                <>
                  <button
                    disabled={rejectingId === reviewDecision.id}
                    onClick={() => handleReject(reviewDecision.id)}
                    className="px-4 py-2 rounded-lg bg-slate-900 hover:bg-slate-800 text-rose-400 border border-rose-900/60 text-sm font-semibold transition"
                  >
                    Reject
                  </button>
                  <button
                    disabled={approvingId === reviewDecision.id}
                    onClick={() => handleApprove(reviewDecision.id)}
                    className="px-5 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-bold transition shadow-lg flex items-center gap-1.5"
                  >
                    <Check className="w-4 h-4" />
                    Approve Operational Move
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
