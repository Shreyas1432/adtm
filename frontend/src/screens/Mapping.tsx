import {
  Alert,
  Box,
  Button,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from '@mui/material';
import { useState } from 'react';
import { sampleMappings } from '../data/sample';
import { StatusChip } from '../components/StatusChip';
import { PageHeader, Mono, SectionCard } from '../components/ui';
import { FlowNav } from '../components/FlowNav';

export function Mapping() {
  const [approved, setApproved] = useState<Record<string, boolean>>({});
  const isApproved = (m: (typeof sampleMappings)[number]) => m.approved || approved[m.source];

  return (
    <>
      <PageHeader
        title="Mapping"
        subtitle="suppliers to Fusion. Human-approved, versioned (ADR-0005)."
        actions={<Button variant="contained">Approve all ready</Button>}
      />

      <Alert severity="info" sx={{ mb: 2 }}>
        Only approved, versioned mappings execute. AI may suggest a mapping at design time;
        a human approves it into the config.
      </Alert>

      <SectionCard>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Source field</TableCell>
              <TableCell>Target field</TableCell>
              <TableCell>Kind</TableCell>
              <TableCell>Transform</TableCell>
              <TableCell>Approval</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {sampleMappings.map((m) => (
              <TableRow key={m.source} hover>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Mono>{m.source}</Mono>
                    {m.suggestion && <StatusChip label="suggestion" kind="info" />}
                  </Box>
                </TableCell>
                <TableCell>
                  <Mono color="#3A3F4B">{m.target}</Mono>
                </TableCell>
                <TableCell>
                  <StatusChip label={m.kind} kind={m.kind === 'one_to_one' ? 'neutral' : 'info'} />
                </TableCell>
                <TableCell>{m.transform ? <Mono color="#3A3F4B">{m.transform}</Mono> : '-'}</TableCell>
                <TableCell>
                  {isApproved(m) ? (
                    <StatusChip label="approved, Dev User" kind="success" />
                  ) : (
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <StatusChip label="needs approval" kind="warning" />
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setApproved((a) => ({ ...a, [m.source]: true }))}
                      >
                        Approve
                      </Button>
                    </Box>
                  )}
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
