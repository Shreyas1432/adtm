import { Box, Paper, Typography } from '@mui/material';
import type { ReactNode } from 'react';
import { fontMono, tokens } from '../theme';

// Character-exact values (SQL, hashes, ids, counts) render in the mono font.
export function Mono({ children, color }: { children: ReactNode; color?: string }) {
  return (
    <Box component="span" sx={{ fontFamily: fontMono, fontSize: 13, color }}>
      {children}
    </Box>
  );
}

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: ReactNode;
  actions?: ReactNode;
}) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2.5 }}>
      <Box sx={{ flex: 1 }}>
        <Typography variant="h1">{title}</Typography>
        {subtitle && (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
            {subtitle}
          </Typography>
        )}
      </Box>
      <Box sx={{ display: 'flex', gap: 1.5 }}>{actions}</Box>
    </Box>
  );
}

export function SectionCard({ title, children }: { title?: string; children: ReactNode }) {
  return (
    <Paper elevation={0} sx={{ borderRadius: 2, overflow: 'hidden', mb: 2.5 }}>
      {title && (
        <Typography
          variant="subtitle1"
          sx={{ fontWeight: 600, px: 2, py: 1.5, borderBottom: `1px solid ${tokens.line}` }}
        >
          {title}
        </Typography>
      )}
      {children}
    </Paper>
  );
}

export function StatTile({ label, value, color }: { label: string; value: ReactNode; color?: string }) {
  return (
    <Paper elevation={0} sx={{ borderRadius: 2, px: 2.5, py: 1.75, minWidth: 160 }}>
      <Typography sx={{ fontSize: 26, fontWeight: 700, color: color || tokens.ink900 }}>
        {value}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ fontWeight: 500 }}>
        {label}
      </Typography>
    </Paper>
  );
}
