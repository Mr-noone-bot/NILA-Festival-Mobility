import {
  Activity,
  ArrowDownRight,
  ArrowUpRight,
  Bus,
  Clock,
  CloudRain,
  SlidersHorizontal,
  Sparkles,
  TrendingUp,
  Users,
} from 'lucide-react';
import type { ScenarioConfig, ScenarioResult } from '../types/nila';
import { formatNumber, riskLabel, toRiskClass } from '../utils/format';

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
  const comparisonRows = [
    {
      label: 'Peak Crowd Inflow',
      baseline: formatNumber(scenario.baseline.peakCrowd),
      scenarioVal: formatNumber(scenario.scenario.peakCrowd),
      unit: 'devotees',
      delta:
        scenario.scenario.peakCrowd !== scenario.baseline.peakCrowd
          ? `+${Math.round(
              ((scenario.scenario.peakCrowd - scenario.baseline.peakCrowd) /
                scenario.baseline.peakCrowd) *
                100
            )}%`
          : '0%',
      worse: scenario.scenario.peakCrowd > scenario.baseline.peakCrowd,
    },
    {
      label: 'Surge Peak Window',
      baseline: scenario.baseline.peakTime,
      scenarioVal: scenario.scenario.peakTime,
      unit: 'local time',
      delta: config.delayMinutes > 0 ? `+${config.delayMinutes}m delay` : 'On schedule',
      worse: scenario.scenario.peakTime !== scenario.baseline.peakTime,
    },
    {
      label: 'Average Passenger Wait',
      baseline: `${scenario.baseline.waitingMinutes} min`,
      scenarioVal: `${scenario.scenario.waitingMinutes} min`,
      unit: 'queue duration',
      delta:
        scenario.scenario.waitingMinutes > scenario.baseline.waitingMinutes
          ? `+${scenario.scenario.waitingMinutes - scenario.baseline.waitingMinutes} min`
          : 'Normal',
      worse: scenario.scenario.waitingMinutes > scenario.baseline.waitingMinutes,
    },
    {
      label: 'Accumulated Stop Queues',
      baseline: `${formatNumber(scenario.baseline.queue)} pax`,
      scenarioVal: `${formatNumber(scenario.scenario.queue)} pax`,
      unit: 'across choke points',
      delta:
        scenario.scenario.queue > scenario.baseline.queue
          ? `+${Math.round(
              ((scenario.scenario.queue - scenario.baseline.queue) /
                scenario.baseline.queue) *
                100
            )}% backlog`
          : 'Stable',
      worse: scenario.scenario.queue > scenario.baseline.queue,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-bold uppercase tracking-wider text-sky-700">
            What-If Operational Stress Testing
          </div>
          <h2 className="text-xl font-black text-slate-900 mt-1 flex items-center gap-2">
            Weather, Attendance & Delay Scenario Simulator
          </h2>
          <p className="text-xs text-slate-600 mt-1">
            Simulate volatile weather conditions, attendance surges, and fleet breakdowns to observe model behavior before dispatching.
          </p>
        </div>

        <button
          onClick={onRunScenario}
          disabled={scenarioStatus === 'loading'}
          className="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm transition-all disabled:opacity-60"
        >
          {scenarioStatus === 'loading' ? (
            <span className="spinner spinner-small" />
          ) : (
            <Activity size={15} />
          )}
          {scenarioStatus === 'loading' ? 'Simulating Dynamic Model…' : 'Simulate Scenario'}
        </button>
      </div>

      {scenarioMessage && (
        <div className="text-xs text-sky-800 bg-sky-50 border border-sky-200 rounded-xl px-4 py-2 font-medium flex items-center gap-2">
          <Sparkles size={14} className="text-sky-600" />
          <span>{scenarioMessage}</span>
        </div>
      )}

      {/* Main Grid: Controls vs Comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (5 cols): Interactive Controls */}
        <div className="lg:col-span-5 bg-white border border-sky-100 rounded-2xl p-6 shadow-sm space-y-5">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-800 flex items-center gap-2">
              <SlidersHorizontal size={16} className="text-sky-600" />
              Adjust Simulation Parameters
            </h3>
            <span className="text-xs px-2 py-0.5 rounded-full font-bold bg-sky-50 text-sky-800 border border-sky-200">
              Interactive
            </span>
          </div>

          {/* Attendance Multiplier */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700 flex items-center gap-1.5">
                <Users size={14} className="text-sky-600" /> Attendance Multiplier
              </span>
              <span className="font-black text-sky-800">{config.attendance}% expected turnout</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {([100, 120, 150] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('attendance', val)}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all border ${
                    config.attendance === val
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-sky-50'
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
              <span className="font-bold text-slate-700 flex items-center gap-1.5">
                <CloudRain size={14} className="text-sky-600" /> Rain Probability / Heat Profile
              </span>
              <span className="font-black text-sky-800">{config.rain}% precipitation</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {([0, 30, 60, 90] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('rain', val)}
                  className={`py-2 px-2 rounded-xl text-xs font-bold transition-all border ${
                    config.rain === val
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-sky-50'
                  }`}
                >
                  {val}% {val === 0 ? 'Clear' : val >= 60 ? 'Heavy' : ''}
                </button>
              ))}
            </div>
          </div>

          {/* Event Delay */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700 flex items-center gap-1.5">
                <Clock size={14} className="text-sky-600" /> Ritual Event Milestone Delay
              </span>
              <span className="font-black text-sky-800">{config.delayMinutes} min delay</span>
            </div>
            <div className="grid grid-cols-4 gap-1.5">
              {([0, 15, 30, 45] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('delayMinutes', val)}
                  className={`py-2 px-2 rounded-xl text-xs font-bold transition-all border ${
                    config.delayMinutes === val
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-sky-50'
                  }`}
                >
                  +{val}m {val === 0 ? 'None' : ''}
                </button>
              ))}
            </div>
          </div>

          {/* Bus Failures */}
          <div className="space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700 flex items-center gap-1.5">
                <Bus size={14} className="text-sky-600" /> Mechanical / Route Bus Failures
              </span>
              <span className="font-black text-sky-800">{config.busFailures} broken down</span>
            </div>
            <div className="grid grid-cols-3 gap-2">
              {([0, 1, 2] as const).map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => onUpdateConfig('busFailures', val)}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all border ${
                    config.busFailures === val
                      ? 'bg-sky-600 text-white border-sky-600 shadow-sm'
                      : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-sky-50'
                  }`}
                >
                  {val} {val === 0 ? 'Zero (100% Ops)' : val === 1 ? '1 bus down' : '2 buses down'}
                </button>
              ))}
            </div>
          </div>

          {/* Environmental note */}
          <div className="p-3 bg-sky-50 rounded-xl border border-sky-200 text-[11px] text-slate-600">
            <strong>Simulation Logic:</strong> Rain reduces pedestrian egress walking speed by ~30%, extending platform dwell time. Attendance surges linearly multiply radial bus stop queue pressure.
          </div>
        </div>

        {/* Right Column (7 cols): Comparison Cards & Table */}
        <div className="lg:col-span-7 space-y-6">
          {/* Baseline vs Scenario Head-to-Head Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Baseline Card */}
            <div className="bg-white border border-slate-200 rounded-2xl p-5 shadow-sm">
              <div className="flex items-center justify-between text-slate-500 mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-slate-600">
                  Standard Baseline
                </span>
                <span className="w-2.5 h-2.5 rounded-full bg-slate-400" />
              </div>
              <div className="text-2xl font-black text-slate-800">
                {formatNumber(scenario.baseline.peakCrowd)}
              </div>
              <div className="text-xs text-slate-500 mt-1">Pilgrims expected at normal pace</div>
              <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                <span>Avg Wait: {scenario.baseline.waitingMinutes}m</span>
                <span className={`risk-pill ${toRiskClass(scenario.baseline.risk)}`}>
                  <span className="risk-dot" />
                  {riskLabel(scenario.baseline.risk)}
                </span>
              </div>
            </div>

            {/* Selected Scenario Card */}
            <div className="bg-sky-50/80 border-2 border-sky-400 rounded-2xl p-5 shadow-sm relative overflow-hidden">
              <div className="flex items-center justify-between text-sky-800 mb-2">
                <span className="text-xs font-bold uppercase tracking-wider text-sky-900">
                  Simulated Scenario
                </span>
                <span className="w-2.5 h-2.5 rounded-full bg-sky-600 animate-ping" />
              </div>
              <div className="text-2xl font-black text-sky-950">
                {formatNumber(scenario.scenario.peakCrowd)}
              </div>
              <div className="text-xs text-sky-800 mt-1">
                With {config.attendance}% attendance & {config.rain}% rain
              </div>
              <div className="mt-3 pt-3 border-t border-sky-200 flex items-center justify-between text-xs">
                <span className="font-bold text-sky-900">
                  Avg Wait: {scenario.scenario.waitingMinutes}m
                </span>
                <span className={`risk-pill ${toRiskClass(scenario.scenario.risk)}`}>
                  <span className="risk-dot" />
                  {riskLabel(scenario.scenario.risk)}
                </span>
              </div>
            </div>
          </div>

          {/* Comparison Table */}
          <div className="bg-white border border-sky-100 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <TrendingUp size={16} className="text-sky-600" />
                Head-to-Head Metric Variance
              </h4>
              <span className="text-xs text-slate-500">
                Delta based on active parameter sliders
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-slate-200 text-slate-500 uppercase tracking-wider">
                    <th className="py-2.5 px-3">Metric Indicator</th>
                    <th className="py-2.5 px-3">Baseline</th>
                    <th className="py-2.5 px-3">Simulated Outcome</th>
                    <th className="py-2.5 px-3">Projected Variance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-medium">
                  {comparisonRows.map((row) => (
                    <tr key={row.label} className="hover:bg-slate-50">
                      <td className="py-3 px-3 font-bold text-slate-900">{row.label}</td>
                      <td className="py-3 px-3 text-slate-600">{row.baseline}</td>
                      <td className="py-3 px-3 font-bold text-sky-900">{row.scenarioVal}</td>
                      <td className="py-3 px-3">
                        <span
                          className={`font-bold px-2 py-0.5 rounded-full text-[11px] inline-flex items-center gap-0.5 ${
                            row.worse
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-emerald-100 text-emerald-800'
                          }`}
                        >
                          {row.worse ? <ArrowUpRight size={11} /> : <ArrowDownRight size={11} />}
                          {row.delta}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Operator Actionable Takeaways */}
          <div className="bg-gradient-to-r from-sky-600 to-sky-700 text-white rounded-2xl p-5 shadow-sm space-y-2">
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-sky-200">
              <Sparkles size={16} /> Operational Decision Takeaway
            </div>
            <p className="text-sm font-medium leading-relaxed text-sky-50">
              {scenario.scenario.risk === 'CRITICAL' || scenario.scenario.risk === 'HIGH'
                ? `Under this ${config.attendance}% attendance condition with ${config.rain}% rain, modeled passenger queue surge exceeds Periyar Stand's physical buffer by ${scenario.scenario.waitingMinutes} minutes. Recommend pre-positioning additional reserve buses before the Therottam chariot arrival.`
                : 'Current parameters maintain acceptable queue thresholds across radial bus terminals. Standby fleets at Mattuthavani can absorb regional variations.'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
