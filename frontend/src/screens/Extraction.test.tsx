import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Extraction } from './Extraction';
import { renderWithProviders } from '../test/utils';

describe('Extraction', () => {
  it('runs the valid default query', async () => {
    renderWithProviders(<Extraction />);
    await userEvent.click(screen.getByRole('button', { name: 'Run extraction' }));
    expect(screen.getByText(/Extraction queued/)).toBeInTheDocument();
  });

  it('lets the user edit the query and blocks non read-only SQL', async () => {
    renderWithProviders(<Extraction />);
    const box = screen.getByLabelText('Extraction SQL');
    await userEvent.clear(box);
    await userEvent.type(box, 'DELETE FROM ap.ap_suppliers');
    expect(screen.getByText('draft, needs approval')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Run extraction' }));
    expect(screen.getByText(/Source is read-only/)).toBeInTheDocument();
  });
});
