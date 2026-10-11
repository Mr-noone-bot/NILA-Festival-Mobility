import type {
  CrowdPoint,
  Festival,
  OptimizeResponse,
  ScenarioConfig,
  ScenarioResult,
  Stop,
} from '../types/nila';

export const DEMO_FESTIVALS: Festival[] = [
  {
    id: 'madurai-chithirai-2026',
    name: 'Chithirai Thiruvizha',
    city: 'Madurai',
    temple: 'Meenakshi Sundareswarar Temple',
    coordinates: [78.1193, 9.9195], // [lng, lat]
    dateLabel: 'Apr 28, 2026 · Chariot Procession',
    expectedAttendance: 500000,
    peakTime: '10:30 AM',
    events: [
      { name: 'Kodi Yetram (Flag Hoisting)', timestamp: '06:00 AM', estimatedTurnout: 85000 },
      { name: 'Meenakshi Pattabhishekam', timestamp: '07:30 PM', estimatedTurnout: 140000 },
      { name: 'Thirukalyanam (Celestial Wedding)', timestamp: '08:30 AM', estimatedTurnout: 320000 },
      { name: 'Therottam (Chariot Procession)', timestamp: '06:30 AM', estimatedTurnout: 500000 },
      { name: 'Kallazhagar Vaigai Entry', timestamp: '06:00 AM', estimatedTurnout: 800000 },
    ],
  },
  {
    id: 'tiruvannamalai-karthigai-2026',
    name: 'Karthigai Deepam',
    city: 'Tiruvannamalai',
    temple: 'Arulmigu Arunachaleswarar Temple',
    coordinates: [79.0747, 12.2300],
    dateLabel: 'Nov 23, 2026 · Maha Deepam',
    expectedAttendance: 1200000,
    peakTime: '06:00 PM',
    events: [
      { name: 'Bharani Deepam Lighting', timestamp: '04:00 AM', estimatedTurnout: 250000 },
      { name: 'Maha Deepam Peak Surge', timestamp: '06:00 PM', estimatedTurnout: 1200000 },
      { name: 'Girivalam Mass Egress', timestamp: '08:00 PM', estimatedTurnout: 950000 },
    ],
  },
  {
    id: 'kumbakonam-mahamaham-2026',
    name: 'Mahamaham Festival',
    city: 'Kumbakonam',
    temple: 'Adi Kumbeswarar Temple & Mahamaham Tank',
    coordinates: [79.3770, 10.9577],
    dateLabel: 'Mar 12, 2026 · Theerthavari',
    expectedAttendance: 650000,
    peakTime: '11:45 AM',
    events: [
      { name: 'Theerthavari Holy Bathing', timestamp: '11:00 AM', estimatedTurnout: 650000 },
      { name: 'Kumbeswarar Car Festival', timestamp: '04:00 PM', estimatedTurnout: 310000 },
    ],
  },
  {
    id: 'palani-thaipusam-2026',
    name: 'Thaipusam Festival',
    city: 'Palani',
    temple: 'Dhandayuthapani Swamy Temple',
    coordinates: [77.5167, 10.4500],
    dateLabel: 'Jan 22, 2026 · Thaipusam Day',
    expectedAttendance: 450000,
    peakTime: '09:00 AM',
    events: [
      { name: 'Kavadi Egress Surge', timestamp: '09:00 AM', estimatedTurnout: 450000 },
      { name: 'Silver Chariot Procession', timestamp: '07:00 PM', estimatedTurnout: 280000 },
    ],
  },
];

export const DEMO_STOPS: Stop[] = [
  {
    id: 'stop-periyar',
    name: 'Periyar Bus Stand',
    shortName: 'Periyar Stand',
    coordinates: [78.1132, 9.9167],
    capacity: 1500,
    currentBuses: 5,
    recommendedBuses: 9,
    crowd: 4200,
    waitMinutes: 48,
    risk: 'CRITICAL',
  },
  {
    id: 'stop-aarapalayam',
    name: 'Aarapalayam Bus Stand',
    shortName: 'Aarapalayam',
    coordinates: [78.1064, 9.9326],
    capacity: 1200,
    currentBuses: 5,
    recommendedBuses: 5,
    crowd: 1800,
    waitMinutes: 22,
    risk: 'MODERATE',
  },
  {
    id: 'stop-mattuthavani',
    name: 'Mattuthavani (MIBT Integrated)',
    shortName: 'Mattuthavani',
    coordinates: [78.1561, 9.9482],
    capacity: 3000,
    currentBuses: 10,
    recommendedBuses: 6,
    crowd: 600,
    waitMinutes: 8,
    risk: 'LOW',
  },
  {
    id: 'stop-goripalayam',
    name: 'Goripalayam Junction',
    shortName: 'Goripalayam',
    coordinates: [78.1287, 9.9284],
    capacity: 900,
    currentBuses: 3,
    recommendedBuses: 3,
    crowd: 1450,
    waitMinutes: 28,
    risk: 'HIGH',
  },
  {
    id: 'stop-thiruparankundram',
    name: 'Thiruparankundram Terminal',
    shortName: 'Thiruparankundram',
    coordinates: [78.0712, 9.8785],
    capacity: 800,
    currentBuses: 2,
    recommendedBuses: 2,
    crowd: 720,
    waitMinutes: 14,
    risk: 'LOW',
  },
];

// Dense crowd cluster around Meenakshi Amman Temple & connecting corridors
export const DEMO_POINTS: CrowdPoint[] = [
  { coordinates: [78.1193, 9.9195], weight: 1.0 }, // Temple Center
  { coordinates: [78.1190, 9.9200], weight: 0.95 },
  { coordinates: [78.1198, 9.9190], weight: 0.92 },
  { coordinates: [78.1185, 9.9198], weight: 0.88 },
  { coordinates: [78.1202, 9.9192], weight: 0.86 },
  { coordinates: [78.1170, 9.9180], weight: 0.82 }, // West Veli approach
  { coordinates: [78.1155, 9.9172], weight: 0.89 },
  { coordinates: [78.1140, 9.9168], weight: 0.94 }, // Towards Periyar Stand
  { coordinates: [78.1132, 9.9167], weight: 0.98 }, // Periyar Hub
  { coordinates: [78.1125, 9.9164], weight: 0.85 },
  { coordinates: [78.1160, 9.9230], weight: 0.72 }, // North corridor
  { coordinates: [78.1130, 9.9270], weight: 0.65 },
  { coordinates: [78.1090, 9.9300], weight: 0.68 },
  { coordinates: [78.1064, 9.9326], weight: 0.74 }, // Aarapalayam
  { coordinates: [78.1240, 9.9220], weight: 0.76 }, // East Gate corridor
  { coordinates: [78.1287, 9.9284], weight: 0.79 }, // Goripalayam
  { coordinates: [78.1380, 9.9360], weight: 0.52 }, // Ring road corridor
  { coordinates: [78.1460, 9.9420], weight: 0.45 },
  { coordinates: [78.1561, 9.9482], weight: 0.38 }, // Mattuthavani MIBT
  { coordinates: [78.1100, 9.9100], weight: 0.60 }, // South corridor
  { coordinates: [78.0900, 9.8950], weight: 0.40 },
  { coordinates: [78.0712, 9.8785], weight: 0.32 }, // Thiruparankundram
];

export const DEMO_OPTIMIZATION: OptimizeResponse = {
  source: 'demo',
  plan_id: 'opt-plan-901',
  total_fleet_size: 25,
  fleet_conserved: true,
  overall_queue_reduction_percentage: 58.4,
  move: {
    sourceStop: 'stop-mattuthavani',
    destinationStop: 'stop-periyar',
    buses: 4,
    departure: '09:15 AM',
    arrival: '09:40 AM',
    travelMinutes: 25,
    waitReduction: 26,
    benefit: 'Eliminates critical queue hazard at Periyar (-62% wait time reduction)',
    tradeoff: 'Minor wait time increase at Mattuthavani (+4 min), well within safe buffer',
    networkEffect: '+3,200 passengers cleared before 10:30 AM peak egress',
  },
  final_allocation: {
    'stop-periyar': 9,
    'stop-aarapalayam': 5,
    'stop-mattuthavani': 6,
    'stop-goripalayam': 3,
    'stop-thiruparankundram': 2,
  },
};

export function buildDemoScenario(config: ScenarioConfig): ScenarioResult {
  const attMult = config.attendance / 100;
  const rainPenalty = config.rain > 50 ? 1.25 : config.rain > 0 ? 1.1 : 1.0;
  const delayPenalty = config.delayMinutes > 0 ? 1 + config.delayMinutes / 60 : 1.0;
  const failurePenalty = config.busFailures > 0 ? 1 + config.busFailures * 0.12 : 1.0;

  const combinedFactor = attMult * rainPenalty * delayPenalty * failurePenalty;

  const baselineCrowd = 500000;
  const scenarioCrowd = Math.round(baselineCrowd * attMult);

  const baselineWait = 34;
  const scenarioWait = Math.round(baselineWait * combinedFactor);

  const baselineQueue = 8770;
  const scenarioQueue = Math.round(baselineQueue * combinedFactor);

  let scenarioRisk: 'LOW' | 'MODERATE' | 'HIGH' | 'CRITICAL' = 'MODERATE';
  if (combinedFactor > 1.45 || scenarioWait > 45) {
    scenarioRisk = 'CRITICAL';
  } else if (combinedFactor > 1.2 || scenarioWait > 35) {
    scenarioRisk = 'HIGH';
  } else if (scenarioWait < 20) {
    scenarioRisk = 'LOW';
  }

  // Adjust peak time if delay
  const baseMinutes = 10 * 60 + 30; // 10:30 AM
  const totalMinutes = baseMinutes + config.delayMinutes;
  const hours = Math.floor(totalMinutes / 60);
  const mins = totalMinutes % 60;
  const formattedTime = `${hours % 12 === 0 ? 12 : hours % 12}:${mins.toString().padStart(2, '0')} ${hours >= 12 ? 'PM' : 'AM'}`;

  return {
    source: 'demo',
    baseline: {
      peakCrowd: baselineCrowd,
      peakTime: '10:30 AM',
      waitingMinutes: baselineWait,
      queue: baselineQueue,
      risk: 'HIGH',
    },
    scenario: {
      peakCrowd: scenarioCrowd,
      peakTime: formattedTime,
      waitingMinutes: scenarioWait,
      queue: scenarioQueue,
      risk: scenarioRisk,
    },
  };
}
