import React from 'react';
import { Cpu, GitMerge, UserCheck, Zap, Activity } from 'lucide-react';

interface HeaderProps {
  activeTab: 'orchestrator' | 'kanban' | 'patient_state' | 'events';
  setActiveTab: (tab: 'orchestrator' | 'kanban' | 'patient_state' | 'events') => void;
}

export const Header: React.FC<HeaderProps> = ({ activeTab, setActiveTab }) => {
  return (
    <header className="glass-panel" style={{ borderRadius: '0 0 20px 20px', padding: '16px 32px', marginBottom: '24px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '16px' }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '42px',
            height: '42px',
            borderRadius: '12px',
            background: 'linear-gradient(135deg, #00f2fe 0%, #4f46e5 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 0 20px rgba(0,242,254,0.4)'
          }}>
            <Activity color="#07090e" size={24} strokeWidth={2.5} />
          </div>
          <div>
            <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em' }}>
              Lifeline<span className="gradient-text">One</span>
            </h1>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              Orquestrador de IA & Plataforma da Jornada do Paciente
            </p>
          </div>
        </div>

        {/* Live Status Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span className="badge badge-emerald">
            <span className="pulse-dot"></span>
            Python FastAPI + AI Orchestrator ON
          </span>
        </div>

        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '8px', background: 'rgba(0,0,0,0.3)', padding: '6px', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          <button
            onClick={() => setActiveTab('orchestrator')}
            className={activeTab === 'orchestrator' ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '0.85rem' }}
          >
            <Cpu size={16} />
            AI Orchestrator (11 Passos)
          </button>
          
          <button
            onClick={() => setActiveTab('kanban')}
            className={activeTab === 'kanban' ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '0.85rem' }}
          >
            <GitMerge size={16} />
            Funil de Jornada (Kanban)
          </button>

          <button
            onClick={() => setActiveTab('patient_state')}
            className={activeTab === 'patient_state' ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '0.85rem' }}
          >
            <UserCheck size={16} />
            Estado do Paciente (CRM)
          </button>

          <button
            onClick={() => setActiveTab('events')}
            className={activeTab === 'events' ? 'btn-primary' : 'btn-secondary'}
            style={{ fontSize: '0.85rem' }}
          >
            <Zap size={16} />
            Simulador de Eventos
          </button>
        </div>
      </div>
    </header>
  );
};
