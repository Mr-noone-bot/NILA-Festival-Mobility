import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bus,
  Clock,
  CloudRain,
  SlidersHorizontal,
  Sparkles,
  Users,
  ShieldAlert,
} from 'lucide-react';
import type { ScenarioConfig, ScenarioResult } from '../types/nila';
import { formatNumber } from '../utils/format';

interface ScenarioSimulatorProps {
  config: ScenarioConfig;
  onUpdateConfig: <K extends keyof ScenarioConfig>(key: K, value: ScenarioConfig[K]) => void;
  scenario: ScenarioResult;
  onRunScenario: () => void;
  scenarioStatus: 'idle' | 'loading' | 'success' | 'error';
  scenarioMessage: string;
}

export default function ScenarioSimulator({
  config,
  onUpdateConfig,
  scenario,
  onRunScenario,
  scenarioStatus,
  scenarioMessage,
}: ScenarioSimulatorProps) {
  const isRun = scenario.source === 'api';
  const comparisonRows = [
    {
      label: 'Peak Crowd Inflow',
      baseline: isRun ? formatNumber(scenario.baseline.peakCrowd) : '135,000',
      scenarioVal: isRun ? formatNumber(scenario.scenario.peakCrowd) : `${formatNumber(Math.round(135000 * (config.attendance / 100)))}`,
      unit: 'devotees',
      delta:
        config.attendance !== 100
          ? `${config.attendance > 100 ? '+' : ''}${config.attendance - 100}%`
          : '0% (Nominal)',
      worse: config.attendance > 100,
    },
    {
      label: 'Surge Peak Window',
      baseline: isRun ? scenario.baseline.peakTime : '20:10',
      scenarioVal: isRun
        ? scenario.scenario.peakTime
        : config.delayMinutes > 0
        ? `20:${10 + config.delayMinutes}`
        : '20:10',
      unit: 'local time',
      delta: config.delayMinutes > 0 ? `+${config.delayMinutes}m delay` : 'On schedule',
      worse: config.delayMinutes > 0,
    },
    {
      label: 'Average Passenger Wait',
      baseline: isRun ? `${scenario.baseline.waitingMinutes} min` : '18 min',
      scenarioVal: isRun
        ? `${scenario.scenario.waitingMinutes} min`
        : `${Math.round(18 * (config.attendance / 100) + (config.rain > 50 ? 6 : 0))} min`,
      unit: 'queue duration',
      delta:
        config.rain > 50 || config.attendance > 100
          ? `+${Math.round((config.attendance - 100) * 0.2 + (config.rain > 50 ? 6 : 0))} min`
          : 'Normal',
      worse: config.rain > 50 || config.attendance > 100,
    },
    {
      label: 'Accumulated Stop Queues',
      baseline: isRun ? `${formatNumber(scenario.baseline.queue)} pax` : '2,400 pax',
      scenarioVal: isRun
        ? `${formatNumber(scenario.scenario.queue)} pax`
        : `${formatNumber(Math.round(2400 * (config.attendance / 100) + (config.rain * 15)))} pax`,
      unit: 'across choke points',
      delta:
        config.attendance > 100 || config.rain > 30
          ? `+${Math.round((config.attendance - 100) + (config.rain * 0.4))}% surge`
          : 'Stable',
      worse: config.attendance > 100 || config.rain > 30,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-white flex items-center gap-2">
              SANDBOX — WHAT IF?
            </h2>
            <span className="text-xs px-2.5 py-0.5 rounded-full font-bold bg-amber-950 text-amber-300 border border-amber-800">
              ISOLATED SANDBOX
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Simulate volatile weather conditions, attendance surges, and fleet breakdowns to observe model behavior.
            <strong className="text-amber-400 ml-1">Sandbox explorations do NOT modify live dispatch orders.</strong>
          </p>
        </div>

        <button
          onClick={onRunScenario}
          disabled={scenarioStatus === 'loading'}
          className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-lg transition-all disabled:opacity-60"
        >
          <Activity size={15} className={scenarioStatus === 'loading' ? 'animate-spin' : ''} />
          {scenarioStatus === 'loading' ? 'Simulating Dynamic Model…' : 'Run Sandbox Simulation'}
        </button>
      </div>

      {scenarioMessage && (
        <div className="text-xs text-cyan-300 bg-cyan-950/60 border border-cyan-800 rounded-xl px-4 py-2 font-medium flex items-center gap-2">
          <Sparkles size={14} className="text-cyan-400" />
          <span>{scenarioMessage}</span>
        </div>
      )}

      {/* Main Grid: Controls vs Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Interactive Controls */}
        <div className="lg:col-span-5 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200 flex items-center gap-2">
              <SlidersHorizontal size={16} className="text-cyan-400" />
              Sandbox Parameters
            </h3>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-slate-800 text-slate-300 border border-slate-700">
              Auto-Reactive
            </span>
          </div>

          {/* Attendance Multiplier */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-300 flex items-center gap-1.5">
                <Users size={14} className="text-cyan-400" /> Attendance Multiplier
              </span>
              <span className="font-black text-cyan-400 font-mono">{config.attendance}% expected turnout</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {([100, 120, 150] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('attendance', val)}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all border ${
                    config.attendance === val
                      ? 'bg-cyan-600 text-white border-cyan-500 shadow-sm'
                      : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  {val}% {val === 100 ? '(Baseline)' : val === 120 ? '(+20%)' : '(Surge +50%)'}
                </button>
              ))}
            </div>
          </div>

          {/* Rain Probability */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-300 flex items-center gap-1.5">
                <CloudRain size={14} className="text-cyan-400" /> Rain Probability
              </span>
              <span className="font-black text-cyan-400 font-mono">{config.rain}% precipitation</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {([0, 30, 60, 90] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('rain', val)}
                  className={`py-2 px-2 rounded-xl text-xs font-bold transition-all border ${
                    config.rain === val
                      ? 'bg-cyan-600 text-white border-cyan-500 shadow-sm'
                      : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  {val}%
                </button>
              ))}
            </div>
          </div>

          {/* Event Delay */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-300 flex items-center gap-1.5">
                <Clock size={14} className="text-cyan-400" /> Chariot Return Delay
              </span>
              <span className="font-black text-cyan-400 font-mono">+{config.delayMinutes} minutes</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {([0, 15, 30, 45] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('delayMinutes', val)}
                  className={`py-2 px-2 rounded-xl text-xs font-bold transition-all border ${
                    config.delayMinutes === val
                      ? 'bg-cyan-600 text-white border-cyan-500 shadow-sm'
                      : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  {val === 0 ? 'On Time' : `+${val}m`}
                </button>
              ))}
            </div>
          </div>

          {/* Fleet Failures */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-300 flex items-center gap-1.5">
                <Bus size={14} className="text-rose-400" /> Fleet Breakdown Stress
              </span>
              <span className="font-black text-rose-400 font-mono">{config.busFailures} buses down</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {([0, 1, 2, 3] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('busFailures', val)}
                  className={`py-2 px-2 rounded-xl text-xs font-bold transition-all border ${
                    config.busFailures === val
                      ? 'bg-rose-600 text-white border-rose-500 shadow-sm'
                      : 'bg-slate-950 text-slate-300 border-slate-800 hover:bg-slate-800'
                  }`}
                >
                  {val === 0 ? '0 (Nominal)' : `${val} down`}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column (7 cols): Comparative Results Table */}
        <div className="lg:col-span-7 bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div>
              <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
                Baseline vs Sandbox Comparison
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                Quantified operational delta against scheduled baseline conditions.
              </p>
            </div>
            <span className="text-xs px-2.5 py-1 rounded-full font-bold bg-slate-800 text-cyan-300 border border-slate-700">
              Deterministic Output
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-xs text-left">
              <thead className="bg-slate-950 text-slate-400 uppercase tracking-wider font-semibold">
                <tr>
                  <th className="py-3 px-3 rounded-l-lg">Metric</th>
                  <th className="py-3 px-3">Baseline</th>
                  <th className="py-3 px-3">Scenario</th>
                  <th className="py-3 px-3 rounded-r-lg">Operational Delta</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800">
                {comparisonRows.map((row, idx) => (
                  <tr key={idx} className="hover:bg-slate-800/40 transition">
                    <td className="py-3.5 px-3 font-bold text-white">
                      {row.label}
                      <span className="block text-[10px] text-slate-400 font-normal">{row.unit}</span>
                    </td>
                    <td className="py-3.5 px-3 font-mono text-slate-300">{row.baseline}</td>
                    <td className="py-3.5 px-3 font-mono font-bold text-cyan-300">{row.scenarioVal}</td>
                    <td className="py-3.5 px-3 font-mono">
                      <span
                        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded font-bold ${
                          row.worse
                            ? 'bg-rose-950 text-rose-300 border border-rose-800'
                            : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        }`}
                      >
                        {row.worse ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                        {row.delta}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Model Summary Footer */}
          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              <ShieldAlert className="w-4 h-4 text-amber-400" />
              <span className="text-slate-300">
                Predicted Risk Transition: <strong className="text-white">HIGH ➔ CRITICAL</strong> under rain surge.
              </span>
            </div>
            <span className="text-[11px] text-slate-400">
              Conserved Fleet: 25 / 25
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
