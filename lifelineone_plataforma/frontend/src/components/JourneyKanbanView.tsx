import React from 'react';
import { GitMerge, User, Phone, Stethoscope, ChevronRight } from 'lucide-react';
import type { JourneyStage } from '../types';

const STAGES: Array<{ id: JourneyStage; label: string; color: string }> = [
  { id: 'lead_criado', label: 'Lead Criado', color: '#38bdf8' },
  { id: 'primeiro_contato', label: 'Primeiro Contato', color: '#818cf8' },
  { id: 'pre_qualificacao', label: 'Pré-qualificação', color: '#c084fc' },
  { id: 'agendamento', label: 'Agendamento', color: '#f472b6' },
  { id: 'consulta_realizada', label: 'Consulta Realizada', color: '#34d399' },
  { id: 'exames', label: 'Exames', color: '#fbbf24' },
  { id: 'tratamento', label: 'Tratamento', color: '#60a5fa' },
  { id: 'retorno', label: 'Retorno', color: '#a78bfa' },
  { id: 'alta', label: 'Alta', color: '#4ade80' },
  { id: 'reativacao', label: 'Reativação (180d)', color: '#f87171' },
];

interface MockPatient {
  id: number;
  name: string;
  phone: string;
  insurance: string;
  doctor: string;
  stage: JourneyStage;
}

export const JourneyKanbanView: React.FC = () => {
  const [patients, setPatients] = React.useState<MockPatient[]>([
    { id: 1, name: 'Gustavo Baptista', phone: '5511999998888', insurance: 'GEAP', doctor: 'Dr. Luiz', stage: 'consulta_realizada' },
    { id: 2, name: 'Sheyla Baptista', phone: '5511977778888', insurance: 'Unimed', doctor: 'Dra. Maria', stage: 'pre_qualificacao' },
    { id: 3, name: 'Carlos Eduardo', phone: '5511966665555', insurance: 'Bradesco Saúde', doctor: 'Dr. Luiz', stage: 'reativacao' },
    { id: 4, name: 'Ana Paula', phone: '5511955554444', insurance: 'Particular', doctor: 'Dra. Maria', stage: 'agendamento' },
  ]);

  const moveStage = (patientId: number) => {
    setPatients(prev => prev.map(p => {
      if (p.id === patientId) {
        const currentIndex = STAGES.findIndex(s => s.id === p.stage);
        const nextStage = STAGES[(currentIndex + 1) % STAGES.length].id;
        return { ...p, stage: nextStage };
      }
      return p;
    }));
  };

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <GitMerge color="var(--primary-cyan)" size={22} />
            Funil Automatizado da Jornada do Paciente (10 Etapas)
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            A plataforma controla a jornada. A IA consulta esse estado antes de tomar qualquer decisão.
          </p>
        </div>
      </div>

      {/* Kanban Board Columns Container */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '12px',
        overflowX: 'auto',
        paddingBottom: '16px'
      }}>
        {STAGES.map((col) => {
          const colPatients = patients.filter(p => p.stage === col.id);
          return (
            <div key={col.id} style={{
              background: 'rgba(15, 23, 42, 0.5)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              padding: '12px',
              minHeight: '400px',
              display: 'flex',
              flexDirection: 'column'
            }}>
              {/* Header Coluna */}
              <div style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                paddingBottom: '8px',
                marginBottom: '12px',
                borderBottom: `2px solid ${col.color}`
              }}>
                <span style={{ fontSize: '0.8rem', fontWeight: 700, color: col.color }}>{col.label}</span>
                <span style={{
                  fontSize: '0.7rem',
                  padding: '2px 6px',
                  borderRadius: '10px',
                  background: 'rgba(255,255,255,0.08)',
                  fontWeight: 600
                }}>
                  {colPatients.length}
                </span>
              </div>

              {/* Cards na Coluna */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', flex: 1 }}>
                {colPatients.map(p => (
                  <div key={p.id} style={{
                    background: 'rgba(30, 41, 59, 0.8)',
                    border: '1px solid var(--border-color)',
                    borderRadius: '10px',
                    padding: '12px',
                    boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                  }}>
                    <h5 style={{ fontSize: '0.85rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '6px' }}>
                      <User size={14} color={col.color} /> {p.name}
                    </h5>
                    
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '6px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Phone size={12} /> {p.phone}
                      </span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                        <Stethoscope size={12} /> {p.doctor} ({p.insurance})
                      </span>
                    </div>

                    <button
                      onClick={() => moveStage(p.id)}
                      style={{
                        marginTop: '10px',
                        width: '100%',
                        padding: '4px 8px',
                        background: 'rgba(0,242,254,0.1)',
                        border: '1px solid rgba(0,242,254,0.2)',
                        color: 'var(--primary-cyan)',
                        borderRadius: '6px',
                        fontSize: '0.7rem',
                        fontWeight: 600,
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        gap: '4px'
                      }}
                    >
                      Avançar Etapa <ChevronRight size={12} />
                    </button>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
