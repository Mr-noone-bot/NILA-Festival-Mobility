/**
 * Compatibility bridge re-exporting real API clients from src/api/
 * Ensures zero fake data, connecting directly to FastAPI backend.
 */
export * from '../api';
export {
  getFestivals,
  getFestivalDetails,
  getHealth,
} from '../api/festivals';
export { predictCrowd, predictCrowd as predictForecast } from '../api/prediction';
export { optimizeFleet, optimizeFleet as optimizeTransport } from '../api/optimization';
export { simulateCrowd, simulateCrowd as simulateScenario } from '../api/simulation';
export { fetchRoute, fetchRoute as getRoute } from '../api/routes';
export { askCopilot, askCopilot as askNila } from '../api/ai';
