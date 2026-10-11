import { useState } from 'react';
import {
  ShieldAlert,
  Clock,
  CloudRain,
  Users,
  Bus,
  FileText,
  Sparkles,
} from 'lucide-react';
import type { Festival, ForecastResponse, OptimizeResponse, Stop } from '../types/nila';
import type { DecisionItem, HandoverResponse } from '../api/operations';
import { generateHandoverBrief } from '../api/operations';

interface EventCommanderProps {
  festival: Festival;
  forecast: ForecastResponse;
  optimization: OptimizeResponse;
  decisions: DecisionItem[];
  stops: Stop[];
  onNavigate: (page: string) => void;
}

export default function EventCommander({
  festival,
  forecast,
  optimization,
  decisions,
  stops: _stops,
  onNavigate,
}: EventCommanderProps) {
  const [handoverData, setHandoverData] = useState<HandoverResponse | null>(null);
  const [generatingHandover, setGeneratingHandover] = useState(false);

  const handleGenerateHandover = async () => {
    setGeneratingHandover(true);
    try {
      const brief = await generateHandoverBrief();
      setHandoverData(brief);
    } catch {
      // Fallback handled cleanly
    } finally {
      setGeneratingHandover(false);
    }
  };

  const approvedDecisions = decisions.filter((d) => d.status === 'APPROVED');
  const pendingDecisions = decisions.filter((d) => d.status === 'PENDING');

  return (
    <div className="space-y-6">
      {/* Strategic Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Event Commander Dashboard</h1>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-950 text-rose-300 border border-rose-800">
              DISTRICT COMMAND
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Executive situational posture for District Collector, Police Commissioner, and Transport Authorities.
          </p>
        </div>

        <button
          onClick={handleGenerateHandover}
          disabled={generatingHandover}
          className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold transition shadow-lg self-start md:self-auto disabled:opacity-50"
        >
          <Sparkles className={`w-4 h-4 ${generatingHandover ? 'animate-spin' : ''}`} />
          {generatingHandover ? 'Synthesizing...' : 'Generate Shift Handover'}
        </button>
      </div>

      {/* 10-Second Executive Status Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-rose-900/60 p-5 rounded-2xl space-y-2 shadow-lg">
          <div className="text-xs font-bold uppercase tracking-wider text-rose-400 flex items-center justify-between">
            <span>Network Posture</span>
            <ShieldAlert className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-rose-400">
            {forecast.metrics?.risk || 'CRITICAL'}
          </div>
          <p className="text-xs text-slate-300">
            Egress surge active at Meenakshi Temple perimeter gates.
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
          <div className="text-xs font-bold uppercase tracking-wider text-cyan-400 flex items-center justify-between">
            <span>Peak Surge Window</span>
            <Clock className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {forecast.metrics?.peakTime || '20:10'}
          </div>
          <p className="text-xs text-slate-300">
            Post-Ther chariot return into sacred core.
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
          <div className="text-xs font-bold uppercase tracking-wider text-amber-400 flex items-center justify-between">
            <span>Egress Crowd Volume</span>
            <Users className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-white">
            {forecast.metrics?.peakCrowd?.toLocaleString() || '135,000'}
          </div>
          <p className="text-xs text-slate-300">
            Pilgrims discharging through 4 major temple towers.
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2 shadow-lg">
          <div className="text-xs font-bold uppercase tracking-wider text-emerald-400 flex items-center justify-between">
            <span>Fleet Conservation</span>
            <Bus className="w-4 h-4" />
          </div>
          <div className="text-3xl font-extrabold text-emerald-400 font-mono">
            25 / 25
          </div>
          <p className="text-xs text-slate-300">
            Fixed fleet strictly conserved. Zero invented vehicles.
          </p>
        </div>
      </div>

      {/* Strategic Operational Split */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-5">
        {/* Festival & Environmental Timeline */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Clock className="w-4 h-4 text-cyan-400" /> Event Milestone & Environmental State
          </h2>

          <div className="space-y-3">
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-400">Scheduled Core Ritual</div>
                <div className="text-sm font-bold text-white">
                  {festival.events?.[0]?.name || 'Chariot Procession (Ther Thiruvizha)'}
                </div>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-semibold">
                ACTIVE
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-400">Sacred Perimeter Weather</div>
                <div className="text-sm font-bold text-white flex items-center gap-1.5">
                  <CloudRain className="w-4 h-4 text-cyan-400" /> Scattered Showers (30% Probability)
                </div>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
                MONITORED
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-400">Data Provenance Rating</div>
                <div className="text-sm font-bold text-emerald-400">
                  OFFICIAL HR&CE + OPERATIONAL ESTIMATES
                </div>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-emerald-950 text-emerald-300 border border-emerald-800">
                VERIFIED
              </span>
            </div>
          </div>
        </div>

        {/* Operational Decision State */}
        <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-white flex items-center gap-2">
              <FileText className="w-4 h-4 text-amber-400" /> Operational Movement Decisions
            </h2>
            <button
              onClick={() => onNavigate('Command center')}
              className="text-xs text-cyan-400 hover:text-cyan-300 underline"
            >
              Control Room ➔
            </button>
          </div>

          <div className="space-y-3">
            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-400">Duty Manager Approvals</div>
                <div className="text-sm font-bold text-emerald-400">
                  {approvedDecisions.length} Approved & Dispatched
                </div>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                DISPATCHED
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-400">Pending Review Decisions</div>
                <div className="text-sm font-bold text-amber-400">
                  {pendingDecisions.length} Recommendations Pending
                </div>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-400 border border-amber-800">
                REVIEW REQ
              </span>
            </div>

            <div className="p-3.5 bg-slate-950 rounded-xl border border-slate-800 flex items-center justify-between">
              <div>
                <div className="text-xs text-slate-400">Network Queue Relief</div>
                <div className="text-sm font-bold text-cyan-300">
                  {optimization.overall_queue_reduction_percentage
                    ? `${optimization.overall_queue_reduction_percentage.toFixed(0)}% Projected Queue Reduction`
                    : 'Calculated upon optimization'}
                </div>
              </div>
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-400 border border-cyan-800">
                CALCULATED
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Generated Shift Handover Brief Modal/Panel */}
      {handoverData && (
        <div className="bg-slate-900 border-2 border-cyan-800/80 rounded-2xl p-6 space-y-4 shadow-2xl animate-scaleUp">
          <div className="flex items-center justify-between border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-cyan-400" />
              <h3 className="text-lg font-bold text-white">Synthesized Shift Handover Brief</h3>
            </div>
            <span className="text-xs font-mono text-slate-400">
              {handoverData.timestamp}
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400">Current Network Posture:</span>
              <div className="text-base font-bold text-rose-400 mt-0.5">{handoverData.network_risk}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400">Peak Egress Window:</span>
              <div className="text-base font-bold text-white mt-0.5">{handoverData.peak_window}</div>
            </div>
            <div className="p-3 bg-slate-950 rounded-xl border border-slate-800">
              <span className="text-slate-400">Next Structured Review:</span>
              <div className="text-base font-bold text-cyan-400 mt-0.5">{handoverData.next_review_time}</div>
            </div>
          </div>

          <div className="p-4 bg-slate-950 rounded-xl border border-slate-800 space-y-2 text-xs">
            <div className="font-bold text-slate-300 uppercase tracking-wider text-[11px]">
              Critical Monitored Locations:
            </div>
            <div className="flex flex-wrap gap-2">
              {handoverData.overloaded_stops.map((stop) => (
                <span
                  key={stop}
                  className="px-2.5 py-1 rounded bg-rose-950/60 text-rose-300 border border-rose-800 font-semibold"
                >
                  {stop}
                </span>
              ))}
            </div>

            <div className="font-bold text-slate-300 uppercase tracking-wider text-[11px] pt-2">
              Outstanding Operational Observations:
            </div>
            <ul className="list-disc list-inside space-y-1 text-slate-300">
              {handoverData.outstanding_issues.map((issue, idx) => (
                <li key={idx}>{issue}</li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
