import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { Header } from '../components/Header';
import { AuthProvider } from '../context/AuthContext';

describe('Header Component', () => {
  it('renders application brand title and subheader', () => {
    const setActiveTab = vi.fn();
    const onOpenIngest = vi.fn();

    render(
      <AuthProvider>
        <Header activeTab="architecture" setActiveTab={setActiveTab} onOpenIngest={onOpenIngest} />
      </AuthProvider>
    );

    expect(screen.getByText('Log to Observability')).toBeInTheDocument();
    expect(screen.getByText(/Alan Vo \| AI & Machine Learning Pipeline/i)).toBeInTheDocument();
  });

  it('triggers onOpenIngest when "+ Ingest Logs" button is clicked', () => {
    const setActiveTab = vi.fn();
    const onOpenIngest = vi.fn();

    render(
      <AuthProvider>
        <Header activeTab="architecture" setActiveTab={setActiveTab} onOpenIngest={onOpenIngest} />
      </AuthProvider>
    );

    const ingestBtn = screen.getByText('+ Ingest Logs');
    fireEvent.click(ingestBtn);
    expect(onOpenIngest).toHaveBeenCalledTimes(1);
  });

  it('calls setActiveTab when a navigation button is clicked', () => {
    const setActiveTab = vi.fn();
    const onOpenIngest = vi.fn();

    render(
      <AuthProvider>
        <Header activeTab="architecture" setActiveTab={setActiveTab} onOpenIngest={onOpenIngest} />
      </AuthProvider>
    );

    const alertsTab = screen.getByText('Alert Rules');
    fireEvent.click(alertsTab);
    expect(setActiveTab).toHaveBeenCalledWith('alerts');
  });
});
