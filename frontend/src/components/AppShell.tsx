import {
  AppBar,
  Box,
  Chip,
  Drawer,
  List,
  ListItemButton,
  ListItemText,
  Step,
  StepLabel,
  Stepper,
  Toolbar,
  Typography,
} from '@mui/material';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { api } from '../api/client';
import { useAsync } from '../hooks/useAsync';
import { steps, stepIndex } from '../flow';
import { tokens } from '../theme';

const RAIL = 240;

function HealthBadge() {
  const { data, error, loading } = useAsync(() => api.health(), []);
  const ok = data?.status === 'ok';
  const label = loading ? 'checking' : error ? 'api unreachable' : ok ? 'api ok' : 'api degraded';
  return (
    <Chip
      size="small"
      label={label}
      sx={{
        bgcolor: ok ? '#E4F2EA' : error ? '#F7E3E1' : '#F6ECD9',
        color: ok ? tokens.success : error ? tokens.danger : tokens.warning,
        fontWeight: 500,
      }}
    />
  );
}

export function AppShell() {
  const { pathname } = useLocation();
  const active = stepIndex(pathname);

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <Drawer
        variant="permanent"
        sx={{
          width: RAIL,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: RAIL,
            bgcolor: tokens.brand900,
            color: '#fff',
            border: 'none',
            px: 2,
            py: 2.5,
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.25, px: 1, mb: 2 }}>
          <Box sx={{ width: 28, height: 28, borderRadius: 1.5, bgcolor: tokens.brand500 }} />
          <Typography sx={{ fontWeight: 700, fontSize: 18 }}>ADTM</Typography>
        </Box>
        <List disablePadding>
          {steps.map((s) => (
            <ListItemButton
              key={s.key}
              component={NavLink}
              to={s.path}
              sx={{
                borderRadius: 1.5,
                mb: 0.5,
                color: tokens.brand200,
                '&.active': { bgcolor: tokens.brand600, color: '#fff' },
                '&:hover': { bgcolor: 'rgba(255,255,255,0.06)' },
              }}
            >
              <ListItemText primaryTypographyProps={{ fontSize: 14 }} primary={s.label} />
            </ListItemButton>
          ))}
        </List>
      </Drawer>

      <Box sx={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0 }}>
        <AppBar
          position="sticky"
          elevation={0}
          sx={{ bgcolor: 'background.paper', borderBottom: `1px solid ${tokens.line}` }}
        >
          <Toolbar sx={{ gap: 1.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 500, color: 'text.primary' }}>
              dev-workspace
            </Typography>
            <Box sx={{ flex: 1 }} />
            <HealthBadge />
            <Chip
              size="small"
              label="Production, source read-only"
              sx={{ bgcolor: '#F6ECD9', color: tokens.warning, fontWeight: 500 }}
            />
            <Typography variant="body2" color="text.secondary">
              Dev User, admin
            </Typography>
          </Toolbar>
        </AppBar>

        <Box sx={{ px: 4, pt: 2, pb: 1 }}>
          <Stepper activeStep={active} alternativeLabel sx={{ '& .MuiStepLabel-label': { fontSize: 12 } }}>
            {steps.map((s) => (
              <Step key={s.key}>
                <StepLabel>{s.label}</StepLabel>
              </Step>
            ))}
          </Stepper>
        </Box>

        <Box sx={{ px: 4, pb: 4, flex: 1 }}>
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
