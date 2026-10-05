import {
  Box,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import { sampleDq } from '../data/sample';
import { StatusChip, type Semantic } from '../components/StatusChip';
import { PreviewNotice } from '../components/StateViews';
import { PageHeader, Mono, SectionCard, StatTile } from '../components/ui';
import { FlowNav } from '../components/FlowNav';
import { tokens } from '../theme';

function failChip(rule: string, failed: number) {
  if (failed === 0) return <StatusChip label="0" kind="success" />;
  const kind: Semantic = rule.startsWith('null') ? 'danger' : 'warning';
  return <StatusChip label={String(failed)} kind={kind} />;
}

export function DataQuality() {
  const passed = sampleDq.filter((r) => r.failed === 0).length;
  const failed = sampleDq.length - passed;

  return (
    <>
      <PageHeader
        title="Data Quality"
        subtitle={<><Mono>suppliers, v3</Mono> 7 rule types over immutable Bronze</>}
      />
      <PreviewNotice />

      <Box sx={{ display: 'flex', gap: 2, mb: 2.5 }}>
        <StatTile label="Rows read" value="1,284" />
        <StatTile label="Rules" value={sampleDq.length} />
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
            {sampleDq.map((r, i) => (
              <TableRow key={i} hover>
                <TableCell>
                  <Mono>{r.rule}</Mono>
                </TableCell>
                <TableCell>
                  <Mono color="#3A3F4B">{r.column}</Mono>
                </TableCell>
                <TableCell>
                  <Mono color="#3A3F4B">{r.passed.toLocaleString()}</Mono>
                </TableCell>
                <TableCell>{failChip(r.rule, r.failed)}</TableCell>
                <TableCell>{r.sample ? <Mono color="#3A3F4B">{r.sample}</Mono> : '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </SectionCard>

      <FlowNav />
    </>
  );
}
