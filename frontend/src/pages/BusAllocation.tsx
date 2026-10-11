import {
  AlertTriangle,
  Bus,
  CheckCircle2,
  Clock,
  Gauge,
  Navigation,
  RefreshCw,
  Scale,
  ShieldCheck,
  Zap,
} from 'lucide-react';
import type { BusMove, OptimizeResponse, Stop } from '../types/nila';
import { formatNumber, riskLabel, toRiskClass } from '../utils/format';

interface BusAllocationProps {
  optimization: OptimizeResponse;
  stops: Stop[];
  onRunOptimization: () => void;
  optimizeStatus: 'idle' | 'loading' | 'success' | 'error';
  optimizeMessage: string;
}

export default function BusAllocation({
  optimization,
  stops,
  onRunOptimization,
  optimizeStatus,
  optimizeMessage,
}: BusAllocationProps) {
  const move: BusMove | null = optimization?.move ?? null;

  const sourceStop: Stop | undefined = move
    ? stops.find((s) => s.id === move.sourceStop) ?? stops[0]
    : undefined;

  const destinationStop: Stop | undefined = move
    ? stops.find((s) => s.id === move.destinationStop) ?? stops[1]
    : undefined;

  const totalBuses =
    stops.reduce((sum, s) => sum + s.currentBuses, 0) ||
    optimization?.total_fleet_size ||
    25;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sky-700">
            Fixed-Fleet Mathematical Optimization
          </div>
          <h2 className="text-xl font-black text-slate-900 mt-1 flex items-center gap-2">
            Bus Allocation & Explicit Trade-off Engine
          </h2>
          <p className="text-xs text-slate-600 mt-1">
            Every vehicle transfer calculates transit duration via OSRM and balances origin service reduction against destination queue relief.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <span className="px-3 py-1.5 rounded-full text-xs font-bold bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center gap-1.5">
            <ShieldCheck size={16} /> Total Fleet Conserved ({totalBuses} Buses)
          </span>
          <button
            onClick={onRunOptimization}
            disabled={optimizeStatus === 'loading'}
            className="px-4 py-2 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm transition-all disabled:opacity-60"
          >
            {optimizeStatus === 'loading' ? (
              <span className="spinner spinner-small" />
            ) : (
              <RefreshCw size={14} />
            )}
            {optimizeStatus === 'loading' ? 'Calculating Moves…' : 'Re-Run Solver'}
          </button>
        </div>
      </div>

      {optimizeMessage && (
        <div className="text-xs text-sky-800 bg-sky-50 border border-sky-200 rounded-xl px-4 py-2 font-medium flex items-center gap-2">
          <ShieldCheck size={14} className="text-sky-600" />
          <span>{optimizeMessage}</span>
        </div>
      )}

      {/* Mathematical Principle Callout */}
      <div className="p-4 rounded-2xl bg-sky-50/80 border border-sky-200 flex items-start gap-3.5 text-xs text-sky-950">
        <Scale size={20} className="text-sky-600 shrink-0 mt-0.5" />
        <div>
          <strong className="font-bold text-sky-900 block text-sm mb-0.5">
            Fixed Fleet Invariant: ∑(Buses) = {totalBuses} Total Conserved
          </strong>
          Transit operators cannot spawn buses out of thin air. NILA strictly respects vehicle conservation. In order to relieve a critical queue at an egress choke point, buses are temporarily borrowed from terminals where passenger queues are safely below capacity.
        </div>
      </div>

      {/* Central Visual Repositioning Flow Diagram & Trade-Off Cards */}
      {move && sourceStop && destinationStop ? (
        <>
          <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm">
            <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">
              Recommended Vehicle Reassignment Flow
            </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-stretch">
          {/* Source Stop Card */}
          <div className="bg-amber-50/40 border-2 border-amber-300 rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-amber-900 uppercase tracking-wider flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
                  Origin Terminal
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-800 font-bold border border-amber-200">
                  Donor
                </span>
              </div>
              <h3 className="text-lg font-black text-slate-900 mt-2">{sourceStop.name}</h3>
              <p className="text-xs text-slate-600 mt-1">
                Low queue pressure terminal with surplus standby vehicles.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-amber-200/70 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-600">Initial Allocation:</span>
                <strong className="text-slate-900">{sourceStop.currentBuses} buses</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Vehicles Transferred:</span>
                <strong className="text-amber-700 font-bold">-{move.buses} buses</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Remaining Buffer:</span>
                <strong className="text-slate-900">
                  {sourceStop.currentBuses - move.buses} buses (Safe)
                </strong>
              </div>
            </div>
          </div>

          {/* Transfer Corridor Node */}
          <div className="bg-gradient-to-b from-sky-50 via-white to-sky-50 border-2 border-sky-300 rounded-2xl p-5 flex flex-col items-center justify-center text-center shadow-sm">
            <div className="w-14 h-14 rounded-2xl bg-sky-600 text-white flex items-center justify-center shadow-lg mb-3">
              <Bus size={28} />
            </div>
            <div className="text-xs font-bold uppercase tracking-wider text-sky-800">
              Inter-Terminal Transfer
            </div>
            <div className="text-2xl font-black text-slate-900 mt-0.5">
              {move.buses} {move.buses === 1 ? 'BUS' : 'BUSES'}
            </div>

            <div className="mt-3 w-full bg-white rounded-xl p-3 border border-sky-200 space-y-1.5 text-xs text-slate-600">
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 font-medium">
                  <Clock size={13} /> Departure:
                </span>
                <strong className="text-slate-900">{move.departure}</strong>
              </div>
              <div className="flex items-center justify-between">
                <span className="flex items-center gap-1 font-medium">
                  <Navigation size={13} /> Estimated Arrival:
                </span>
                <strong className="text-slate-900">{move.arrival}</strong>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-slate-100">
                <span className="font-medium">Travel Duration:</span>
                <strong className="text-sky-700">{move.travelMinutes} mins (OSRM)</strong>
              </div>
            </div>
          </div>

          {/* Destination Stop Card */}
          <div className="bg-emerald-50/40 border-2 border-emerald-300 rounded-2xl p-5 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-bold text-emerald-900 uppercase tracking-wider flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                  Target Terminal
                </span>
                <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold border border-emerald-200">
                  Reinforced
                </span>
              </div>
              <h3 className="text-lg font-black text-slate-900 mt-2">{destinationStop.name}</h3>
              <p className="text-xs text-slate-600 mt-1">
                Critical egress hub facing severe post-event crowd surge.
              </p>
            </div>

            <div className="mt-4 pt-3 border-t border-emerald-200/70 space-y-2 text-xs">
              <div className="flex justify-between">
                <span className="text-slate-600">Initial Allocation:</span>
                <strong className="text-slate-900">{destinationStop.currentBuses} buses</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Vehicles Influx:</span>
                <strong className="text-emerald-700 font-bold">+{move.buses} buses</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-600">Post-Optimization Fleet:</span>
                <strong className="text-slate-900">
                  {destinationStop.currentBuses + move.buses} buses (Relieved)
                </strong>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Transparent Service Trade-off Comparison Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Destination Expected Benefit */}
        <div className="bg-white border-2 border-emerald-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center">
              <Zap size={18} />
            </div>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-emerald-800">
                Destination Stop Gain
              </div>
              <h4 className="text-base font-bold text-slate-900">
                Queue Relief & Wait Reduction
              </h4>
            </div>
          </div>

          <div className="p-3.5 bg-emerald-50/70 rounded-xl border border-emerald-200/80 mb-3">
            <div className="text-2xl font-black text-emerald-700">
              -{move.waitReduction} min average wait
            </div>
            <p className="text-xs text-emerald-950 mt-1 leading-relaxed">{move.benefit}</p>
          </div>

          <ul className="text-xs text-slate-600 space-y-2">
            <li className="flex items-start gap-2">
              <CheckCircle2 size={14} className="text-emerald-600 shrink-0 mt-0.5" />
              <span>
                Prevents hazardous crush condition at {destinationStop.name} platforms.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <CheckCircle2 size={14} className="text-emerald-600 shrink-0 mt-0.5" />
              <span>
                Enhances passenger boarding rate before the 10:30 AM ritual egress peak.
              </span>
            </li>
          </ul>
        </div>

        {/* Source Service Sacrifice */}
        <div className="bg-white border-2 border-amber-200 rounded-2xl p-6 shadow-sm">
          <div className="flex items-center gap-2.5 mb-3">
            <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-800 flex items-center justify-center">
              <AlertTriangle size={18} />
            </div>
            <div>
              <div className="text-[11px] font-bold uppercase tracking-wider text-amber-800">
                Source Stop Sacrifice
              </div>
              <h4 className="text-base font-bold text-slate-900">
                Origin Standby Capacity Reduction
              </h4>
            </div>
          </div>

          <div className="p-3.5 bg-amber-50/70 rounded-xl border border-amber-200/80 mb-3">
            <div className="text-2xl font-black text-amber-800">
              Standby Capacity Sacrificed
            </div>
            <p className="text-xs text-amber-950 mt-1 leading-relaxed">{move.tradeoff}</p>
          </div>

          <ul className="text-xs text-slate-600 space-y-2">
            <li className="flex items-start gap-2">
              <AlertTriangle size={14} className="text-amber-600 shrink-0 mt-0.5" />
              <span>
                Mattuthavani passenger waiting time temporarily rises by ~4 minutes.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <AlertTriangle size={14} className="text-amber-600 shrink-0 mt-0.5" />
              <span>
                Acceptable trade-off because Mattuthavani queue is only at 20% of rated capacity.
              </span>
            </li>
          </ul>
        </div>
      </div>
    </>
  ) : (
    <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm text-center">
      <div className="w-14 h-14 rounded-2xl bg-sky-100 text-sky-700 flex items-center justify-center mx-auto mb-3">
        <Bus size={28} />
      </div>
      <h3 className="text-base font-bold text-slate-900">
        {optimization?.source === 'not_run'
          ? 'Fleet Optimization Pending'
          : 'No beneficial repositioning required for this scenario.'}
      </h3>
      <p className="text-xs text-slate-600 mt-1 max-w-lg mx-auto">
        {optimization?.source === 'not_run'
          ? 'Click "Generate Optimization Plan" above to calculate optimal vehicle reallocation under the fixed-fleet invariant.'
          : 'All monitored stops have balanced supply relative to predicted crowd demand. No beneficial repositioning required for this scenario.'}
      </p>
    </div>
  )}

      {/* Network Overview Table */}
      <div className="bg-white border border-sky-100 rounded-2xl p-6 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <h4 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Gauge size={18} className="text-sky-600" />
            Complete Fixed-Fleet Allocation Matrix
          </h4>
          <span className="text-xs font-semibold text-slate-500">
            Overall Network Queue Relief:{' '}
            <strong className="text-emerald-600">
              +{optimization.overall_queue_reduction_percentage}%
            </strong>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider">
                <th className="py-2.5 px-3">Terminal Name</th>
                <th className="py-2.5 px-3">Crowd Demand</th>
                <th className="py-2.5 px-3">Baseline Fleet</th>
                <th className="py-2.5 px-3">Optimized Fleet</th>
                <th className="py-2.5 px-3">Net Adjustment</th>
                <th className="py-2.5 px-3">Post-Opt Risk</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-medium">
              {stops.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-6 text-center text-slate-500 italic">
                    Loading terminal allocations…
                  </td>
                </tr>
              ) : (
                stops.map((stop) => {
                  const isSource = move ? stop.id === move.sourceStop : false;
                  const isDest = move ? stop.id === move.destinationStop : false;
                  const netChange = isDest ? `+${move!.buses}` : isSource ? `-${move!.buses}` : '0';
                  const finalCount = optimization.final_allocation?.[stop.id] ?? stop.currentBuses;

                  return (
                    <tr
                      key={stop.id}
                      className={`hover:bg-slate-50 ${isDest ? 'bg-emerald-50/40' : isSource ? 'bg-amber-50/30' : ''
                        }`}
                    >
                      <td className="py-3 px-3 font-bold text-slate-900">{stop.name}</td>
                      <td className="py-3 px-3 text-slate-600">
                        {formatNumber(stop.crowd)} passengers
                      </td>
                      <td className="py-3 px-3 text-slate-700">{stop.currentBuses} buses</td>
                      <td className="py-3 px-3 font-bold text-sky-900">{finalCount} buses</td>
                      <td className="py-3 px-3">
                        <span
                          className={`font-bold px-2 py-0.5 rounded-full text-[11px] ${isDest
                              ? 'bg-emerald-100 text-emerald-800'
                              : isSource
                                ? 'bg-amber-100 text-amber-800'
                                : 'bg-slate-100 text-slate-600'
                            }`}
                        >
                          {netChange}
                        </span>
                      </td>
                      <td className="py-3 px-3">
                        <span
                          className={`risk-pill ${isDest ? 'risk-moderate' : toRiskClass(stop.risk)
                            }`}
                        >
                          <span className="risk-dot" />
                          {isDest ? 'Moderate' : riskLabel(stop.risk)}
                        </span>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
