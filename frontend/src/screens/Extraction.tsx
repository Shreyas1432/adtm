import { Alert, Box, Button, TextField } from '@mui/material';
import { useState } from 'react';
import { StatusChip } from '../components/StatusChip';
import { PreviewNotice } from '../components/StateViews';
import { PageHeader, Mono, SectionCard } from '../components/ui';
import { FlowNav } from '../components/FlowNav';
import { isReadonlySelect } from '../lib/sql';
import { fontMono } from '../theme';

const DEFAULT_SQL = `SELECT vendor_id, vendor_name, tax_id, email,
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
  const [sql, setSql] = useState(DEFAULT_SQL);
  const [result, setResult] = useState<{ ok: boolean; msg: string } | null>(null);
  const edited = sql.trim() !== DEFAULT_SQL.trim();

  function run() {
    if (!isReadonlySelect(sql)) {
      setResult({
        ok: false,
        msg: 'Source is read-only. Only a single SELECT or WITH statement can run against EBS.',
      });
      return;
    }
    setResult({
      ok: true,
      msg: edited
        ? 'Query is valid and queued as a new draft version. It runs after human approval, writing a new immutable Bronze version (preview, no backend here).'
        : 'Extraction queued. A new immutable Bronze version would be created from the rows this query returns (preview, no backend here).',
    });
  }

  return (
    <>
      <PageHeader
        title="Extraction"
        subtitle={<><Mono>AP_SUPPLIERS</Mono> versioned read-only SQL to immutable Bronze</>}
        actions={
          <>
            <Button variant="outlined" disabled={!edited} onClick={() => { setSql(DEFAULT_SQL); setResult(null); }}>
              Reset
            </Button>
            <Button variant="contained" onClick={run}>
              Run extraction
            </Button>
          </>
        }
      />
      <PreviewNotice />

      <SectionCard title="Extraction SQL">
        <Box sx={{ p: 2 }}>
          <Box sx={{ display: 'flex', gap: 1, mb: 1.5 }}>
            {edited ? (
              <StatusChip label="draft, needs approval" kind="warning" />
            ) : (
              <StatusChip label="v3, approved" kind="success" />
            )}
            <StatusChip label="read-only" kind="info" />
          </Box>
          <TextField
            multiline
            fullWidth
            minRows={7}
            value={sql}
            onChange={(e) => { setSql(e.target.value); setResult(null); }}
            spellCheck={false}
            inputProps={{ 'aria-label': 'Extraction SQL', style: { fontFamily: fontMono, fontSize: 13 } }}
          />
          {result && (
            <Alert severity={result.ok ? 'success' : 'error'} sx={{ mt: 1.5 }}>
              {result.msg}
            </Alert>
          )}
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
