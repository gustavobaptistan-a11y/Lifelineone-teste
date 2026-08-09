import React, { useState } from 'react';

interface JourneyStep {
  step: string;
  stage: string;
  intent?: string;
  ai_response?: string;
  details?: string;
  exam_type?: string;
  extracted_findings?: string;
}

interface UnifiedPEPState {
  patient_id: number;
  personal_data: {
    id: number;
    name: string;
    phone: string;
    email?: string;
    cpf?: string;
    birth_date?: string;
  };
  insurance: {
    name?: string;
    card_number?: string;
    plan?: string;
  };
  medical_info: {
    attending_doctor?: string;
    doctor_crm?: string;
    specialty?: string;
  };
  current_stage: string;
  active_treatment?: string;
  expected_return_date?: string;
  exams_data: Array<{
    id: number;
    exam_type: string;
    file_name: string;
    findings: string;
    status: string;
    date: string;
  }>;
}

export const UnifiedPEPView: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [steps, setSteps] = useState<JourneyStep[]>([]);
  const [pepState, setPepState] = useState<UnifiedPEPState | null>(null);

  const runFullSimulation = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/v1/simulation/full-journey', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_name: 'Gustavo Baptista (Teste E2E)',
          phone: '5511999998888'
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setSteps(data.journey_steps_executed);
        setPepState(data.unified_pep_state);
      }
    } catch (err) {
      console.error('Erro na simulação:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      {/* Header Banner */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(37,99,235,0.2) 0%, rgba(147,51,234,0.2) 100%)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '16px',
        padding: '24px',
        backdropFilter: 'blur(10px)',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '1.6rem', color: '#fff' }}>
            📑 Prontuário Eletrônico Unificado (PEP 360°)
          </h2>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
            Visão 360° da Fonte Única da Verdade do Paciente: da 1ª conversa no WhatsApp até a Alta Médica
          </p>
        </div>
        <button
          onClick={runFullSimulation}
          disabled={loading}
          style={{
            background: loading ? '#475569' : 'linear-gradient(135deg, #2563eb 0%, #7c3aed 100%)',
            color: '#fff',
            border: 'none',
            borderRadius: '12px',
            padding: '14px 24px',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: loading ? 'not-allowed' : 'pointer',
            boxShadow: '0 4px 14px rgba(37,99,235,0.4)',
            transition: 'all 0.2s ease'
          }}
        >
          {loading ? '⚡ Simulando Fluxo E2E...' : '🚀 Executar Teste do Fluxo Completo'}
        </button>
      </div>

      {/* Grid com Linha do Tempo e PEP Unificado */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.2fr', gap: '24px' }}>
        
        {/* Lado Esquerdo: Etapas Executadas na Simulação */}
        <div style={{
          background: '#1e293b',
          borderRadius: '16px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.08)'
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#38bdf8', fontSize: '1.2rem' }}>
            🔄 Passos da Jornada Completa
          </h3>

          {steps.length === 0 ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: '40px 0' }}>
              Clique em <strong>"Executar Teste do Fluxo Completo"</strong> para rodar o ciclo: WhatsApp ➔ Consulta ➔ Exame/Lab ➔ Tratamento ➔ Alta.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {steps.map((st, idx) => (
                <div key={idx} style={{
                  background: 'rgba(255,255,255,0.03)',
                  borderLeft: '4px solid #3b82f6',
                  padding: '12px 16px',
                  borderRadius: '6px'
                }}>
                  <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>
                    {st.step}
                  </div>
                  {st.ai_response && (
                    <div style={{ color: '#cbd5e1', fontSize: '0.85rem', marginTop: '4px', fontStyle: 'italic' }}>
                      💬 IA: "{st.ai_response}"
                    </div>
                  )}
                  {st.extracted_findings && (
                    <div style={{ color: '#34d399', fontSize: '0.85rem', marginTop: '4px' }}>
                      🔬 Exame OCR: {st.extracted_findings}
                    </div>
                  )}
                  {st.details && (
                    <div style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '4px' }}>
                      📌 {st.details}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Lado Direito: Prontuário Unificado Consolidado */}
        <div style={{
          background: '#1e293b',
          borderRadius: '16px',
          padding: '20px',
          border: '1px solid rgba(255,255,255,0.08)'
        }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#a855f7', fontSize: '1.2rem' }}>
            📋 Prontuário Eletrônico Unificado (PEP)
          </h3>

          {!pepState ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: '40px 0' }}>
              Nenhum prontuário carregado. Clique para simular e visualizar os dados unificados.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              {/* Card de Identificação */}
              <div style={{
                background: 'rgba(168,85,247,0.1)',
                border: '1px solid rgba(168,85,247,0.3)',
                padding: '14px',
                borderRadius: '12px'
              }}>
                <div style={{ fontWeight: 600, fontSize: '1.1rem', color: '#f3e8ff' }}>
                  👤 {pepState.personal_data?.name}
                </div>
                <div style={{ color: '#cbd5e1', fontSize: '0.9rem', marginTop: '4px' }}>
                  📞 Telefone: {pepState.personal_data?.phone} | 🪪 ID: #{pepState.patient_id}
                </div>
                <div style={{ color: '#cbd5e1', fontSize: '0.9rem', marginTop: '2px' }}>
                  🏥 Convênio: {pepState.insurance?.name || 'Particular'} ({pepState.insurance?.plan || 'Executivo'})
                </div>
              </div>

              {/* Estado e Médico Responsável */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                  <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>ETAPA ATUAL DA JORNADA</span>
                  <div style={{ color: '#38bdf8', fontWeight: 600, marginTop: '2px' }}>
                    {pepState.current_stage?.toUpperCase()}
                  </div>
                </div>
                <div style={{ background: 'rgba(255,255,255,0.03)', padding: '12px', borderRadius: '8px' }}>
                  <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>MÉDICO RESPONSÁVEL</span>
                  <div style={{ color: '#f8fafc', fontWeight: 600, marginTop: '2px' }}>
                    {pepState.medical_info?.attending_doctor || 'Dr. Carlos Pneumologia'} ({pepState.medical_info?.specialty || 'Pneumologia'})
                  </div>
                </div>
              </div>

              {/* Central de Exames Laboratoriais */}
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '8px' }}>
                <div style={{ fontWeight: 600, color: '#34d399', marginBottom: '8px', fontSize: '0.95rem' }}>
                  🔬 Exames & Laudos OCR (Unificados no PEP)
                </div>
                {(!pepState.exams_data || pepState.exams_data.length === 0) ? (
                  <div style={{ color: '#64748b', fontSize: '0.85rem' }}>Nenhum exame anexo.</div>
                ) : (
                  pepState.exams_data.map(ex => (
                    <div key={ex.id} style={{ background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '6px', marginTop: '6px' }}>
                      <div style={{ color: '#f8fafc', fontWeight: 500, fontSize: '0.9rem' }}>
                        📄 {ex.exam_type} - {ex.file_name}
                      </div>
                      <div style={{ color: '#a7f3d0', fontSize: '0.85rem', marginTop: '4px' }}>
                        💡 Laudo IA: {ex.findings}
                      </div>
                    </div>
                  ))
                )}
              </div>

            </div>
          )}

        </div>

      </div>
    </div>
  );
};
