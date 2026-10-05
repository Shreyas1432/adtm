import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from './client';

function mockFetch(status: number, body: unknown) {
  const spy = vi.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    statusText: status === 200 ? 'OK' : 'ERR',
    json: async () => body,
  } as Response);
  vi.stubGlobal('fetch', spy);
  return spy;
}

afterEach(() => vi.unstubAllGlobals());

describe('api client', () => {
  it('sends a bearer token and parses JSON', async () => {
    const spy = mockFetch(200, [{ name: 'VENDOR_ID', type: 'NUMBER', encryption: 'none' }]);
    const cols = await api.columns('cid', 'AP_SUPPLIERS');
    expect(cols[0].name).toBe('VENDOR_ID');
    const [url, init] = spy.mock.calls[0];
    expect(url).toContain('/connections/cid/tables/AP_SUPPLIERS/columns');
    expect((init.headers as Record<string, string>).Authorization).toMatch(/^Bearer /);
  });

  it('verifyAudit hits /audit/verify', async () => {
    const spy = mockFetch(200, { ok: true, count: 3 });
    const r = await api.verifyAudit();
    expect(r).toEqual({ ok: true, count: 3 });
    expect(spy.mock.calls[0][0]).toContain('/audit/verify');
  });

  it('throws ApiError with the status on a non-2xx response', async () => {
    mockFetch(401, {});
    await expect(api.verifyAudit()).rejects.toMatchObject({ status: 401 });
    await expect(api.verifyAudit()).rejects.toBeInstanceOf(ApiError);
  });
});
