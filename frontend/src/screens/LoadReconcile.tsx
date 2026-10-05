import { Alert, Box, Button, Paper } from '@mui/material';
import { sampleReconciliation as r } from '../data/sample';
import { StatusChip } from '../components/StatusChip';
import { PreviewNotice } from '../components/StateViews';
import { PageHeader, Mono, SectionCard, StatTile } from '../components/ui';
import { FlowNav } from '../components/FlowNav';
import { tokens } from '../theme';

const evidence: [string, string, string?][] = [
  ['source_count', '1,284'],
  ['expected_count', '1,281'],
  ['actual_count (read-back)', '1,281', 'ok'],
  ['loaded_count', '1,281'],
  ['failed_count', '3', 'warn'],
  ['unmatched_count', '0'],
  ['evidence_path', 'recon/suppliers/run-1.json'],
];

export function LoadReconcile() {
  return (
    <>
      <PageHeader
        title="Load & Reconciliation"
        subtitle="suppliers, run-1, Fusion (local target)"
        actions={<Button variant="outlined">Replay 3 failed</Button>}
      />
      <PreviewNotice />

      <Box sx={{ display: 'flex', gap: 2, mb: 2.5 }}>
        <StatTile label="Submitted" value={r.submitted.toLocaleString()} />
        <StatTile label="Accepted" value={r.accepted.toLocaleString()} color={tokens.success} />
        <StatTile label="Rejected" value={r.rejected} color={tokens.warning} />
      </Box>

      <SectionCard title="Reconciliation, read-back evidence">
        <Box sx={{ p: 2 }}>
          <Alert severity="info" sx={{ mb: 2 }}>
            Reconciliation re-reads actual target state via the Read-Back Adapter. Success is
            never inferred from the load response (ADR-0009).
          </Alert>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: tokens.bg }}>
            <Box sx={{ display: 'grid', gridTemplateColumns: '220px 1fr', rowGap: 1 }}>
              {evidence.map(([k, v, flag]) => (
                <Box key={k} sx={{ display: 'contents' }}>
                  <Mono color="#555B66">{k}</Mono>
                  <Mono color={flag === 'ok' ? tokens.success : flag === 'warn' ? tokens.warning : undefined}>
                    {v}
                  </Mono>
                </Box>
              ))}
            </Box>
          </Paper>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mt: 2 }}>
            <Mono color="#555B66">status</Mono>
            <StatusChip label={r.status} kind="success" />
            <StatusChip label="idempotent, replay never double-creates" kind="info" />
          </Box>
        </Box>
      </SectionCard>

      <FlowNav />
    </>
  );
}
