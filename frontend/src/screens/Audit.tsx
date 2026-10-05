import {
  Alert,
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { api } from '../api/client';
import type { AuditEntry, AuditVerify } from '../api/types';
import { useAsync } from '../hooks/useAsync';
import { sampleAuditLog } from '../data/sample';
import { StatusChip } from '../components/StatusChip';
import { Loading } from '../components/StateViews';
import { PageHeader, Mono, SectionCard } from '../components/ui';
import { FlowNav } from '../components/FlowNav';
import { tokens } from '../theme';

interface Row {
  id: number | string;
  action: string;
  object: string;
  actor: string;
  hash: string;
  at: string;
}

const fromLive = (e: AuditEntry): Row => ({
  id: e.id,
  action: e.action,
  object: e.object_ref ?? '',
  actor: e.actor ?? '',
  hash: e.hash,
  at: e.created_at ?? '',
});

const sampleRows: Row[] = sampleAuditLog.map((e) => ({
  id: e.n,
  action: e.action,
  object: e.object,
  actor: e.actor,
  hash: e.hash,
  at: e.at,
}));

// Both the verification result (GET /audit/verify) and the log (GET /audit) are
// live; the log falls back to sample data when the control plane is unreachable.
export function Audit() {
  const verify = useAsync<AuditVerify>(() => api.verifyAudit(), []);
  const log = useAsync<AuditEntry[]>(() => api.auditLog(50), []);
  const ok = verify.data?.ok === true;

  const live = !!log.data && log.data.length > 0;
  const rows: Row[] = live ? log.data!.map(fromLive) : sampleRows;

  return (
    <>
      <PageHeader
        title="Audit"
        subtitle="hash-chained, append-only (ADR-0008)"
        actions={
          <Button variant="contained" onClick={() => { verify.reload(); log.reload(); }}>
            Verify chain
          </Button>
        }
      />

      <SectionCard title="Chain verification">
        <Box sx={{ p: 2 }}>
          {verify.loading && <Loading label="Verifying chain" />}
          {!verify.loading && verify.error && (
            <Alert severity="warning">
              Could not verify the chain ({verify.error.message}). The endpoint needs a running
              control plane with a persisted run.
            </Alert>
          )}
          {!verify.loading && !verify.error && verify.data && (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.5 }}>
                <Box sx={{ width: 12, height: 12, borderRadius: '50%', bgcolor: ok ? tokens.success : tokens.danger }} />
                <Typography sx={{ fontSize: 20, fontWeight: 700, color: ok ? tokens.success : tokens.danger }}>
                  {ok ? 'Chain verified' : 'Chain broken'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {verify.data.count} entries, workspace dev-workspace
                </Typography>
              </Box>
              <Paper variant="outlined" sx={{ p: 1.5, bgcolor: tokens.bg }}>
                <Mono>GET /audit/verify {'->'} {JSON.stringify(verify.data)}</Mono>
              </Paper>
            </>
          )}
        </Box>
      </SectionCard>

      <SectionCard title={live ? 'Audit log' : 'Audit log (preview)'}>
        {log.loading && <Loading label="Loading audit log" />}
        {!log.loading && (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>#</TableCell>
                <TableCell>Action</TableCell>
                <TableCell>Object</TableCell>
                <TableCell>Actor</TableCell>
                <TableCell>hash (sha256)</TableCell>
                <TableCell>at</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {rows.map((r) => (
                <TableRow key={r.id} hover>
                  <TableCell><Mono color="#3A3F4B">{r.id}</Mono></TableCell>
                  <TableCell><StatusChip label={r.action} kind="info" /></TableCell>
                  <TableCell><Mono color="#3A3F4B">{r.object}</Mono></TableCell>
                  <TableCell>{r.actor}</TableCell>
                  <TableCell><Mono>{r.hash}</Mono></TableCell>
                  <TableCell><Mono color="#555B66">{r.at}</Mono></TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </SectionCard>

      <FlowNav />
    </>
  );
}
