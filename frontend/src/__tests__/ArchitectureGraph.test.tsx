import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { ArchitectureGraph } from '../components/ArchitectureGraph';
import { ArchitectureResult } from '../types';

describe('ArchitectureGraph Component', () => {
  it('renders empty state when no architecture is available', () => {
    render(<ArchitectureGraph architecture={null} />);
    expect(screen.getByText('No Architecture Detected Yet')).toBeInTheDocument();
  });

  it('renders service nodes, topology counts, and node details on click', () => {
    const mockArch: ArchitectureResult = {
      id: 1,
      created_at: new Date().toISOString(),
      title: 'Test Cluster',
      log_count: 50,
      services: [
        {
          name: 'api-gateway',
          role: 'gateway',
          user_facing: true,
          evidence: 'Found 30 ingress events',
          event_count: 30,
          error_count: 2,
          p95_latency_ms: 120
        },
        {
          name: 'order-service',
          role: 'api',
          user_facing: false,
          evidence: 'Found 20 backend events',
          event_count: 20,
          error_count: 0,
          p95_latency_ms: 85
        }
      ],
      topology: [
        {
          source: 'api-gateway',
          target: 'order-service',
          protocol: 'http',
          call_count: 20,
          failure_count: 0
        }
      ],
      datastores: [
        {
          name: 'postgres',
          type: 'relational',
          touching_services: ['order-service'],
          evidence: 'Referenced in order-service'
        }
      ],
      failure_patterns: [
        {
          pattern_type: 'timeout_spike',
          service: 'api-gateway',
          frequency: 2,
          summary: 'Detected 2 timeout incidents in api-gateway',
          evidence_lines: ['504 Gateway Timeout']
        }
      ],
      is_llm_assisted: false
    };

    render(<ArchitectureGraph architecture={mockArch} />);

    // Check stats summary
    expect(screen.getByText('Services Discovered')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // 2 services
    expect(screen.getAllByText('1').length).toBeGreaterThanOrEqual(1);

    // Check node labels in SVG
    expect(screen.getByText('api-gateway')).toBeInTheDocument();
    expect(screen.getByText('order-service')).toBeInTheDocument();
    expect(screen.getByText('postgres')).toBeInTheDocument();

    // Click on api-gateway circle to open detail sidebar
    const gatewayLabel = screen.getByText('api-gateway');
    fireEvent.click(gatewayLabel);

    expect(screen.getByText('GATEWAY')).toBeInTheDocument();
    expect(screen.getByText('Yes (Public Ingress)')).toBeInTheDocument();
    expect(screen.getByText('Found 30 ingress events')).toBeInTheDocument();
  });
});
