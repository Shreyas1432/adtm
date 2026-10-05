import { Box, Chip } from '@mui/material';
import { tokens } from '../theme';
import type { Encryption } from '../api/types';

export type Semantic = 'success' | 'warning' | 'danger' | 'info' | 'neutral';

const MAP: Record<Semantic, { fg: string; bg: string }> = {
  success: { fg: tokens.success, bg: '#E4F2EA' },
  warning: { fg: tokens.warning, bg: '#F6ECD9' },
  danger: { fg: tokens.danger, bg: '#F7E3E1' },
  info: { fg: tokens.brand600, bg: tokens.brand50 },
  neutral: { fg: tokens.ink700, bg: '#EEF0F2' },
};

// Status is always icon (dot) + color + text, never color alone (a11y).
export function StatusChip({ label, kind }: { label: string; kind: Semantic }) {
  const c = MAP[kind];
  return (
    <Chip
      size="small"
      label={label}
      icon={
        <Box
          component="span"
          sx={{ width: 6, height: 6, borderRadius: '50%', bgcolor: c.fg, ml: 1 }}
        />
      }
      sx={{
        bgcolor: c.bg,
        color: c.fg,
        fontWeight: 500,
        fontSize: 12,
        borderRadius: 1,
        '& .MuiChip-icon': { color: c.fg },
      }}
    />
  );
}

const ENC: Record<Encryption, { label: string; kind: Semantic }> = {
  none: { label: 'none', kind: 'neutral' },
  aead: { label: 'aead', kind: 'info' },
  aead_blind_index: { label: 'aead + blind index', kind: 'success' },
};

export function EncryptionChip({ value }: { value: Encryption }) {
  const e = ENC[value];
  return <StatusChip label={e.label} kind={e.kind} />;
}

export function encryptionRationale(value: Encryption): string {
  if (value === 'aead_blind_index') return 'match key, so AEAD plus a blind index';
  if (value === 'aead') return 'sensitive, so AEAD';
  return 'low cardinality or no PII, so none';
}
