// MUI theme built from docs/DESIGN_SYSTEM.md tokens. Components reference the
// theme, never raw hex.
import { createTheme } from '@mui/material/styles';

export const tokens = {
  brand900: '#141A45',
  brand800: '#1E2761',
  brand600: '#2E3A8C',
  brand500: '#3B49B5',
  brand200: '#C7CCEC',
  brand50: '#EEF0FB',
  ink900: '#14161C',
  ink700: '#3A3F4B',
  ink500: '#555B66',
  line: '#E2E5EA',
  surface: '#FFFFFF',
  bg: '#F7F8FA',
  success: '#1E7F4F',
  warning: '#B06A00',
  danger: '#B3261E',
  info: '#2E3A8C',
  neutral: '#6B7280',
};

export const fontSans =
  'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
export const fontMono =
  '"Roboto Mono", "SF Mono", "JetBrains Mono", ui-monospace, monospace';

export const theme = createTheme({
  palette: {
    primary: { main: tokens.brand500, dark: tokens.brand600, contrastText: '#fff' },
    success: { main: tokens.success },
    warning: { main: tokens.warning },
    error: { main: tokens.danger },
    info: { main: tokens.info },
    background: { default: tokens.bg, paper: tokens.surface },
    text: { primary: tokens.ink900, secondary: tokens.ink500 },
    divider: tokens.line,
  },
  typography: {
    fontFamily: fontSans,
    h1: { fontSize: 28, fontWeight: 700, lineHeight: 1.2 },
    h2: { fontSize: 20, fontWeight: 700, lineHeight: 1.2 },
    subtitle2: { fontSize: 13, fontWeight: 500 },
    body2: { fontSize: 13 },
    button: { textTransform: 'none', fontWeight: 600 },
  },
  shape: { borderRadius: 8 },
  components: {
    MuiButton: { defaultProps: { disableElevation: true } },
    MuiPaper: {
      styleOverrides: {
        root: { backgroundImage: 'none', border: `1px solid ${tokens.line}` },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        head: { fontWeight: 600, color: tokens.ink500, fontSize: 12 },
        root: { borderColor: tokens.line },
      },
    },
  },
});
