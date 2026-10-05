// Thin fetch client for the ADTM control plane. Every request carries the
// bearer token (ADR-0011); /health is open but sending the header is harmless.
import { getConfig } from '../config';
import type { AuditVerify, Column, Health, Job, Project, Workspace } from './types';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const { apiBase, token } = getConfig();
  const res = await fetch(apiBase + path, {
    ...init,
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/json',
      ...(init?.headers || {}),
    },
  });
  if (!res.ok) {
    throw new ApiError(res.status, `${res.status} ${res.statusText}`);
  }
  return res.status === 204 ? (undefined as T) : (res.json() as Promise<T>);
}

export const api = {
  health: () => req<Health>('/health'),
  workspaces: () => req<Workspace[]>('/workspaces'),
  projects: () => req<Project[]>('/projects'),
  jobs: () => req<Job[]>('/jobs'),
  tables: (connectionId: string) => req<string[]>(`/connections/${connectionId}/tables`),
  columns: (connectionId: string, table: string) =>
    req<Column[]>(`/connections/${connectionId}/tables/${table}/columns`),
  testConnection: (connectionId: string) =>
    req<{ ok: boolean }>(`/connections/${connectionId}/test`, { method: 'POST' }),
  verifyAudit: () => req<AuditVerify>('/audit/verify'),
};
