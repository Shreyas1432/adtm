import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Mapping } from './Mapping';
import { renderWithProviders } from '../test/utils';

describe('Mapping', () => {
  it('shows pending mappings and approves one on click', async () => {
    renderWithProviders(<Mapping />);
    // two rows start pending (STATUS, PAYMENT_TERMS)
    expect(screen.getAllByText('needs approval')).toHaveLength(2);
    await userEvent.click(screen.getAllByRole('button', { name: 'Approve' })[0]);
    expect(screen.getAllByText('needs approval')).toHaveLength(1);
  });

  it('surfaces the design-time AI guardrail and a suggestion', () => {
    renderWithProviders(<Mapping />);
    expect(screen.getByText(/design time/i)).toBeInTheDocument();
    expect(screen.getByText('suggestion')).toBeInTheDocument();
  });
});
