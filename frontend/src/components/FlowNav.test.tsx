import { describe, expect, it } from 'vitest';
import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom';
import { ThemeProvider } from '@mui/material';
import { render } from '@testing-library/react';
import { FlowNav } from './FlowNav';
import { theme } from '../theme';

function Where() {
  return <div data-testid="path">{useLocation().pathname}</div>;
}

function renderAt(route: string) {
  return render(
    <ThemeProvider theme={theme}>
      <MemoryRouter initialEntries={[route]}>
        <Routes>
          <Route
            path="*"
            element={
              <>
                <FlowNav />
                <Where />
              </>
            }
          />
        </Routes>
      </MemoryRouter>
    </ThemeProvider>,
  );
}

describe('FlowNav', () => {
  it('moves to the next step', async () => {
    renderAt('/discovery');
    await userEvent.click(screen.getByRole('button', { name: /Next: Extraction/i }));
    expect(screen.getByTestId('path')).toHaveTextContent('/extraction');
  });

  it('moves to the previous step', async () => {
    renderAt('/discovery');
    await userEvent.click(screen.getByRole('button', { name: 'Back' }));
    expect(screen.getByTestId('path')).toHaveTextContent('/connections');
  });

  it('disables Back on the first step and shows Done on the last', () => {
    renderAt('/connections');
    expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled();
    renderAt('/audit');
    expect(screen.getByRole('button', { name: 'Done' })).toBeDisabled();
  });
});
