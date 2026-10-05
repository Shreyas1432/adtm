import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { Audit } from './Audit';
import { renderWithProviders } from '../test/utils';

type LogRow = {
  id: number;
  action: string;
  object_ref: string | null;
  actor: string | null;
  hash: string;
};

function stub(verifyOk: boolean, logRows: LogRow[] = []) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async (url: string) => {
      if (String(url).includes('/audit/verify')) {
        return { ok: true, status: 200, json: async () => ({ ok: verifyOk, count: 1048 }) } as Response;
      }
      if (String(url).includes('/audit')) {
        return { ok: true, status: 200, json: async () => logRows } as Response;
      }
      return { ok: true, status: 200, json: async () => ({}) } as Response;
    }),
  );
}
afterEach(() => vi.unstubAllGlobals());

describe('Audit', () => {
  it('shows a verified chain and the live audit log', async () => {
    stub(true, [
      { id: 7, action: 'reconcile', object_ref: 'suppliers', actor: 'system', hash: '5d31f0..ee90' },
    ]);
    renderWithProviders(<Audit />);
    await waitFor(() => expect(screen.getByText('Chain verified')).toBeInTheDocument());
    expect(screen.getByText(/1048 entries/)).toBeInTheDocument();
    // live row from GET /audit
    await waitFor(() => expect(screen.getByText('reconcile')).toBeInTheDocument());
    expect(screen.getByText('Audit log')).toBeInTheDocument(); // not "(preview)" when live
  });

  it('flags a broken chain and falls back to the sample log when empty', async () => {
    stub(false, []);
    renderWithProviders(<Audit />);
    await waitFor(() => expect(screen.getByText('Chain broken')).toBeInTheDocument());
    // empty live log -> sample preview still renders known actions
    await waitFor(() => expect(screen.getByText('Audit log (preview)')).toBeInTheDocument());
    expect(screen.getByText('extract')).toBeInTheDocument();
  });
});
