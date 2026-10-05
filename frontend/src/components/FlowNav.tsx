import { Box, Button } from '@mui/material';
import { useLocation, useNavigate } from 'react-router-dom';
import { steps, stepIndex } from '../flow';
import type { ReactNode } from 'react';

export function FlowNav({ action }: { action?: ReactNode }) {
  const { pathname } = useLocation();
  const nav = useNavigate();
  const i = stepIndex(pathname);
  const prev = steps[i - 1];
  const next = steps[i + 1];
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mt: 2 }}>
      <Button variant="outlined" disabled={!prev} onClick={() => prev && nav(prev.path)}>
        Back
      </Button>
      <Box sx={{ flex: 1 }} />
      {action}
      <Button variant="contained" disabled={!next} onClick={() => next && nav(next.path)}>
        {next ? `Next: ${next.label}` : 'Done'}
      </Button>
    </Box>
  );
}
