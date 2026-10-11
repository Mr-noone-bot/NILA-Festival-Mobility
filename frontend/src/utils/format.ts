import type { RiskLevel } from '../types/nila';

export function formatNumber(val: number | undefined | null): string {
  if (val === undefined || val === null || isNaN(val)) return '0';
  return new Intl.NumberFormat('en-IN').format(Math.round(val));
}

export function riskLabel(risk: RiskLevel | string | undefined | null): string {
  if (!risk) return 'Unknown';
  switch (risk.toUpperCase()) {
    case 'CRITICAL':
      return 'Critical';
    case 'HIGH':
      return 'High';
    case 'MODERATE':
    case 'MEDIUM':
      return 'Moderate';
    case 'LOW':
      return 'Low';
    default:
      return risk;
  }
}

export function toRiskClass(risk: RiskLevel | string | undefined | null): string {
  if (!risk) return 'risk-moderate';
  switch (risk.toUpperCase()) {
    case 'CRITICAL':
      return 'risk-critical';
    case 'HIGH':
      return 'risk-high';
    case 'MODERATE':
    case 'MEDIUM':
      return 'risk-moderate';
    case 'LOW':
      return 'risk-low';
    default:
      return 'risk-moderate';
  }
}

export function scenarioIsValid(
  attendance: number,
  rain: number,
  delayMinutes: number,
  busFailures: number
): boolean {
  const validAttendance = [100, 120, 150].includes(attendance);
  const validRain = [0, 30, 60, 90].includes(rain);
  const validDelay = [0, 15, 30, 45].includes(delayMinutes);
  const validFailures = [0, 1, 2].includes(busFailures);
  return validAttendance && validRain && validDelay && validFailures;
}
