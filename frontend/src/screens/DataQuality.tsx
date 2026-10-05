import {
  Alert,
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import { api } from '../api/client';
import type { DqResult } from '../api/types';
import { useAsync } from '../hooks/useAsync';
import { sampleDq } from '../data/sample';
import { StatusChip, type Semantic } from '../components/StatusChip';
import { Loading, PreviewNotice } from '../components/StateViews';
import { PageHeader, Mono, SectionCard, StatTile } from '../components/ui';
import { FlowNav } from '../components/FlowNav';
import { tokens } from '../theme';

interface Row {
  rule: string;
  column: string;
  passed: number;
  failed: number;
  sample: string;
}

function fromLive(r: DqResult): Row {
  const p = r.params || {};
  const column =
    (p.column as string) ??
    (Array.isArray(p.columns) ? (p.columns as string[]).join(',') : '');
  const dt = p.datatype ? `: ${p.datatype}` : '';
  const arr = Array.isArray(r.sample) ? r.sample : r.sample != null ? [r.sample] : [];
  const sample = arr.length ? String(arr[0] ?? '(null)') : '';
  return { rule: r.rule_type + dt, column, passed: r.passed, failed: r.failed, sample };
}

const sampleRows: Row[] = sampleDq.map((r) => ({ ...r }));

function failChip(rule: string, failed: number) {
  if (failed === 0) return <StatusChip label="0" kind="success" />;
  const kind: Semantic = rule.startsWith('null') ? 'danger' : 'warning';
  return <StatusChip label={String(failed)} kind={kind} />;
}

export function DataQuality() {
  const { data, loading } = useAsync<DqResult[]>(() => api.dqResults(), []);
  const live = !!data && data.length > 0;
  const rows: Row[] = live ? data!.map(fromLive) : sampleRows;
  const passed = rows.filter((r) => r.failed === 0).length;
  const failed = rows.length - passed;

  return (
    <>
      <PageHeader
        title="Data Quality"
        subtitle={<><Mono>suppliers, v3</Mono> rule results over immutable Bronze</>}
      />
      {!live && <PreviewNotice />}

      {loading ? (
        <Loading label="Loading rule results" />
      ) : (
        <>
          <Box sx={{ display: 'flex', gap: 2, mb: 2.5 }}>
            <StatTile label="Rules" value={rows.length} />
            <StatTile label="Passed" value={passed} color={tokens.success} />
            <StatTile label="Failed" value={failed} color={tokens.danger} />
          </Box>

          <SectionCard>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Rule</TableCell>
                  <TableCell>Column</TableCell>
                  <TableCell>Passed</TableCell>
                  <TableCell>Failed</TableCell>
                  <TableCell>Sample (first match)</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((r, i) => (
                  <TableRow key={i} hover>
                    <TableCell><Mono>{r.rule}</Mono></TableCell>
                    <TableCell><Mono color="#3A3F4B">{r.column}</Mono></TableCell>
                    <TableCell><Mono color="#3A3F4B">{r.passed.toLocaleString()}</Mono></TableCell>
                    <TableCell>{failChip(r.rule, r.failed)}</TableCell>
                    <TableCell>{r.sample ? <Mono color="#3A3F4B">{r.sample}</Mono> : '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </SectionCard>
        </>
      )}

      <FlowNav />
    </>
  );
}
