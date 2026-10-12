import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { AlertRuleViewer } from '../components/AlertRuleViewer';
import { AuthProvider } from '../context/AuthContext';

describe('AlertRuleViewer Component', () => {
  it('renders initial empty state prompt when no rules exist', () => {
    render(
      <AuthProvider>
        <AlertRuleViewer architecture={null} />
      </AuthProvider>
    );

    expect(screen.getByText('Prometheus Alert Rules')).toBeInTheDocument();
    expect(screen.getByText('No Alert Rules Generated')).toBeInTheDocument();
  });
});
