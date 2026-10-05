import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { DataQuality } from './DataQuality';
import { renderWithProviders } from '../test/utils';

describe('DataQuality', () => {
  it('summarises rules and shows failing samples', () => {
    renderWithProviders(<DataQuality />);
    // 'Rows read' is only a stat-tile label (Passed/Failed also appear as column headers)
    expect(screen.getByText('Rows read')).toBeInTheDocument();
    // a failing rule and its first-match sample render
    expect(screen.getByText('ri (country ref)')).toBeInTheDocument();
    expect(screen.getByText('(null) x3')).toBeInTheDocument();
    expect(screen.getByText('"ZZ" not in ref')).toBeInTheDocument();
  });
});
