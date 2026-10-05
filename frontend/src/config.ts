// Runtime config for the control-plane API. The bearer token and workspace id
// are supplied by the deployment (ADR-0011); in dev they fall back to the seed
// workspace. Never hard-code a real token here.
export interface AppConfig {
  apiBase: string;
  token: string;
  workspaceId: string;
}

const LS_TOKEN = 'adtm.token';
const LS_WS = 'adtm.workspace';

function fromStore(key: string): string | null {
  try {
    return typeof localStorage !== 'undefined' ? localStorage.getItem(key) : null;
  } catch {
    return null;
  }
}

export function getConfig(): AppConfig {
  const env = import.meta.env;
  return {
    apiBase: env.VITE_API_BASE || '/api',
    token: fromStore(LS_TOKEN) || env.VITE_ADTM_TOKEN || 'dev-token',
    workspaceId:
      fromStore(LS_WS) || env.VITE_ADTM_WORKSPACE || '00000000-0000-0000-0000-000000000001',
  };
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(LS_TOKEN, token);
  } catch {
    /* ignore */
  }
}
