import React, { useState, useEffect } from 'react';

interface PatientData {
  id: number;
  name: string;
  phone: string;
  current_status: string;
}

interface ReleasedExam {
  id: number;
  exam_name: string;
  requesting_doctor: string;
  status: string;
  scheduled_date?: string;
  findings?: string;
  vault_hash?: string;
}

export const PatientPortalView: React.FC = () => {
  const [patient, setPatient] = useState<PatientData | null>(null);
  const [exams, setExams] = useState<ReleasedExam[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchPortalData = async () => {
    try {
      const res = await fetch('/api/v1/patient-portal/my-dashboard');
      const data = await res.json();
      if (data.patient) {
        setPatient(data.patient);
        setExams(data.released_exams || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPortalData();
  }, []);

  const downloadPDF = () => {
    if (patient) {
      window.open(`/api/v1/documents/pep-pdf/${patient.id}`, '_blank');
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* Banner de Boas-Vindas Estilo App Mobile */}
      <div style={{
        background: 'linear-gradient(135deg, #0284c7 0%, #0d9488 100%)',
        borderRadius: '20px',
        padding: '24px',
        color: '#fff',
        boxShadow: '0 10px 25px -5px rgba(14, 165, 233, 0.4)'
      }}>
        <div style={{ fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px', opacity: 0.9 }}>
          📱 PORTAL DO PACIENTE MOBILE
        </div>
        <h2 style={{ margin: '8px 0 4px 0', fontSize: '1.6rem' }}>
          Olá, {patient ? patient.name : 'Paciente Lifeline'} 👋
        </h2>
        <p style={{ margin: 0, fontSize: '0.9rem', opacity: 0.95 }}>
          Acompanhe seus exames, laudos criptografados e consultas em tempo real.
        </p>

        <button
          onClick={downloadPDF}
          style={{
            marginTop: '16px',
            background: '#fff',
            color: '#0284c7',
            border: 'none',
            borderRadius: '10px',
            padding: '10px 18px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
          }}
        >
          📄 Baixar Meu Prontuário Oficial em PDF
        </button>
      </div>

      {/* Seção de Laudos no Cofre Segura */}
      <div style={{ background: '#1e293b', borderRadius: '16px', padding: '20px', border: '1px solid rgba(255,255,255,0.08)' }}>
        <h3 style={{ margin: '0 0 14px 0', color: '#38bdf8', fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '8px' }}>
          🔐 Meus Laudos e Exames Liberados
        </h3>

        {loading ? (
          <div style={{ color: '#94a3b8', textAlign: 'center', padding: '20px' }}>Carregando seus laudos...</div>
        ) : exams.length === 0 ? (
          <div style={{ color: '#64748b', textAlign: 'center', padding: '20px' }}>
            Nenhum exame liberado no momento. Solicite um exame com seu médico.
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {exams.map(e => (
              <div key={e.id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '12px', padding: '14px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 600, color: '#f8fafc' }}>📄 {e.exam_name}</span>
                  <span style={{ background: '#10b981', color: '#fff', padding: '3px 8px', borderRadius: '10px', fontSize: '0.75rem', fontWeight: 600 }}>
                    {e.status.toUpperCase()}
                  </span>
                </div>
                <div style={{ color: '#94a3b8', fontSize: '0.82rem', marginTop: '6px' }}>
                  👨‍⚕️ Prescrito por: {e.requesting_doctor}
                </div>
                {e.findings && (
                  <div style={{ color: '#cbd5e1', fontSize: '0.85rem', marginTop: '8px', background: 'rgba(0,0,0,0.2)', padding: '8px', borderRadius: '6px' }}>
                    <strong>Resultado / Laudo:</strong> {e.findings}
                  </div>
                )}
                {e.vault_hash && (
                  <div style={{ color: '#34d399', fontSize: '0.75rem', marginTop: '6px', fontFamily: 'monospace' }}>
                    🔒 Selo Cofre Segura: {e.vault_hash}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Card da Jornada Atual */}
      <div style={{ background: '#1e293b', borderRadius: '16px', padding: '20px', border: '1px solid rgba(255,255,255,0.08)' }}>
        <h3 style={{ margin: '0 0 10px 0', color: '#a855f7', fontSize: '1.1rem' }}>
          🏥 Status da Sua Jornada de Saúde
        </h3>
        <p style={{ margin: 0, color: '#cbd5e1', fontSize: '0.9rem' }}>
          Etapa Atual: <strong style={{ color: '#38bdf8' }}>{patient?.current_status || 'Atendimento Inicial'}</strong>
        </p>
      </div>

    </div>
  );
};
