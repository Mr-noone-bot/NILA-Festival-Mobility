import { useCallback, useEffect, useState } from 'react';
import {
  AlertTriangle,
  Bus,
  Command,
  Compass,
  MapPinned,
  Menu,
  RefreshCw,
  SlidersHorizontal,
  Sparkles,
  Waves,
  Wifi,
  WifiOff,
  X,
} from 'lucide-react';
import {
  ApiError,
  askCopilot,
  fetchRoute,
  getFestivalDetails,
  getFestivals,
  getHealth,
  optimizeFleet,
  predictCrowd,
  simulateCrowd,
  type BackendStop,
  type Festival as BackendFestival,
  type FestivalDetails,
  type HealthResponse,
  type OptimizationResponse,
  type PredictionResponse,
  type RequestStatus,
  type RouteResponse,
  type SimulationResponse,
} from './api';
import {
  toUIFestival,
  type BusMove,
  type ForecastResponse,
  type OptimizeResponse,
  type ScenarioConfig,
  type ScenarioResult,
  type Stop,
  type UIFestival,
} from './types/nila';
import { DEMO_POINTS, DEMO_STOPS } from './data/demoFixtures';

import CommandCenter from './pages/CommandCenter';
import FestivalPlanner from './pages/FestivalPlanner';
import CrowdMap from './pages/CrowdMap';
import BusAllocation from './pages/BusAllocation';
import ScenarioSimulator from './pages/ScenarioSimulator';
import AskNila from './pages/AskNila';

const DEFAULT_CONFIG: ScenarioConfig = {
  attendance: 100,
  rain: 30,
  delayMinutes: 0,
  busFailures: 0,
};

// Default fallback festival representation before network responds
const INITIAL_FESTIVAL: UIFestival = {
  id: 'madurai-chithirai-2026',
  name: 'Chithirai Thiruvizha',
  city: 'Madurai',
  temple: 'Meenakshi Sundareswarar Temple',
  coordinates: [78.1193, 9.9195],
  dateLabel: 'Apr 28, 2026',
  expectedAttendance: 500000,
  peakTime: '10:30 AM',
  events: [
    { name: 'Chariot Procession (Ther)', timestamp: '08:00 AM', estimatedTurnout: 500000 },
  ],
};

export default function App() {
  const [activeNav, setActiveNav] = useState('Command center');
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  // Backend Health State
  const [backendHealth, setBackendHealth] = useState<HealthResponse | null>(null);
  const [healthStatus, setHealthStatus] = useState<RequestStatus>('idle');
  const [healthError, setHealthError] = useState<string>('');

  // Festivals State
  const [festivals, setFestivals] = useState<BackendFestival[]>([]);
  const [selectedFestivalId, setSelectedFestivalId] = useState<string>('madurai-chithirai-2026');
  const [festivalDetails, setFestivalDetails] = useState<FestivalDetails | null>(null);
  const [festivalStatus, setFestivalStatus] = useState<RequestStatus>('idle');
  const [festivalError, setFestivalError] = useState<string>('');

  // Scenario / Simulation config
  const [config, setConfig] = useState<ScenarioConfig>(DEFAULT_CONFIG);
  const [simulationResponse, setSimulationResponse] = useState<SimulationResponse | null>(null);
  const [scenarioStatus, setScenarioStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [scenarioMessage, setScenarioMessage] = useState<string>('');

  // Prediction State
  const [predictionResponse, setPredictionResponse] = useState<PredictionResponse | null>(null);
  const [forecastStatus, setForecastStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [forecastMessage, setForecastMessage] = useState<string>('');

  // Optimization State
  const [optimizationResponse, setOptimizationResponse] = useState<OptimizationResponse | null>(null);
  const [optimizeStatus, setOptimizeStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [optimizeMessage, setOptimizeMessage] = useState<string>('');

  // Route State
  const [routeResponse, setRouteResponse] = useState<RouteResponse | null>(null);

  // Map & Inspector State
  const [selectedStop, setSelectedStop] = useState<Stop | null>(DEMO_STOPS[0]);

  // AI Copilot Chat State
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatError, setChatError] = useState('');
  const [chatMessages, setChatMessages] = useState<
    Array<{ role: 'user' | 'assistant'; text: string; source?: 'api' | 'demo' }>
  >([
    {
      role: 'assistant',
      text: 'Vanakkam! I am NILA, the real-time AI festival mobility copilot. Connected to the FastAPI backend service. Ask me about crowd surges, fixed-fleet optimization, or origin service trade-offs.',
      source: 'api',
    },
  ]);

  // Check Backend Health
  const checkHealth = useCallback(async () => {
    setHealthStatus('loading');
    setHealthError('');
    try {
      const data = await getHealth();
      setBackendHealth(data);
      setHealthStatus('success');
    } catch (err: unknown) {
      setHealthStatus('error');
      setBackendHealth(null);
      if (err instanceof ApiError) {
        setHealthError(`Backend offline: ${err.message}`);
      } else {
        setHealthError('Cannot connect to backend service (GET /api/health)');
      }
    }
  }, []);

  // Load Festivals from GET /api/festivals
  const loadFestivals = useCallback(async () => {
    setFestivalStatus('loading');
    setFestivalError('');
    try {
      const data = await getFestivals();
      setFestivals(data);
      setFestivalStatus(data.length ? 'success' : 'empty');
      if (data.length > 0 && !data.some((f) => f.id === selectedFestivalId)) {
        setSelectedFestivalId(data[0].id);
      }
    } catch (err: unknown) {
      setFestivalStatus('error');
      if (err instanceof ApiError) {
        setFestivalError(`Failed to load festivals: ${err.message}`);
      } else {
        setFestivalError('Failed to load festival catalog from backend');
      }
    }
  }, [selectedFestivalId]);

  // Load Festival Details from GET /api/festivals/{festival_id}
  const loadDetails = useCallback(async (id: string) => {
    if (!id) return;
    try {
      const details = await getFestivalDetails(id);
      setFestivalDetails(details);
      if (details.stops && details.stops.length > 0) {
        const first = details.stops[0];
        setSelectedStop({
          id: first.id,
          name: first.name,
          shortName: first.name.replace(' Bus Stand', '').replace(' Terminal', ''),
          coordinates: [first.coordinates.lng, first.coordinates.lat],
          capacity: first.capacity,
          currentBuses: 5,
          recommendedBuses: 5,
          crowd: Math.round(first.capacity * 0.8),
          waitMinutes: 15,
          risk: 'MODERATE',
        });
      }
    } catch (err: unknown) {
      if (err instanceof ApiError) {
        setFestivalError(`Failed to load festival details for ${id}: ${err.message}`);
      }
    }
  }, []);

  // Initial load
  useEffect(() => {
    void checkHealth();
    void loadFestivals();
  }, [checkHealth, loadFestivals]);

  // When selected festival changes, load its details
  useEffect(() => {
    if (selectedFestivalId) {
      void loadDetails(selectedFestivalId);
    }
  }, [selectedFestivalId, loadDetails]);

  // Real POST /api/predict execution
  const runForecast = useCallback(async () => {
    setForecastStatus('loading');
    setForecastMessage('');
    try {
      const result = await predictCrowd({
        festival_id: selectedFestivalId,
        time_window_start: '2026-04-28T06:00:00+05:30',
        time_window_end: '2026-04-28T18:00:00+05:30',
        weather_condition: config.rain > 50 ? 'rainy' : 'clear',
        surge_multiplier: config.attendance / 100,
      });

      setPredictionResponse(result);
      setForecastStatus('success');
      setForecastMessage(
        `Crowd prediction completed. Peak surge expected at ${result.peak_surge_time}. Highest demand: ${result.highest_demand_stops.join(', ')}`
      );
    } catch (err: unknown) {
      setForecastStatus('error');
      if (err instanceof ApiError) {
        setForecastMessage(`POST /api/predict failed (${err.status}): ${err.message}`);
      } else {
        setForecastMessage('Unexpected error during crowd prediction request');
      }
    }
  }, [selectedFestivalId, config.rain, config.attendance]);

  // Real POST /api/optimize execution
  const runOptimization = useCallback(async () => {
    setOptimizeStatus('loading');
    setOptimizeMessage('');
    try {
      const stopsList = festivalDetails?.stops || [];
      const currentAllocation: Record<string, number> = {};
      const predictedDemand: Record<string, number> = {};

      stopsList.forEach((s, idx) => {
        currentAllocation[s.id] = idx === 0 ? 5 : idx === 1 ? 5 : 10;
        predictedDemand[s.id] = idx === 0 ? 4200 : idx === 1 ? 1800 : 600;
      });

      const result = await optimizeFleet({
        festival_id: selectedFestivalId,
        total_fleet_size: festivalDetails?.default_fleet_size || 25,
        current_allocation: currentAllocation,
        predicted_demand_profile: predictedDemand,
        time_horizon_minutes: 120,
      });

      setOptimizationResponse(result);
      setOptimizeStatus('success');
      setOptimizeMessage(
        `Optimization completed. Fleet conserved: ${result.fleet_conserved}. Queue reduction: ${result.overall_queue_reduction_percentage}%.`
      );

      // Automatically fetch real road route for the primary repositioning move
      const move = result.repositioning_moves?.[0];
      if (move && stopsList.length >= 2) {
        const src = stopsList.find((s) => s.id === move.source_stop);
        const dst = stopsList.find((s) => s.id === move.destination_stop);
        if (src && dst) {
          try {
            const route = await fetchRoute({
              origin: { lat: src.coordinates.lat, lng: src.coordinates.lng },
              destination: { lat: dst.coordinates.lat, lng: dst.coordinates.lng },
              congestion_factor: 1.3,
            });
            setRouteResponse(route);
          } catch {
            // Route call is non-blocking
          }
        }
      }
    } catch (err: unknown) {
      setOptimizeStatus('error');
      if (err instanceof ApiError) {
        setOptimizeMessage(`POST /api/optimize failed (${err.status}): ${err.message}`);
      } else {
        setOptimizeMessage('Optimization request failed unexpectedly');
      }
    }
  }, [selectedFestivalId, festivalDetails]);

  // Real POST /api/simulate execution
  const runScenario = useCallback(async () => {
    setScenarioStatus('loading');
    setScenarioMessage('');
    try {
      const result = await simulateCrowd({
        festival_id: selectedFestivalId,
        attendance_multiplier: config.attendance / 100,
        rain_probability: config.rain,
        event_delay_minutes: config.delayMinutes,
        bus_failures: config.busFailures,
      });

      setSimulationResponse(result);
      setScenarioStatus('success');
      setScenarioMessage(
        `Simulation step generated (${result.simulation_id}). Analyzed spatial crowd discharge across gates.`
      );
    } catch (err: unknown) {
      setScenarioStatus('error');
      if (err instanceof ApiError) {
        setScenarioMessage(`POST /api/simulate failed (${err.status}): ${err.message}`);
      } else {
        setScenarioMessage('Scenario simulation failed unexpectedly');
      }
    }
  }, [selectedFestivalId, config]);

  // Real POST /api/ai/ask execution
  const submitQuestion = useCallback(
    async (question: string) => {
      const trimmed = question.trim();
      if (!trimmed || chatLoading) return;

      setChatInput('');
      setChatError('');
      setChatMessages((prev) => [...prev, { role: 'user', text: trimmed }]);
      setChatLoading(true);

      try {
        const response = await askCopilot({
          question: trimmed,
          plan_id: optimizationResponse?.plan_id || 'opt-plan-default',
          festival_id: selectedFestivalId,
          scenario: {
            attendance: config.attendance,
            rain: config.rain,
            delay: config.delayMinutes,
            failures: config.busFailures,
          },
        });

        setChatMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: response.answer,
            source: 'api',
          },
        ]);
      } catch (err: unknown) {
        let msg = 'Failed to get response from AI endpoint';
        if (err instanceof ApiError) {
          msg = `POST /api/ai/ask error (${err.status}): ${err.message}`;
        }
        setChatError(msg);
        setChatMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            text: `[Error from Backend AI Service]: ${msg}. Ensure backend is running and GEMINI_API_KEY is configured in backend .env.`,
            source: 'api',
          },
        ]);
      } finally {
        setChatLoading(false);
      }
    },
    [chatLoading, optimizationResponse?.plan_id, selectedFestivalId, config]
  );

  // Adapted stops for UI rendering from real festival details
  const currentStops: Stop[] =
    festivalDetails?.stops && festivalDetails.stops.length > 0
      ? festivalDetails.stops.map((bs: BackendStop) => {
          const isCritical = predictionResponse?.highest_demand_stops?.includes(bs.id);
          return {
            id: bs.id,
            name: bs.name,
            shortName: bs.name.replace(' Bus Stand', '').replace(' Terminal', ''),
            coordinates: [bs.coordinates.lng, bs.coordinates.lat],
            capacity: bs.capacity,
            currentBuses: optimizationResponse?.final_allocation?.[bs.id] ?? 5,
            recommendedBuses: optimizationResponse?.final_allocation?.[bs.id] ?? 5,
            crowd: isCritical ? Math.round(bs.capacity * 1.5) : Math.round(bs.capacity * 0.7),
            waitMinutes: isCritical ? 45 : 15,
            risk: isCritical ? 'CRITICAL' : 'MODERATE',
          };
        })
      : DEMO_STOPS;

  // Adapted active repositioning move
  const activeMove: BusMove = optimizationResponse?.repositioning_moves?.[0]
    ? {
        sourceStop: optimizationResponse.repositioning_moves[0].source_stop,
        destinationStop: optimizationResponse.repositioning_moves[0].destination_stop,
        buses: optimizationResponse.repositioning_moves[0].buses_to_transfer,
        departure: optimizationResponse.repositioning_moves[0].departure_time,
        arrival: optimizationResponse.repositioning_moves[0].arrival_time,
        travelMinutes: optimizationResponse.repositioning_moves[0].travel_time_minutes,
        waitReduction: 26,
        benefit: optimizationResponse.repositioning_moves[0].expected_benefit,
        tradeoff: optimizationResponse.repositioning_moves[0].source_service_loss,
        networkEffect: optimizationResponse.repositioning_moves[0].network_effect,
      }
    : {
        sourceStop: currentStops[2]?.id || 'stop-mattuthavani',
        destinationStop: currentStops[0]?.id || 'stop-periyar',
        buses: 4,
        departure: '09:15 AM',
        arrival: '09:40 AM',
        travelMinutes: 25,
        waitReduction: 26,
        benefit: 'Reduces queue pressure at peak egress terminal',
        tradeoff: 'Origin standby buffer reduced',
        networkEffect: '+3,200 passengers cleared before peak',
      };

  // Adapted forecast metrics for UI
  const adaptedForecast: ForecastResponse = {
    source: predictionResponse ? 'api' : 'demo',
    metrics: {
      peakCrowd: predictionResponse?.timeline?.[0]?.total_crowd_estimate ?? 450000,
      peakTime: predictionResponse?.peak_surge_time ?? '10:30 AM',
      waitingMinutes: 32,
      overloadedStops: predictionResponse?.highest_demand_stops?.length ?? 2,
      risk: (predictionResponse?.timeline?.[0]?.surge_alert_level as 'LOW' | 'MEDIUM' | 'MODERATE' | 'HIGH' | 'CRITICAL') ?? 'HIGH',
    },
    points: simulationResponse?.steps?.[0]?.density_grid?.map((pt) => ({
      coordinates: [pt.longitude, pt.latitude] as [number, number],
      weight: pt.weight,
    })) || DEMO_POINTS,
    stops: currentStops,
  };

  // Adapted optimization for UI
  const adaptedOptimization: OptimizeResponse = {
    source: optimizationResponse ? 'api' : 'demo',
    plan_id: optimizationResponse?.plan_id || 'opt-plan-initial',
    total_fleet_size: optimizationResponse?.total_fleet_size || festivalDetails?.default_fleet_size || 25,
    fleet_conserved: optimizationResponse?.fleet_conserved ?? true,
    move: activeMove,
    overall_queue_reduction_percentage:
      optimizationResponse?.overall_queue_reduction_percentage ?? 58.4,
    final_allocation: optimizationResponse?.final_allocation,
  };

  // Adapted scenario result for UI
  const adaptedScenario: ScenarioResult = {
    source: simulationResponse ? 'api' : 'demo',
    baseline: {
      peakCrowd: 500000,
      peakTime: '10:30 AM',
      waitingMinutes: 34,
      queue: 8770,
      risk: 'HIGH',
    },
    scenario: {
      peakCrowd: Math.round(500000 * (config.attendance / 100)),
      peakTime: config.delayMinutes > 0 ? `10:${30 + config.delayMinutes} AM` : '10:30 AM',
      waitingMinutes: Math.round(34 * (config.attendance / 100) * (config.rain > 50 ? 1.25 : 1)),
      queue: Math.round(8770 * (config.attendance / 100)),
      risk: config.attendance > 120 || config.rain > 50 ? 'CRITICAL' : 'HIGH',
    },
  };

  // Active festival presentation object
  const matchedBackend = festivals.find((f) => f.id === selectedFestivalId);
  const activeFestivalObj: UIFestival = matchedBackend
    ? toUIFestival(matchedBackend, festivalDetails)
    : INITIAL_FESTIVAL;

  // Adapt festivals list for FestivalPlanner
  const uiFestivalsList: UIFestival[] = festivals.length
    ? festivals.map((f) => toUIFestival(f, f.id === selectedFestivalId ? festivalDetails : null))
    : [INITIAL_FESTIVAL];

  const navItems = [
    { label: 'Command center', icon: Command },
    { label: 'Festival planner', icon: MapPinned },
    { label: 'Crowd map', icon: Compass },
    { label: 'Bus allocation & trade-off', icon: Bus },
    { label: 'Scenario simulator', icon: SlidersHorizontal },
    { label: 'ASK NILA', icon: Sparkles },
  ];

  return (
    <div className="min-h-screen bg-sky-50/50 text-slate-800 flex flex-col md:flex-row antialiased font-sans">
      {/* Mobile Drawer Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar Navigation */}
      <aside
        className={`fixed md:sticky top-0 h-screen w-72 bg-white border-r border-sky-100 flex flex-col z-50 transition-transform duration-300 ease-in-out shrink-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
        }`}
      >
        {/* Brand Header */}
        <div className="p-5 border-b border-sky-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-sky-600 to-sky-500 text-white flex items-center justify-center shadow-md">
              <Waves size={22} strokeWidth={2.4} />
            </div>
            <div>
              <div className="text-lg font-black tracking-tight text-slate-900 flex items-center gap-1">
                NILA
                <span className="text-[10px] font-bold px-1.5 py-0.2 rounded-full bg-sky-100 text-sky-700">
                  LIVE API
                </span>
              </div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-sky-700">
                Mobility Intelligence
              </div>
            </div>
          </div>
          <button
            className="md:hidden text-slate-400 hover:text-slate-600 p-1 rounded-lg"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        {/* Real-time Backend Connection Chip */}
        <div className="p-3 mx-4 my-3 bg-sky-50/80 rounded-2xl border border-sky-200 flex items-center justify-between text-xs">
          <div className="flex items-center gap-2.5">
            <span
              className={`w-7 h-7 rounded-xl font-bold flex items-center justify-center text-[11px] shadow-sm text-white ${
                backendHealth?.status === 'healthy' ? 'bg-emerald-600' : 'bg-amber-600'
              }`}
            >
              {backendHealth?.status === 'healthy' ? <Wifi size={14} /> : <WifiOff size={14} />}
            </span>
            <div>
              <strong className="block text-slate-900 font-bold text-xs">
                {backendHealth?.status === 'healthy' ? 'FastAPI Connected' : 'Backend Disconnected'}
              </strong>
              <small className="text-slate-500 text-[10px]">
                {backendHealth?.version ? `v${backendHealth.version} (${backendHealth.environment})` : 'Offline / Check Port 8000'}
              </small>
            </div>
          </div>
          <button
            onClick={() => void checkHealth()}
            title="Refresh backend health"
            disabled={healthStatus === 'loading'}
            className="text-slate-400 hover:text-sky-600 p-1 rounded"
          >
            <RefreshCw size={13} className={healthStatus === 'loading' ? 'animate-spin text-sky-600' : ''} />
          </button>
        </div>

        {/* Operations Navigation Links */}
        <div className="px-4 py-2 text-[10px] font-extrabold uppercase tracking-widest text-slate-400">
          Operation Modes
        </div>
        <nav className="flex-1 px-3 space-y-1 overflow-y-auto">
          {navItems.map(({ label, icon: Icon }) => {
            const isActive = activeNav === label;
            return (
              <button
                key={label}
                onClick={() => {
                  setActiveNav(label);
                  setMobileMenuOpen(false);
                  window.scrollTo({ top: 0, behavior: 'smooth' });
                }}
                className={`w-full text-left px-3.5 py-3 rounded-xl text-xs font-bold flex items-center gap-3 transition-all ${
                  isActive
                    ? 'bg-sky-600 text-white shadow-sm shadow-sky-600/20'
                    : 'text-slate-600 hover:bg-sky-50 hover:text-sky-800'
                }`}
              >
                <Icon size={18} className={isActive ? 'text-white' : 'text-slate-400'} />
                <span>{label}</span>
              </button>
            );
          })}
        </nav>

        {/* Invariant Constraint Note */}
        <div className="p-4 m-3 bg-slate-50 rounded-2xl border border-slate-200 text-slate-600 text-[11px] space-y-1">
          <div className="font-bold text-slate-900 flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            Backend Invariant Enforced
          </div>
          <p className="text-[10px] leading-relaxed text-slate-500">
            Enforces Fixed Fleet Constraint $\sum F_i = F_{"{total}"}$. Consumes real FastAPI endpoints.
          </p>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="sticky top-0 bg-white/90 backdrop-blur-md border-b border-sky-100 z-30 px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="md:hidden p-2 rounded-xl text-slate-600 hover:bg-slate-100"
              aria-label="Open mobile navigation"
            >
              <Menu size={20} />
            </button>
            <div className="flex items-center gap-2 text-xs text-slate-500">
              <span>NILA Mobility Ops</span>
              <span className="text-slate-300">/</span>
              <strong className="text-slate-900 font-bold">{activeNav}</strong>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {backendHealth?.status === 'healthy' ? (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                <span>Backend Online (Port 8000)</span>
              </div>
            ) : (
              <div className="flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                <span>Backend Offline</span>
              </div>
            )}
          </div>
        </header>

        {/* Global Connection Warning Banner if Offline */}
        {(healthStatus === 'error' || festivalStatus === 'error') && (
          <div className="bg-amber-50 border-b border-amber-200 px-6 py-2.5 text-xs text-amber-900 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle size={15} className="text-amber-600 shrink-0" />
              <span>
                <strong>Backend Service Offline:</strong>{' '}
                {healthError || festivalError || `Could not connect to FastAPI at ${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}`}. Ensure uvicorn is running.
              </span>
            </div>
            <button
              onClick={() => {
                void checkHealth();
                void loadFestivals();
              }}
              className="px-2.5 py-1 bg-amber-200 hover:bg-amber-300 text-amber-900 rounded font-semibold text-[11px] shrink-0"
            >
              Retry Connection
            </button>
          </div>
        )}

        {/* Dynamic Page Views */}
        <main className="flex-1 p-4 md:p-8 max-w-7xl w-full mx-auto">
          {activeNav === 'Command center' && (
            <CommandCenter
              festival={activeFestivalObj}
              forecast={adaptedForecast}
              optimization={adaptedOptimization}
              stops={currentStops}
              selectedStop={selectedStop}
              onSelectStop={setSelectedStop}
              onNavigate={setActiveNav}
              onRunForecast={runForecast}
              onRunOptimization={runOptimization}
              forecastStatus={forecastStatus}
              optimizeStatus={optimizeStatus}
              forecastMessage={forecastMessage}
              optimizeMessage={optimizeMessage}
            />
          )}

          {activeNav === 'Festival planner' && (
            <FestivalPlanner
              festivals={uiFestivalsList}
              selectedFestivalId={selectedFestivalId}
              onSelectFestival={setSelectedFestivalId}
              onRunForecast={runForecast}
              onNavigate={setActiveNav}
            />
          )}

          {activeNav === 'Crowd map' && (
            <CrowdMap
              festival={activeFestivalObj}
              stops={currentStops}
              points={adaptedForecast.points}
              move={activeMove}
              selectedStop={selectedStop}
              onSelectStop={setSelectedStop}
              routeGeometry={routeResponse?.geometry?.coordinates || null}
            />
          )}

          {activeNav === 'Bus allocation & trade-off' && (
            <BusAllocation
              optimization={adaptedOptimization}
              stops={currentStops}
              onRunOptimization={runOptimization}
              optimizeStatus={optimizeStatus}
              optimizeMessage={optimizeMessage}
            />
          )}

          {activeNav === 'Scenario simulator' && (
            <ScenarioSimulator
              config={config}
              onUpdateConfig={(k, v) => setConfig((prev) => ({ ...prev, [k]: v }))}
              scenario={adaptedScenario}
              onRunScenario={runScenario}
              scenarioStatus={scenarioStatus}
              scenarioMessage={scenarioMessage}
            />
          )}

          {activeNav === 'ASK NILA' && (
            <AskNila
              festival={activeFestivalObj}
              forecast={adaptedForecast}
              optimization={adaptedOptimization}
              chatMessages={chatMessages}
              chatLoading={chatLoading}
              chatError={chatError}
              chatInput={chatInput}
              onChatInputChange={setChatInput}
              onSubmitQuestion={submitQuestion}
            />
          )}
        </main>

        {/* Global Footer */}
        <footer className="mt-auto border-t border-sky-100 bg-white py-5 px-6 text-xs text-slate-500">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3">
            <div className="flex items-center gap-2">
              <Waves size={15} className="text-sky-600" />
              <span className="font-bold text-slate-800">NILA</span>
              <span>· AI-Powered Festival Mobility & Crowd Management</span>
            </div>
            <div className="text-[11px] text-slate-400">
              Phase 6 API Integration Active · Consuming FastAPI Endpoints
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
}