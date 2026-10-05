import {
  Alert,
  Box,
  Button,
  Snackbar,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import { useState } from 'react';
import { api } from '../api/client';
import type { Column } from '../api/types';
import { useAsync } from '../hooks/useAsync';
import { SAMPLE_CONNECTION_ID, SAMPLE_TABLE, sampleColumns } from '../data/sample';
import { EncryptionChip, StatusChip, encryptionRationale } from '../components/StatusChip';
import { Loading } from '../components/StateViews';
import { PageHeader, Mono, SectionCard } from '../components/ui';
import { FlowNav } from '../components/FlowNav';

// Wired to GET /connections/{id}/tables/{table}/columns. When the control plane
// is unreachable (e.g. no API running in dev) it falls back to sample metadata
// and says so, so the screen is always demonstrable.
export function SchemaDiscovery() {
  const { data, loading, error, reload } = useAsync<Column[]>(
    () => api.columns(SAMPLE_CONNECTION_ID, SAMPLE_TABLE),
    [],
  );
  const [approved, setApproved] = useState(false);

  const live = !!data;
  const columns = data ?? sampleColumns;

  return (
    <>
      <PageHeader
        title="Schema Discovery"
        subtitle={
          <>
            <Mono>{SAMPLE_TABLE}</Mono> source: EBS (read-only)
          </>
        }
        actions={
          <>
            <Button variant="outlined">Preview config</Button>
            <Button variant="contained" onClick={() => setApproved(true)}>
              Approve encryption plan
            </Button>
          </>
        }
      />

      <Alert severity="info" sx={{ mb: 2 }}>
        AI suggestions are design-time only. Approve to write them into the versioned
        config. No model runs at execution time.
      </Alert>

      {loading && <Loading label="Reading source metadata" />}
      {!loading && error && (
        <Alert
          severity="warning"
          sx={{ mb: 2 }}
          action={
            <Button color="inherit" size="small" onClick={reload}>
              Retry
            </Button>
          }
        >
          Control plane not reachable. Showing sample metadata.
        </Alert>
      )}

      {!loading && (
        <SectionCard>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Column</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Nullable</TableCell>
                <TableCell>PK</TableCell>
                <TableCell>Encryption at rest</TableCell>
                <TableCell>AI suggestion (design-time)</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {columns.map((c) => (
                <TableRow key={c.name} hover>
                  <TableCell>
                    <Mono>{c.name}</Mono>
                  </TableCell>
                  <TableCell>
                    <Mono color="#3A3F4B">{c.type}</Mono>
                  </TableCell>
                  <TableCell>{c.nullable ? 'Yes' : 'No'}</TableCell>
                  <TableCell>{c.pk ? <StatusChip label="PK" kind="info" /> : '-'}</TableCell>
                  <TableCell>
                    <EncryptionChip value={c.encryption} />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <StatusChip label="suggestion" kind="info" />
                      <span>{encryptionRationale(c.encryption)}</span>
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </SectionCard>
      )}

      <FlowNav />
      <Snackbar
        open={approved}
        autoHideDuration={3000}
        onClose={() => setApproved(false)}
        message={`Encryption plan approved for ${SAMPLE_TABLE}${live ? '' : ' (sample)'}`}
      />
    </>
  );
}
