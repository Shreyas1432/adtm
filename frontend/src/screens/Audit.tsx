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
import type { AuditVerify } from '../api/types';
import { useAsync } from '../hooks/useAsync';
import { sampleAuditLog } from '../data/sample';
import { StatusChip } from '../components/StatusChip';
import { Loading } from '../components/StateViews';
import { PageHeader, Mono, SectionCard } from '../components/ui';
import { FlowNav } from '../components/FlowNav';
import { tokens } from '../theme';

// Wired to GET /audit/verify. The audit log table is sample data until a list
// endpoint exists; the verification result is live.
export function Audit() {
  const { data, loading, error, reload } = useAsync<AuditVerify>(() => api.verifyAudit(), []);
  const verified = data?.ok === true;

  return (
    <>
      <PageHeader
        title="Audit"
        subtitle="hash-chained, append-only (ADR-0008)"
        actions={
          <Button variant="contained" onClick={reload}>
            Verify chain
          </Button>
        }
      />

      <SectionCard title="Chain verification">
        <Box sx={{ p: 2 }}>
          {loading && <Loading label="Verifying chain" />}
          {!loading && error && (
            <Alert severity="warning">
              Could not verify the chain ({error.message}). The endpoint needs a running
              control plane with a persisted run.
            </Alert>
          )}
          {!loading && !error && data && (
            <>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, mb: 1.5 }}>
                <Box
                  sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: verified ? tokens.success : tokens.danger,
                  }}
                />
                <Typography sx={{ fontSize: 20, fontWeight: 700, color: verified ? tokens.success : tokens.danger }}>
                  {verified ? 'Chain verified' : 'Chain broken'}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {data.count} entries, workspace dev-workspace
                </Typography>
              </Box>
              <Paper variant="outlined" sx={{ p: 1.5, bgcolor: tokens.bg }}>
                <Mono>
                  GET /audit/verify {'->'} {JSON.stringify(data)}
                </Mono>
              </Paper>
            </>
          )}
        </Box>
      </SectionCard>

      <SectionCard title="Audit log (preview)">
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>#</TableCell>
              <TableCell>Action</TableCell>
              <TableCell>Object</TableCell>
              <TableCell>Actor</TableCell>
              <TableCell>hash (sha256)</TableCell>
              <TableCell>at (UTC)</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sampleAuditLog.map((r) => (
              <TableRow key={r.n} hover>
                <TableCell>
                  <Mono color="#3A3F4B">{r.n}</Mono>
                </TableCell>
                <TableCell>
                  <StatusChip label={r.action} kind="info" />
                </TableCell>
                <TableCell>
                  <Mono color="#3A3F4B">{r.object}</Mono>
                </TableCell>
                <TableCell>{r.actor}</TableCell>
                <TableCell>
                  <Mono>{r.hash}</Mono>
                </TableCell>
                <TableCell>
                  <Mono color="#555B66">{r.at}</Mono>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </SectionCard>

      <FlowNav />
    </>
  );
}
