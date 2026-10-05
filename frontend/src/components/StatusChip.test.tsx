import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import { EncryptionChip, encryptionRationale } from './StatusChip';
import { renderWithProviders } from '../test/utils';

describe('EncryptionChip', () => {
  it('labels each encryption choice', () => {
    renderWithProviders(<EncryptionChip value="aead_blind_index" />);
    expect(screen.getByText('aead + blind index')).toBeInTheDocument();
  });

  it('explains the rationale without em-dashes', () => {
    expect(encryptionRationale('aead_blind_index')).toContain('blind index');
    expect(encryptionRationale('none')).not.toContain('—');
    expect(encryptionRationale('aead')).not.toContain('—');
  });
});
