import {
  Alert,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { useState } from 'react';
import { api, ApiError } from '../api/client';
import { SAMPLE_CONNECTION_ID, sampleConnections } from '../data/sample';
import { StatusChip } from '../components/StatusChip';
import { PageHeader, Mono, SectionCard } from '../components/ui';
import { FlowNav } from '../components/FlowNav';

export function Connections() {
  const [testing, setTesting] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  async function test() {
    setTesting(true);
    setResult(null);
    try {
      const r = await api.testConnection(SAMPLE_CONNECTION_ID);
      setResult(r.ok ? 'SELECT 1 OK' : 'test returned not ok');
    } catch (e) {
      const msg = e instanceof ApiError ? `test failed (${e.status})` : 'control plane not reachable';
      setResult(msg);
    } finally {
      setTesting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Connections"
        subtitle="source and target systems. Secrets resolve from the client secrets manager."
        actions={
          <>
            <Button variant="outlined">Test all</Button>
            <Button variant="contained">New connection</Button>
          </>
        }
      />

      <SectionCard>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Kind</TableCell>
              <TableCell>Host / service</TableCell>
              <TableCell>Secret ref (handle)</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sampleConnections.map((c) => (
              <TableRow key={c.id} hover>
                <TableCell>
                  <Mono>{c.name}</Mono>
                </TableCell>
                <TableCell>
                  <StatusChip label={c.kind} kind="info" />
                </TableCell>
                <TableCell>
                  <Mono color="#3A3F4B">{c.host}</Mono>
                </TableCell>
                <TableCell>
                  <StatusChip label={c.secretRef} kind="neutral" />
                </TableCell>
                <TableCell>
                  <StatusChip label={c.status} kind="success" />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </SectionCard>

      <SectionCard title="Connection detail: ebs-suppliers-ro">
        <Box sx={{ p: 2 }}>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Source is read-only. The adapter issues no DML or DDL. Credentials resolve at
            call time and are never stored or logged (invariant #7).
          </Alert>
          <Box sx={{ display: 'grid', gridTemplateColumns: '200px 1fr', rowGap: 1 }}>
            <Mono color="#555B66">user</Mono>
            <Mono>adtm_ro (from secrets manager)</Mono>
            <Mono color="#555B66">schema</Mono>
            <Mono>AP</Mono>
            <Mono color="#555B66">driver</Mono>
            <Mono>python-oracledb (thin)</Mono>
            <Mono color="#555B66">secret_ref</Mono>
            <Mono>EBS_SUPPLIERS_RO (handle, not the secret)</Mono>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mt: 2 }}>
            <Button variant="outlined" onClick={test} disabled={testing}>
              {testing ? 'Testing' : 'Test connection'}
            </Button>
            {result && (
              <StatusChip
                label={result}
                kind={result.includes('OK') ? 'success' : 'warning'}
              />
            )}
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
            Connections are sample data until a list endpoint exists. Test connection is
            wired to POST /connections/&#123;id&#125;/test.
          </Typography>
        </Box>
      </SectionCard>

      <FlowNav />
    </>
  );
}
