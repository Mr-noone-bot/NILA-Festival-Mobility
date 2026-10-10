import {
  Calendar,
  CheckCircle2,
  ChevronDown,
  Clock,
  Compass,
  Flame,
  MapPin,
  Sparkles,
} from 'lucide-react';
import type { Festival } from '../types/nila';
import { formatNumber } from '../utils/format';

interface FestivalPlannerProps {
  festivals: Festival[];
  selectedFestivalId: string;
  onSelectFestival: (festivalId: string) => void;
  onRunForecast: () => void;
  onNavigate: (page: string) => void;
}

export default function FestivalPlanner({
  festivals,
  selectedFestivalId,
  onSelectFestival,
  onRunForecast,
  onNavigate,
}: FestivalPlannerProps) {
  const currentFestival = festivals.find((f) => f.id === selectedFestivalId) ?? festivals[0];
  const cities = Array.from(new Set(festivals.map((f) => f.city)));

  return (
    <div className="space-y-6">
      {/* Intro Header */}
      <div className="bg-white border border-sky-200 rounded-2xl p-6 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="text-xs font-bold uppercase tracking-wider text-sky-600">
              Operations Configuration
            </div>
            <h2 className="text-xl font-black text-slate-900 mt-1">
              Festival & Operating Context Planner
            </h2>
            <p className="text-sm text-slate-600 mt-1">
              Select the Tamil Nadu temple festival, regional transit sector, and operational milestone.
            </p>
          </div>
          <button
            onClick={() => {
              onRunForecast();
              onNavigate('Command center');
            }}
            className="px-5 py-2.5 bg-sky-600 hover:bg-sky-700 text-white rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-sm transition-all"
          >
            Apply Context & Run Prediction <Sparkles size={16} />
          </button>
        </div>

        {/* Structured Selectors Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-100">
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              State / Administrative Region
            </label>
            <div className="relative">
              <select
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-900 appearance-none focus:outline-none focus:ring-2 focus:ring-sky-500 focus:bg-white"
                value="Tamil Nadu"
                disabled
              >
                <option value="Tamil Nadu">Tamil Nadu (TNSTC Jurisdiction)</option>
              </select>
              <ChevronDown
                size={16}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Festival City / Sector
            </label>
            <div className="relative">
              <select
                className="w-full bg-white border border-slate-300 rounded-xl px-3.5 py-2.5 text-sm font-semibold text-slate-900 appearance-none focus:outline-none focus:ring-2 focus:ring-sky-500"
                value={currentFestival.city}
                onChange={(e) => {
                  const targetCity = e.target.value;
                  const match = festivals.find((f) => f.city === targetCity);
                  if (match) onSelectFestival(match.id);
                }}
              >
                {cities.map((city) => (
                  <option key={city} value={city}>
                    {city} District
                  </option>
                ))}
              </select>
              <ChevronDown
                size={16}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-500 pointer-events-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">
              Temple Festival Event
            </label>
            <div className="relative">
              <select
                className="w-full bg-sky-50/70 border border-sky-300 rounded-xl px-3.5 py-2.5 text-sm font-bold text-sky-950 appearance-none focus:outline-none focus:ring-2 focus:ring-sky-500"
                value={selectedFestivalId}
                onChange={(e) => onSelectFestival(e.target.value)}
              >
                {festivals.map((fest) => (
                  <option key={fest.id} value={fest.id}>
                    {fest.name} ({fest.city})
                  </option>
                ))}
              </select>
              <ChevronDown
                size={16}
                className="absolute right-3.5 top-1/2 -translate-y-1/2 text-sky-700 pointer-events-none"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Selected Festival Spotlight */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Festival Details & Sacred Ritual Milestones */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white border border-sky-100 rounded-2xl p-6 shadow-sm space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <span className="text-[11px] font-bold uppercase tracking-wider text-sky-600 bg-sky-50 px-2.5 py-1 rounded-full border border-sky-200">
                  Active Operational Target
                </span>
                <h3 className="text-2xl font-black text-slate-900 mt-2">
                  {currentFestival.name}
                </h3>
                <p className="text-sm font-medium text-slate-600 flex items-center gap-1.5 mt-1">
                  <MapPin size={15} className="text-sky-600" /> {currentFestival.temple} · {currentFestival.city}
                </p>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-500">Projected Turnout</div>
                <div className="text-2xl font-black text-slate-900">
                  {formatNumber(currentFestival.expectedAttendance)}
                </div>
                <div className="text-[11px] font-semibold text-sky-700">devotees / day</div>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-4 border-t border-slate-100 text-xs">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-slate-500 flex items-center gap-1 mb-1">
                  <Calendar size={13} /> Target Date
                </div>
                <div className="font-bold text-slate-900">{currentFestival.dateLabel}</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-slate-500 flex items-center gap-1 mb-1">
                  <Clock size={13} /> Peak Surge Window
                </div>
                <div className="font-bold text-slate-900">{currentFestival.peakTime}</div>
              </div>
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-100">
                <div className="text-slate-500 flex items-center gap-1 mb-1">
                  <Compass size={13} /> Geographic Anchor
                </div>
                <div className="font-bold text-slate-900">
                  {currentFestival.coordinates[1].toFixed(4)}° N, {currentFestival.coordinates[0].toFixed(4)}° E
                </div>
              </div>
            </div>
          </div>

          {/* Ritual Milestones & Surge Triggers */}
          <div className="bg-white border border-sky-100 rounded-2xl p-6 shadow-sm">
            <h4 className="text-base font-bold text-slate-900 flex items-center gap-2 mb-4">
              <Flame size={18} className="text-amber-500" />
              Ritual Timeline & Post-Event Surge Triggers
            </h4>
            <p className="text-xs text-slate-500 mb-4">
              Sacred rituals dictate crowd dynamics. When ceremonies conclude, simultaneous mass exit flows concentrate into radial bus stands.
            </p>

            <div className="space-y-3">
              {(currentFestival.events || [
                { name: 'Sacred Ritual Ceremony', timestamp: '08:00 AM', estimatedTurnout: 350000 },
                { name: 'Deity Procession Egress', timestamp: '10:30 AM', estimatedTurnout: 500000 },
                { name: 'Evening Theerthavari', timestamp: '05:30 PM', estimatedTurnout: 220000 },
              ]).map((evt, idx) => (
                <div
                  key={evt.name}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-100 hover:border-sky-200 hover:bg-sky-50/30 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <span className="w-7 h-7 rounded-lg bg-sky-100 text-sky-700 text-xs font-bold flex items-center justify-center shrink-0">
                      {idx + 1}
                    </span>
                    <div>
                      <div className="text-sm font-bold text-slate-900">{evt.name}</div>
                      <div className="text-xs text-slate-500 flex items-center gap-1">
                        <Clock size={12} /> Scheduled: {evt.timestamp}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-bold text-slate-800">
                      ~{formatNumber(evt.estimatedTurnout)} pilgrims
                    </div>
                    <span className="text-[10px] font-semibold text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-200">
                      Surge Trigger
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Col: Operating Catalog & Guidelines */}
        <div className="space-y-6">
          <div className="bg-white border border-sky-100 rounded-2xl p-6 shadow-sm space-y-4">
            <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <CheckCircle2 size={16} className="text-emerald-600" />
              Operating Protocols Enforced
            </h4>
            <div className="space-y-3 text-xs text-slate-600">
              <div className="p-3 bg-sky-50 rounded-xl border border-sky-200">
                <strong className="text-sky-900 block mb-1">Fixed Fleet Conservation</strong>
                Total buses cannot be generated ad-hoc. All adjustments require redeploying existing fleet from lower-pressure terminals.
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <strong className="text-slate-900 block mb-1">OSRM Congestion Multiplier</strong>
                Travel times account for pedestrian spillover and narrow temple car streets (t_arrival = t_departure + travel_time).
              </div>
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <strong className="text-slate-900 block mb-1">Transparent Service Trade-offs</strong>
                Before shifting vehicles, the operator sees origin wait time penalties vs destination relief.
              </div>
            </div>
          </div>

          <div className="bg-gradient-to-br from-sky-50 to-white border border-sky-200 rounded-2xl p-6 shadow-sm">
            <h4 className="text-xs font-bold uppercase tracking-wider text-sky-800 mb-2">
              Available Festival Catalog
            </h4>
            <div className="space-y-2">
              {festivals.map((f) => (
                <button
                  key={f.id}
                  onClick={() => onSelectFestival(f.id)}
                  className={`w-full text-left p-2.5 rounded-xl border text-xs transition-all flex items-center justify-between ${
                    f.id === selectedFestivalId
                      ? 'border-sky-500 bg-white font-bold text-sky-900 shadow-sm'
                      : 'border-slate-200 hover:border-sky-300 bg-white/70 text-slate-700'
                  }`}
                >
                  <span>{f.name}</span>
                  <span className="text-[11px] text-slate-500 font-normal">{f.city}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
