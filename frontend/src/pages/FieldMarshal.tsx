import { useState } from 'react';
import {
  MapPin,
  CheckCircle2,
  Send,
  Users,
  Clock,
  Radio,
} from 'lucide-react';
import type { Stop } from '../types/nila';
import { reportStopCrowd, type CrowdReportResponse } from '../api/operations';

interface FieldMarshalProps {
  stops: Stop[];
}

export default function FieldMarshal({ stops }: FieldMarshalProps) {
  const [selectedStopId, setSelectedStopId] = useState<string>(
    stops[0]?.id || 'stop-periyar'
  );
  const [selectedLevel, setSelectedLevel] = useState<
    'LIGHT' | 'MODERATE' | 'HEAVY' | 'UNSAFE'
  >('MODERATE');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [recentReports, setRecentReports] = useState<CrowdReportResponse[]>([
    {
      id: 'CR-0001',
      stop_id: 'stop-periyar',
      level: 'HEAVY',
      notes: 'South tower gate procession dispersing into terminal',
      timestamp: '18:40:12',
      status: 'RECORDED',
    },
  ]);
  const [toastMsg, setToastMsg] = useState('');

  const currentStop = stops.find((s) => s.id === selectedStopId) || stops[0];

  const handleSubmitReport = async () => {
    setSubmitting(true);
    setToastMsg('');
    try {
      const res = await reportStopCrowd(selectedStopId, selectedLevel, notes || undefined);
      setRecentReports((prev) => [res, ...prev]);
      setToastMsg(`Crowd report logged for ${currentStop?.shortName || selectedStopId}: ${selectedLevel}`);
      setNotes('');
    } catch {
      setToastMsg('Failed to log field crowd report. Check connectivity.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-md mx-auto space-y-5 py-2">
      {/* Mobile Top Header */}
      <div className="bg-slate-900 border border-slate-800 p-4 rounded-2xl flex items-center justify-between shadow-lg">
        <div className="flex items-center gap-2.5">
          <div className="w-10 h-10 rounded-xl bg-rose-950 border border-rose-800 flex items-center justify-center text-rose-400">
            <Radio className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="text-xs uppercase font-extrabold tracking-wider text-rose-400">
              Field Marshal Unit
            </div>
            <div className="text-sm font-bold text-white">On-Ground Ground Truth</div>
          </div>
        </div>

        <div className="text-right">
          <span className="inline-block px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
            DISPATCHED
          </span>
          <div className="text-[10px] text-slate-400 mt-0.5">Sector North</div>
        </div>
      </div>

      {toastMsg && (
        <div className="p-3 bg-emerald-950/90 border border-emerald-800 text-emerald-300 text-xs rounded-xl flex items-center gap-2 shadow-lg animate-fadeIn">
          <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* Stop Selector Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4 shadow-xl">
        <div className="border-b border-slate-800 pb-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <MapPin className="w-4 h-4 text-cyan-400" /> Assigned Transit Stop
          </label>
          <select
            value={selectedStopId}
            onChange={(e) => setSelectedStopId(e.target.value)}
            className="w-full mt-2 bg-slate-950 border border-slate-700 rounded-xl px-3 py-2.5 text-white font-bold text-base focus:outline-none focus:border-cyan-500"
          >
            {stops.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.currentBuses} buses active)
              </option>
            ))}
          </select>
        </div>

        {/* 1-Tap Crowd Level Selector */}
        <div className="space-y-3">
          <label className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
            <Users className="w-4 h-4 text-rose-400" /> Current Observed Density
          </label>

          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setSelectedLevel('LIGHT')}
              className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
                selectedLevel === 'LIGHT'
                  ? 'bg-emerald-950 text-emerald-300 border-emerald-500 ring-2 ring-emerald-500'
                  : 'bg-slate-950 hover:bg-slate-800 text-emerald-400 border-slate-800'
              }`}
            >
              <span className="text-xl">🟢</span>
              <span>LIGHT</span>
              <span className="text-[10px] text-slate-400 font-normal">Free boarding flow</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedLevel('MODERATE')}
              className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
                selectedLevel === 'MODERATE'
                  ? 'bg-amber-950 text-amber-300 border-amber-500 ring-2 ring-amber-500'
                  : 'bg-slate-950 hover:bg-slate-800 text-amber-400 border-slate-800'
              }`}
            >
              <span className="text-xl">🟡</span>
              <span>MODERATE</span>
              <span className="text-[10px] text-slate-400 font-normal">Lines forming</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedLevel('HEAVY')}
              className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
                selectedLevel === 'HEAVY'
                  ? 'bg-orange-950 text-orange-300 border-orange-500 ring-2 ring-orange-500'
                  : 'bg-slate-950 hover:bg-slate-800 text-orange-400 border-slate-800'
              }`}
            >
              <span className="text-xl">🟠</span>
              <span>HEAVY</span>
              <span className="text-[10px] text-slate-400 font-normal">Terminal full</span>
            </button>

            <button
              type="button"
              onClick={() => setSelectedLevel('UNSAFE')}
              className={`py-4 px-3 rounded-xl border font-bold text-sm transition flex flex-col items-center justify-center gap-1 active:scale-95 ${
                selectedLevel === 'UNSAFE'
                  ? 'bg-rose-950 text-rose-300 border-rose-500 ring-2 ring-rose-500'
                  : 'bg-slate-950 hover:bg-slate-800 text-rose-400 border-slate-800'
              }`}
            >
              <span className="text-xl">🔴</span>
              <span>UNSAFE</span>
              <span className="text-[10px] text-slate-400 font-normal">Spillover into road</span>
            </button>
          </div>
        </div>

        {/* Optional notes */}
        <div className="space-y-1.5">
          <label className="text-xs font-semibold text-slate-400">Field Observations (Optional):</label>
          <textarea
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            placeholder="e.g. Rain causing crowd bottleneck near Gate 3..."
            rows={2}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Transmit button */}
        <button
          onClick={handleSubmitReport}
          disabled={submitting}
          className="w-full py-3.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-extrabold text-sm transition shadow-xl flex items-center justify-center gap-2 active:scale-98 disabled:opacity-50"
        >
          <Send className="w-4 h-4" />
          {submitting ? 'Transmitting...' : 'TRANSMIT REPORT TO CONTROL ROOM'}
        </button>
      </div>

      {/* Confirmed Reports History */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-cyan-400" /> Recent Field Transmissions
        </h3>

        <div className="space-y-2">
          {recentReports.map((r) => (
            <div
              key={r.id}
              className="p-2.5 bg-slate-950 rounded-xl border border-slate-800/80 text-xs flex items-center justify-between"
            >
              <div>
                <span className="font-bold text-white uppercase">{r.level}</span>
                <span className="text-slate-400 ml-2 font-mono">[{r.timestamp}]</span>
                {r.notes && <div className="text-slate-400 text-[11px] mt-0.5">{r.notes}</div>}
              </div>
              <span className="text-emerald-400 text-[10px] font-bold bg-emerald-950 px-2 py-0.5 rounded border border-emerald-800">
                {r.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
