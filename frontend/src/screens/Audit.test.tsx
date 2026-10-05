import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { Audit } from './Audit';
import { renderWithProviders } from '../test/utils';

function stubVerify(ok: boolean) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: true, status: 200, json: async () => ({ ok, count: 1048 }) }) as Response),
  );
}
afterEach(() => vi.unstubAllGlobals());

describe('Audit', () => {
  it('shows a verified chain from /audit/verify', async () => {
    stubVerify(true);
    renderWithProviders(<Audit />);
    await waitFor(() => expect(screen.getByText('Chain verified')).toBeInTheDocument());
    expect(screen.getByText(/1048 entries/)).toBeInTheDocument();
    // sample audit log renders hash-chained actions
    expect(screen.getByText('reconcile')).toBeInTheDocument();
  });

  it('flags a broken chain when verify returns ok false', async () => {
    stubVerify(false);
    renderWithProviders(<Audit />);
    await waitFor(() => expect(screen.getByText('Chain broken')).toBeInTheDocument());
  });
});
