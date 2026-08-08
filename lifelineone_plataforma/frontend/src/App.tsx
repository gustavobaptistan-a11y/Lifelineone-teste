import { useState } from 'react';
import { Header } from './components/Header';
import { MetricsOverview } from './components/MetricsOverview';
import { AIOrchestratorView } from './components/AIOrchestratorView';
import { JourneyKanbanView } from './components/JourneyKanbanView';
import { PatientStateView } from './components/PatientStateView';
import { EventSimulatorView } from './components/EventSimulatorView';

export function App() {
  const [activeTab, setActiveTab] = useState<'orchestrator' | 'kanban' | 'patient_state' | 'events'>('orchestrator');

  return (
    <div style={{ maxWidth: '1440px', margin: '0 auto', padding: '0 24px 40px 24px' }}>
      <Header activeTab={activeTab} setActiveTab={setActiveTab} />
      
      <MetricsOverview patientCount={4} />

      <main>
        {activeTab === 'orchestrator' && <AIOrchestratorView />}
        {activeTab === 'kanban' && <JourneyKanbanView />}
        {activeTab === 'patient_state' && <PatientStateView />}
        {activeTab === 'events' && <EventSimulatorView />}
      </main>

      <footer style={{ marginTop: '40px', textAlign: 'center', fontSize: '0.75rem', color: 'var(--text-dim)', borderTop: '1px solid var(--border-color)', paddingTop: '20px' }}>
        Lifeline One &copy; 2026 — Plataforma & AI Orchestrator da Jornada do Paciente
      </footer>
    </div>
  );
}

export default App;
