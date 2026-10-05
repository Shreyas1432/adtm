import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { SchemaDiscovery } from './SchemaDiscovery';
import { renderWithProviders } from '../test/utils';

function stubFetch(impl: () => Promise<Response>) {
  vi.stubGlobal('fetch', vi.fn(impl));
}
afterEach(() => vi.unstubAllGlobals());

describe('SchemaDiscovery', () => {
  it('renders live columns from the API with encryption choices', async () => {
    stubFetch(async () =>
      ({
        ok: true,
        status: 200,
        json: async () => [
          { name: 'TAX_ID', type: 'VARCHAR2', nullable: true, encryption: 'aead_blind_index' },
        ],
      }) as Response,
    );
    renderWithProviders(<SchemaDiscovery />);
    await waitFor(() => expect(screen.getByText('TAX_ID')).toBeInTheDocument());
    expect(screen.getByText('aead + blind index')).toBeInTheDocument();
    // design-time AI guardrail is always surfaced
    expect(screen.getByText(/design-time only/i)).toBeInTheDocument();
  });

  it('falls back to sample metadata and warns when the API is unreachable', async () => {
    stubFetch(async () => ({ ok: false, status: 503, statusText: 'ERR', json: async () => ({}) }) as Response);
    renderWithProviders(<SchemaDiscovery />);
    await waitFor(() => expect(screen.getByText(/showing sample metadata/i)).toBeInTheDocument());
    // sample still renders the table so the screen is demonstrable
    expect(screen.getByText('VENDOR_ID')).toBeInTheDocument();
  });
});
