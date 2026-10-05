import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Connections } from './Connections';
import { renderWithProviders } from '../test/utils';

function stubFetch(status: number, body: unknown) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok: status < 400, status, statusText: 'x', json: async () => body }) as Response),
  );
}
afterEach(() => vi.unstubAllGlobals());

describe('Connections', () => {
  it('lists connections and marks the source read-only', () => {
    stubFetch(200, { ok: true });
    renderWithProviders(<Connections />);
    expect(screen.getByText('ebs-suppliers-ro')).toBeInTheDocument();
    expect(screen.getByText(/read-only/i)).toBeInTheDocument();
    // secret ref is shown as a handle, never the secret
    expect(screen.getByText('EBS_SUPPLIERS_RO')).toBeInTheDocument();
  });

  it('reports a successful test connection', async () => {
    stubFetch(200, { ok: true });
    renderWithProviders(<Connections />);
    await userEvent.click(screen.getByRole('button', { name: 'Test connection' }));
    await waitFor(() => expect(screen.getByText('SELECT 1 OK')).toBeInTheDocument());
  });

  it('reports a failed test connection with the status', async () => {
    stubFetch(404, {});
    renderWithProviders(<Connections />);
    await userEvent.click(screen.getByRole('button', { name: 'Test connection' }));
    await waitFor(() => expect(screen.getByText('test failed (404)')).toBeInTheDocument());
  });
});
