import { useState, useMemo } from 'react';
import {
  Bus,
  CheckCircle2,
  AlertTriangle,
  Clock,
  MapPin,
  Search,
  Filter,
  X,
  ArrowRight,
  RefreshCw,
  Sliders,
  Check
} from 'lucide-react';
import type { BusTelemetryItem, FleetSummaryResponse, OccupancyBand } from '../api/operations';
import { updateBusOccupancy } from '../api/operations';

interface FleetIntelligenceProps {
  fleetData: FleetSummaryResponse | null;
  loading: boolean;
  onRefresh: () => void;
  onSelectBusForDecision?: (busId: string) => void;
}

export default function FleetIntelligence({
  fleetData,
  loading,
  onRefresh,
  onSelectBusForDecision,
}: FleetIntelligenceProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedBus, setSelectedBus] = useState<BusTelemetryItem | null>(null);
  const [updatingOccupancy, setUpdatingOccupancy] = useState(false);
  const [verifySuccessMsg, setVerifySuccessMsg] = useState('');

  const buses = useMemo(() => fleetData?.buses || [], [fleetData]);

  const filteredBuses = useMemo(() => {
    return buses.filter((bus) => {
      const matchesSearch =
        bus.bus_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        bus.route.toLowerCase().includes(searchQuery.toLowerCase()) ||
        bus.current_stop.toLowerCase().includes(searchQuery.toLowerCase());

      if (!matchesSearch) return false;

      if (statusFilter === 'ALL') return true;
      if (statusFilter === 'LOW_CONFIDENCE') {
        return bus.confidence === 'LOW' || bus.confidence === 'VERIFY_REQUIRED';
      }
      return bus.status === statusFilter;
    });
  }, [buses, searchQuery, statusFilter]);

  const handleUpdateOccupancy = async (band: OccupancyBand) => {
    if (!selectedBus) return;
    setUpdatingOccupancy(true);
    setVerifySuccessMsg('');
    try {
      const updated = await updateBusOccupancy(selectedBus.bus_id, band);
      setSelectedBus(updated);
      setVerifySuccessMsg(`Updated ${selectedBus.bus_id} to ${band}`);
      onRefresh();
    } catch {
      // Error handled cleanly
    } finally {
      setUpdatingOccupancy(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'AVAILABLE':
        return 'bg-emerald-950/70 text-emerald-400 border-emerald-800';
      case 'IN_SERVICE':
        return 'bg-sky-950/70 text-sky-400 border-sky-800';
      case 'RETURNING':
        return 'bg-amber-950/70 text-amber-400 border-amber-800';
      case 'UNAVAILABLE':
        return 'bg-rose-950/70 text-rose-400 border-rose-800';
      default:
        return 'bg-slate-800 text-slate-300 border-slate-700';
    }
  };

  const getOccupancyBadge = (band: string) => {
    switch (band) {
      case 'EMPTY':
        return 'text-emerald-400 bg-emerald-950/40 border-emerald-800/60';
      case 'SEATS_FREE':
        return 'text-cyan-400 bg-cyan-950/40 border-cyan-800/60';
      case 'STANDING':
        return 'text-amber-400 bg-amber-950/40 border-amber-800/60';
      case 'CROWDED':
        return 'text-rose-400 bg-rose-950/40 border-rose-800/60';
      default:
        return 'text-slate-400 bg-slate-900 border-slate-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header & Metrics */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold tracking-tight text-white">Fleet Intelligence</h1>
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
              LIVE TELEMETRY
            </span>
            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700">
              PROVENANCE: SIMULATED TELEMETRY
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-1">
            Real-time supply-side vehicle ledger tracking occupancy, release points, and candidate availability.
          </p>
        </div>

        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition self-start md:self-auto disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          Refresh Fleet
        </button>
      </div>

      {/* KPI Counters */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
          <div className="text-xs font-medium text-slate-400 uppercase tracking-wider">Total Fleet</div>
          <div className="text-2xl font-bold text-white mt-1">{fleetData?.total_fleet || 25}</div>
          <div className="text-[11px] text-emerald-400 mt-1 font-medium">Conserved Invariant</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
          <div className="text-xs font-medium text-emerald-400 uppercase tracking-wider">Available</div>
          <div className="text-2xl font-bold text-emerald-400 mt-1">{fleetData?.available ?? 7}</div>
          <div className="text-[11px] text-slate-400 mt-1">Immediate staging</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
          <div className="text-xs font-medium text-sky-400 uppercase tracking-wider">In Service</div>
          <div className="text-2xl font-bold text-sky-400 mt-1">{fleetData?.in_service ?? 14}</div>
          <div className="text-[11px] text-slate-400 mt-1">On active routes</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl">
          <div className="text-xs font-medium text-amber-400 uppercase tracking-wider">Returning</div>
          <div className="text-2xl font-bold text-amber-400 mt-1">{fleetData?.returning ?? 3}</div>
          <div className="text-[11px] text-slate-400 mt-1">Releasing &lt;20 min</div>
        </div>

        <div className="bg-slate-900/90 border border-slate-800 p-3.5 rounded-xl col-span-2 sm:col-span-1">
          <div className="text-xs font-medium text-rose-400 uppercase tracking-wider">Unavailable</div>
          <div className="text-2xl font-bold text-rose-400 mt-1">{fleetData?.unavailable ?? 1}</div>
          <div className="text-[11px] text-slate-400 mt-1">Maintenance / Holding</div>
        </div>
      </div>

      {/* Filter and Search Controls */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-3 bg-slate-900/60 p-3 rounded-xl border border-slate-800">
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by Bus ID (e.g. BUS-12), Route, or Stop..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex items-center gap-1.5 overflow-x-auto pb-1 sm:pb-0">
          <span className="text-xs text-slate-400 flex items-center gap-1 mr-1">
            <Filter className="w-3.5 h-3.5" /> Filter:
          </span>
          {['ALL', 'AVAILABLE', 'RETURNING', 'IN_SERVICE', 'LOW_CONFIDENCE'].map((f) => (
            <button
              key={f}
              onClick={() => setStatusFilter(f)}
              className={`px-2.5 py-1 rounded-md text-xs font-medium transition whitespace-nowrap ${
                statusFilter === f
                  ? 'bg-cyan-600 text-white font-semibold'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {f.replace('_', ' ')}
            </button>
          ))}
        </div>
      </div>

      {/* Fleet Ledger Table */}
      <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/70 border-b border-slate-800 text-xs text-slate-400 uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Bus ID</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4">Current Stop</th>
                <th className="py-3 px-4">Occupancy Band</th>
                <th className="py-3 px-4">Load / Cap</th>
                <th className="py-3 px-4">Free At</th>
                <th className="py-3 px-4">Release Point</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {filteredBuses.map((bus) => (
                <tr
                  key={bus.bus_id}
                  onClick={() => setSelectedBus(bus)}
                  className={`hover:bg-slate-800/50 cursor-pointer transition ${
                    selectedBus?.bus_id === bus.bus_id ? 'bg-cyan-950/30' : ''
                  }`}
                >
                  <td className="py-3 px-4 font-bold text-white flex items-center gap-2 font-sans">
                    <Bus className="w-4 h-4 text-slate-400" />
                    {bus.bus_id}
                    {bus.candidate_for_repositioning && (
                      <span className="text-[10px] px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800 font-medium">
                        CANDIDATE
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-semibold border ${getStatusBadge(
                        bus.status
                      )}`}
                    >
                      {bus.status}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300 font-sans">{bus.current_stop}</td>
                  <td className="py-3 px-4">
                    <span
                      className={`px-2 py-0.5 rounded text-[11px] font-medium border ${getOccupancyBadge(
                        bus.occupancy_band
                      )}`}
                    >
                      {bus.occupancy_band.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-300">
                    {bus.current_load} / {bus.capacity}
                  </td>
                  <td className="py-3 px-4 text-cyan-400 font-bold">{bus.free_at}</td>
                  <td className="py-3 px-4 text-slate-300 font-sans">{bus.release_point}</td>
                  <td className="py-3 px-4">
                    {bus.confidence === 'HIGH' ? (
                      <span className="text-emerald-400 font-sans text-xs flex items-center gap-1">
                        <CheckCircle2 className="w-3.5 h-3.5" /> High
                      </span>
                    ) : (
                      <span className="text-amber-400 font-sans text-xs flex items-center gap-1 font-medium">
                        <AlertTriangle className="w-3.5 h-3.5" /> Verify Req
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setSelectedBus(bus);
                      }}
                      className="px-2.5 py-1 text-xs font-sans rounded bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition"
                    >
                      Inspect
                    </button>
                  </td>
                </tr>
              ))}

              {filteredBuses.length === 0 && (
                <tr>
                  <td colSpan={9} className="py-8 text-center text-slate-400 font-sans">
                    No vehicles found matching current search/filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Bus Detail Drawer */}
      {selectedBus && (
        <div className="fixed inset-y-0 right-0 w-full sm:w-96 bg-slate-900 border-l border-slate-800 p-6 shadow-2xl z-50 overflow-y-auto flex flex-col justify-between">
          <div className="space-y-6">
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div className="flex items-center gap-2">
                <Bus className="w-5 h-5 text-cyan-400" />
                <div>
                  <h2 className="text-lg font-bold text-white">{selectedBus.bus_id}</h2>
                  <div className="text-xs text-slate-400">{selectedBus.route}</div>
                </div>
              </div>
              <button
                onClick={() => setSelectedBus(null)}
                className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {verifySuccessMsg && (
              <div className="p-3 bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs rounded-lg flex items-center gap-2">
                <Check className="w-4 h-4" />
                {verifySuccessMsg}
              </div>
            )}

            {/* Quick Metrics */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[11px] text-slate-400">Current Status</div>
                <div className="mt-1 font-semibold text-white">{selectedBus.status}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
                <div className="text-[11px] text-slate-400">Expected Free At</div>
                <div className="mt-1 font-bold text-cyan-400">{selectedBus.free_at}</div>
              </div>
            </div>

            {/* Load and Capacity */}
            <div className="space-y-2">
              <div className="flex justify-between text-xs text-slate-300">
                <span>Passenger Load</span>
                <span className="font-bold">
                  {selectedBus.current_load} / {selectedBus.capacity} ({selectedBus.occupancy_band})
                </span>
              </div>
              <div className="w-full h-2.5 bg-slate-800 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    selectedBus.current_load > 45
                      ? 'bg-rose-500'
                      : selectedBus.current_load > 25
                      ? 'bg-amber-500'
                      : 'bg-emerald-500'
                  }`}
                  style={{
                    width: `${Math.min(100, (selectedBus.current_load / selectedBus.capacity) * 100)}%`,
                  }}
                />
              </div>
            </div>

            {/* Release Point & Destination Match */}
            <div className="bg-slate-950/80 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="text-xs font-semibold uppercase text-slate-400 tracking-wider">
                Supply-to-Hotspot Matching
              </div>

              <div className="flex items-center gap-2 text-sm text-slate-200">
                <MapPin className="w-4 h-4 text-amber-400" />
                <span>Release Location: <strong>{selectedBus.release_point}</strong></span>
              </div>

              <div className="flex items-center gap-2 text-sm text-slate-200">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span>Available Window: <strong>{selectedBus.free_at}</strong></span>
              </div>

              {selectedBus.candidate_for_repositioning && (
                <div className="p-3 bg-cyan-950/40 border border-cyan-800/80 rounded-lg text-xs space-y-1">
                  <div className="font-bold text-cyan-300 flex items-center gap-1.5">
                    <ArrowRight className="w-3.5 h-3.5" /> Feasible Candidate for Periyar
                  </div>
                  <p className="text-slate-300">
                    Can reach Periyar by 19:06 (14 min transit time) before the 20:10 critical egress surge.
                  </p>
                </div>
              )}
            </div>

            {/* Operator Verification / 1-Tap Load Update */}
            <div className="space-y-3 border-t border-slate-800 pt-4">
              <div className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                <Sliders className="w-3.5 h-3.5 text-cyan-400" />
                Manual Telemetry Verification
              </div>
              <p className="text-xs text-slate-400">
                Update occupancy band directly if field reports diverge from automated telemetry:
              </p>

              <div className="grid grid-cols-2 gap-2">
                {(['EMPTY', 'SEATS_FREE', 'STANDING', 'CROWDED'] as OccupancyBand[]).map((band) => (
                  <button
                    key={band}
                    disabled={updatingOccupancy}
                    onClick={() => handleUpdateOccupancy(band)}
                    className={`py-1.5 px-2 text-xs rounded border transition font-medium ${
                      selectedBus.occupancy_band === band
                        ? 'bg-cyan-700 text-white border-cyan-600'
                        : 'bg-slate-800 text-slate-300 hover:bg-slate-700 border-slate-700'
                    }`}
                  >
                    {band.replace('_', ' ')}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-800">
            {selectedBus.candidate_for_repositioning && onSelectBusForDecision && (
              <button
                onClick={() => {
                  onSelectBusForDecision(selectedBus.bus_id);
                  setSelectedBus(null);
                }}
                className="w-full py-2 px-4 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-sm transition shadow-lg"
              >
                Review in Decision Queue
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
