import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material';

export function Loading({ label = 'Loading' }: { label?: string }) {
  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, p: 4, color: 'text.secondary' }}>
      <CircularProgress size={20} />
      <Typography variant="body2">{label}</Typography>
    </Box>
  );
}

export function ErrorView({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  const unauth = /\b401\b/.test(error.message);
  return (
    <Alert
      severity={unauth ? 'warning' : 'error'}
      action={
        onRetry ? (
          <Button color="inherit" size="small" onClick={onRetry}>
            Retry
          </Button>
        ) : undefined
      }
      sx={{ my: 2 }}
    >
      {unauth
        ? 'Not authorized. Check the API token for this workspace.'
        : `Could not reach the control plane (${error.message}).`}
    </Alert>
  );
}

export function Empty({ text }: { text: string }) {
  return (
    <Box sx={{ p: 4, textAlign: 'center', color: 'text.secondary' }}>
      <Typography variant="body2">{text}</Typography>
    </Box>
  );
}

export function PreviewNotice() {
  return (
    <Alert severity="info" variant="outlined" sx={{ mb: 2 }}>
      Preview data. This step is produced by a worker job; its read endpoint is
      not wired yet, so sample values are shown.
    </Alert>
  );
}
