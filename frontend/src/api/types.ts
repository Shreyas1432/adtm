// Control-plane API shapes (subset in use by Phase 1 screens).

export type Encryption = 'none' | 'aead' | 'aead_blind_index';

export interface Column {
  name: string;
  type: string;
  length?: string | number | null;
  nullable?: boolean;
  pk?: boolean;
  description?: string | null;
  encryption: Encryption;
}

export interface Workspace {
  id: string;
  name: string;
  created_at?: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
}

export interface Job {
  id: string;
  job_type: string;
  status: string;
  attempt: number;
  created_at?: string;
}

export interface Health {
  status: string;
  db: string;
}

export interface AuditVerify {
  ok: boolean;
  count: number;
}

export interface AuditEntry {
  id: number;
  action: string;
  object_ref: string | null;
  actor: string | null;
  hash: string;
  created_at?: string | null;
}

export interface DqResult {
  id: string;
  run_id: string;
  rule_type: string;
  params: Record<string, unknown>;
  passed: number;
  failed: number;
  sample: unknown;
  created_at?: string | null;
}
