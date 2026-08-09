import { useState } from 'react';
import { AIOrchestratorView } from './components/AIOrchestratorView';
import { JourneyKanbanView } from './components/JourneyKanbanView';
import { PatientStateView } from './components/PatientStateView';
import { EventSimulatorView } from './components/EventSimulatorView';
import { UnifiedPEPView } from './components/UnifiedPEPView';
import { LabAndAuditView } from './components/LabAndAuditView';

export default function App() {
  const [activeTab, setActiveTab] = useState<'chat' | 'kanban' | 'crm' | 'events' | 'pep' | 'lab'>('lab');

  return (
    <div style={{ minHeight: '100vh', background: '#0f172a', color: '#f8fafc', fontFamily: 'Inter, system-ui, sans-serif' }}>
      
      {/* Header Bar */}
      <header style={{
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        background: 'rgba(15, 23, 42, 0.8)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            width: '40px',
            height: '40px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: 'bold',
            fontSize: '1.2rem',
            boxShadow: '0 0 20px rgba(59, 130, 246, 0.5)'
          }}>
            L1
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
              Lifeline One <span style={{ fontSize: '0.85rem', color: '#38bdf8', fontWeight: 500 }}>Plataforma & AI Orchestrator</span>
            </h1>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav style={{ display: 'flex', gap: '8px', background: 'rgba(255, 255, 255, 0.05)', padding: '4px', borderRadius: '12px' }}>
          <button
            onClick={() => setActiveTab('lab')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'lab' ? '#10b981' : 'transparent',
              color: activeTab === 'lab' ? '#fff' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            🔬 Laboratório & Guardião IA
          </button>
          <button
            onClick={() => setActiveTab('pep')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'pep' ? '#3b82f6' : 'transparent',
              color: activeTab === 'pep' ? '#fff' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📑 PEP Unificado 360°
          </button>
          <button
            onClick={() => setActiveTab('chat')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'chat' ? '#3b82f6' : 'transparent',
              color: activeTab === 'chat' ? '#fff' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            🤖 AI Orchestrator
          </button>
          <button
            onClick={() => setActiveTab('kanban')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'kanban' ? '#3b82f6' : 'transparent',
              color: activeTab === 'kanban' ? '#fff' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            📊 Kanban da Jornada
          </button>
          <button
            onClick={() => setActiveTab('crm')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'crm' ? '#3b82f6' : 'transparent',
              color: activeTab === 'crm' ? '#fff' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            👤 Estado do Paciente
          </button>
          <button
            onClick={() => setActiveTab('events')}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: activeTab === 'events' ? '#3b82f6' : 'transparent',
              color: activeTab === 'events' ? '#fff' : '#94a3b8',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s'
            }}
          >
            ⚡ Eventos & Automacões
          </button>
        </nav>
      </header>

      {/* Main Workspace */}
      <main style={{ padding: '32px', maxWidth: '1600px', margin: '0 auto' }}>
        {activeTab === 'lab' && <LabAndAuditView />}
        {activeTab === 'pep' && <UnifiedPEPView />}
        {activeTab === 'chat' && <AIOrchestratorView />}
        {activeTab === 'kanban' && <JourneyKanbanView />}
        {activeTab === 'crm' && <PatientStateView />}
        {activeTab === 'events' && <EventSimulatorView />}
      </main>
    </div>
  );
}
