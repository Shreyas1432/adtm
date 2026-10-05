import { Box, Paper } from '@mui/material';
import { StatusChip } from '../components/StatusChip';
import { PreviewNotice } from '../components/StateViews';
import { PageHeader, Mono, SectionCard } from '../components/ui';
import { FlowNav } from '../components/FlowNav';
import { tokens } from '../theme';

const SQL = `SELECT vendor_id, vendor_name, tax_id, email,
       bank_account, address_line1, status,
       country_code, creation_date
FROM   AP.AP_SUPPLIERS
WHERE  enabled_flag = 'Y'`;

const manifest: [string, string][] = [
  ['dataset', 'suppliers'],
  ['version', 'v3'],
  ['file', 'bronze/suppliers/v3/part-0.parquet'],
  ['row_count', '1,284'],
  ['file_sha256', '9f2a1c..e7b4 (64 hex)'],
  ['schema_fingerprint', 'c41d8f..a2'],
  ['key_version', 'v1'],
  ['written_at', '2026-10-05 10:21:04Z'],
];

export function Extraction() {
  return (
    <>
      <PageHeader
        title="Extraction"
        subtitle={<><Mono>AP_SUPPLIERS</Mono> versioned read-only SQL to immutable Bronze</>}
      />
      <PreviewNotice />

      <SectionCard title="Extraction SQL">
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>
            <StatusChip label="v3, approved" kind="success" />
            <StatusChip label="read-only" kind="info" />
          </Box>
          <Paper variant="outlined" sx={{ p: 1.5, bgcolor: tokens.bg }}>
            <Box component="pre" sx={{ m: 0, fontFamily: 'inherit' }}>
              <Mono>{SQL}</Mono>
            </Box>
          </Paper>
        </Box>
      </SectionCard>

      <SectionCard title="Bronze manifest">
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>
            <StatusChip label="immutable, write-once" kind="success" />
            <StatusChip label="hash-chained audit" kind="info" />
          </Box>
          <Box sx={{ display: 'grid', gridTemplateColumns: '200px 1fr', rowGap: 1 }}>
            {manifest.map(([k, v]) => (
              <Box key={k} sx={{ display: 'contents' }}>
                <Mono color="#555B66">{k}</Mono>
                <Mono>{v}</Mono>
              </Box>
            ))}
          </Box>
        </Box>
      </SectionCard>

      <FlowNav />
    </>
  );
}
