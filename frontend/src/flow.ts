// The Suppliers migration flow. Drives both the nav rail and the stepper so the
// screens read as one journey, not isolated states.
export interface Step {
  key: string;
  label: string;
  path: string;
}

export const steps: Step[] = [
  { key: 'connections', label: 'Connections', path: '/connections' },
  { key: 'discovery', label: 'Schema Discovery', path: '/discovery' },
  { key: 'extraction', label: 'Extraction', path: '/extraction' },
  { key: 'dq', label: 'Data Quality', path: '/dq' },
  { key: 'mapping', label: 'Mapping', path: '/mapping' },
  { key: 'load', label: 'Load & Reconciliation', path: '/load' },
  { key: 'audit', label: 'Audit', path: '/audit' },
];

export function stepIndex(path: string): number {
  const i = steps.findIndex((s) => path.startsWith(s.path));
  return i < 0 ? 0 : i;
}
