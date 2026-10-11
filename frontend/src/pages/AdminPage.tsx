import { useState } from 'react';
import {
  Settings,
  Database,
  Bus,
  MapPin,
  ShieldCheck,
  CheckCircle2,
  ExternalLink,
} from 'lucide-react';
import type { Festival, Stop } from '../types/nila';

interface AdminPageProps {
  festival: Festival;
  stops: Stop[];
}

export default function AdminPage({ festival, stops }: AdminPageProps) {
  const [activeTab, setActiveTab] = useState<'festivals' | 'stops' | 'fleet' | 'data_sources'>('data_sources');

  return (
    <div className="space-y-6">
      <div className="border-b border-slate-800 pb-5">
        <div className="flex items-center gap-2">
          <Settings className="w-6 h-6 text-slate-400" />
          <h1 className="text-2xl font-bold tracking-tight text-white">System Administration & Catalogs</h1>
          <span className="px-2 py-0.5 rounded text-xs bg-slate-800 text-slate-300 border border-slate-700">
            READ-ONLY OPERATIONAL REGISTRY
          </span>
        </div>
        <p className="text-sm text-slate-400 mt-1">
          Ground-truth registry configurations, official HR&CE data provenance, and public routing service bindings.
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-800">
        {[
          { id: 'data_sources', label: 'Data Provenance & Sources', icon: Database },
          { id: 'festivals', label: 'Festivals Catalog', icon: ShieldCheck },
          { id: 'stops', label: 'Transit Hub Registry', icon: MapPin },
          { id: 'fleet', label: 'Fixed Fleet Specifications', icon: Bus },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-semibold border-b-2 transition -mb-[1px] ${
                activeTab === tab.id
                  ? 'border-cyan-500 text-cyan-400 bg-slate-900/50'
                  : 'border-transparent text-slate-400 hover:text-slate-300'
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab 1: Data Sources */}
      {activeTab === 'data_sources' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Official Festival Catalog</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                OFFICIAL GOVERNMENT SOURCE
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Temple ritual schedules, chariot procession timings, and holy calendar data sourced from Tamil Nadu Hindu Religious & Charitable Endowments (HR&CE).
            </p>
            <div className="text-xs font-mono text-cyan-400 flex items-center gap-1">
              <span>Source URL:</span>
              <a
                href="https://hrce.tn.gov.in/hrcehome/hrce-festival-calendar.php"
                target="_blank"
                rel="noreferrer"
                className="underline flex items-center gap-1 hover:text-cyan-300"
              >
                hrce.tn.gov.in <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Free Routing & Cartography</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                100% FREE & OPEN SOURCE
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Transit routing powered by backend OSRM integration with safe offline geodesic fallback. Map tiles rendered via MapLibre GL and OpenFreeMap public vector tiles. Zero paid API keys required.
            </p>
            <div className="text-xs font-mono text-slate-400">
              Tile Provider: OpenFreeMap Libre Vector | Routing: OSRM Public Engine
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Fleet Telemetry Ledger</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
                SIMULATED TELEMETRY
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Per-vehicle passenger loads and release points are simulated operational telemetry for the Sakthi Hackfest'26 demonstration. Strictly not connected to production hardware GPS.
            </p>
            <div className="text-xs font-mono text-slate-400">
              Fleet Size: 25 Fixed Vehicles | Update Rate: Live Reactive
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-white">Generative AI Copilot</h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800">
                GROUNDED FASTAPI BACKEND
              </span>
            </div>
            <p className="text-xs text-slate-300">
              Gemini GenAI model integrated securely on the FastAPI backend with tool grounding. API key is never exposed to the frontend browser bundle.
            </p>
            <div className="text-xs font-mono text-slate-400">
              Architecture: React ➔ FastAPI ➔ NilaAIService ➔ Gemini
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Festivals */}
      {activeTab === 'festivals' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h2 className="text-sm font-bold text-white">Active Festival Profile</h2>
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Festival ID:</span>
              <span className="font-mono text-cyan-300">{festival.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Name:</span>
              <span className="font-bold text-white">{festival.name}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Temple:</span>
              <span className="text-slate-200">{festival.temple}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">City / Jurisdiction:</span>
              <span className="text-slate-200">{festival.city}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Expected Peak Day:</span>
              <span className="text-slate-200">{festival.dateLabel}</span>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Stops */}
      {activeTab === 'stops' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h2 className="text-sm font-bold text-white">Active Transit Hubs ({stops.length})</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            {stops.map((s) => (
              <div key={s.id} className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-2">
                <div className="font-bold text-white">{s.name}</div>
                <div className="text-slate-400">Stop ID: <span className="font-mono text-slate-300">{s.id}</span></div>
                <div className="text-slate-400">Holding Capacity: <span className="font-bold text-white">{s.capacity} pax</span></div>
                <div className="text-slate-400">Current Fleet Allocation: <span className="font-bold text-cyan-400">{s.currentBuses} buses</span></div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Fleet */}
      {activeTab === 'fleet' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-5 space-y-4">
          <h2 className="text-sm font-bold text-white">Fixed Fleet Invariant Specifications</h2>
          <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs space-y-3">
            <div className="flex items-center gap-2 text-emerald-400 font-bold">
              <CheckCircle2 className="w-4 h-4" /> Fixed Fleet Size Invariant: F_total = 25
            </div>
            <p className="text-slate-300">
              The optimizer solves an allocation redistribution schedule subject to the hard constraint that total vehicles across all stops remain constant. No additional buses may be created.
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2">
              <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">Standard Bus Capacity</div>
                <div className="font-bold text-white text-sm">51 Passengers</div>
              </div>
              <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">Staging Floor Per Stop</div>
                <div className="font-bold text-white text-sm">1 Bus Minimum</div>
              </div>
              <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">Turnaround Buffer</div>
                <div className="font-bold text-white text-sm">15 Minutes</div>
              </div>
              <div className="p-2.5 bg-slate-900 rounded-lg border border-slate-800">
                <div className="text-[10px] text-slate-400">Optimization Solver</div>
                <div className="font-bold text-emerald-400 text-sm">Deterministic LP</div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
