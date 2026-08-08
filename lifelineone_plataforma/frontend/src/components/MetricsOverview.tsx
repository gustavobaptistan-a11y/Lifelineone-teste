import React from 'react';
import { Users, Calendar, Bot, RefreshCw } from 'lucide-react';

interface MetricsProps {
  patientCount: number;
}

export const MetricsOverview: React.FC<MetricsProps> = ({ patientCount }) => {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
      gap: '16px',
      marginBottom: '24px'
    }}>
      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Total de Pacientes</span>
          <Users size={18} color="var(--primary-cyan)" />
        </div>
        <h3 style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '8px' }}>{patientCount}</h3>
        <span className="badge badge-cyan" style={{ marginTop: '8px' }}>+100% ativo na plataforma</span>
      </div>

      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Decisões da IA (ReAct)</span>
          <Bot size={18} color="var(--accent-purple)" />
        </div>
        <h3 style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '8px' }}>11 Passos</h3>
        <span className="badge badge-purple" style={{ marginTop: '8px' }}>Orquestração contínua</span>
      </div>

      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Consultas & Retornos</span>
          <Calendar size={18} color="var(--accent-emerald)" />
        </div>
        <h3 style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '8px' }}>100% Sync</h3>
        <span className="badge badge-emerald" style={{ marginTop: '8px' }}>Fonte da Verdade em tempo real</span>
      </div>

      <div className="glass-panel" style={{ padding: '20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontWeight: 600 }}>Reativações de 180 dias</span>
          <RefreshCw size={18} color="var(--accent-amber)" />
        </div>
        <h3 style={{ fontSize: '1.8rem', fontWeight: 800, marginTop: '8px' }}>Automatizado</h3>
        <span className="badge badge-amber" style={{ marginTop: '8px' }}>Event-Driven System</span>
      </div>
    </div>
  );
};
