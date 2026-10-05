import { afterEach, describe, expect, it, vi } from 'vitest';
import { screen, waitFor } from '@testing-library/react';
import { DataQuality } from './DataQuality';
import { renderWithProviders } from '../test/utils';

function stub(rows: unknown, ok = true) {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => ({ ok, status: ok ? 200 : 500, statusText: 'x', json: async () => rows }) as Response),
  );
}
afterEach(() => vi.unstubAllGlobals());

describe('DataQuality', () => {
  it('maps live rule results from GET /dq/results', async () => {
    stub([
      { id: 'd1', run_id: 'r1', rule_type: 'null', params: { column: 'TAX_ID' }, passed: 1281, failed: 3, sample: [null, null, null] },
      { id: 'd2', run_id: 'r1', rule_type: 'ri', params: { column: 'COUNTRY_CODE' }, passed: 1283, failed: 1, sample: ['ZZ'] },
    ]);
    renderWithProviders(<DataQuality />);
    await waitFor(() => expect(screen.getByText('TAX_ID')).toBeInTheDocument());
    expect(screen.getByText('null')).toBeInTheDocument();
    expect(screen.getByText('(null)')).toBeInTheDocument(); // first sample element mapped
    expect(screen.getByText('3')).toBeInTheDocument(); // failed count chip
  });

  it('falls back to sample results when the endpoint fails', async () => {
    stub({}, false);
    renderWithProviders(<DataQuality />);
    await waitFor(() => expect(screen.getByText('ri (country ref)')).toBeInTheDocument());
    expect(screen.getByText('(null) x3')).toBeInTheDocument();
    expect(screen.getByText('Rules')).toBeInTheDocument(); // stat tile still renders from sample
  });
});
