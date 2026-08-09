import React, { useState } from 'react';

interface LabOrder {
  id: number;
  exam_name: string;
  requesting_doctor: string;
  status: string;
  unit: string;
  scheduled_date?: string;
  vault_hash?: string;
  findings?: string;
  created_at: string;
}

interface AuditLog {
  actor_name: string;
  actor_role: string;
  unit: string;
  ip: string;
  action: string;
  status: string;
  timestamp: string;
}

interface IntegrityReport {
  total_access_logs: number;
  anomalies_detected: number;
  integrity_score: string;
  pep_blockchain_sha256_hash: string;
  recent_access_logs: AuditLog[];
}

export const LabAndAuditView: React.FC = () => {
  const [patientId, setPatientId] = useState<number>(1);
  const [examName, setExamName] = useState<string>('Espirometria Completa');
  const [doctorName, setDoctorName] = useState<string>('Dr. Carlos Pneumologia');
  const [unitLocation, setUnitLocation] = useState<string>('Unidade Jardins - SP');
  
  const [orders, setOrders] = useState<LabOrder[]>([]);
  const [auditReport, setAuditReport] = useState<IntegrityReport | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  // 1. Criar Pedido de Exame
  const createOrder = async () => {
    try {
      const res = await fetch('/api/v1/lab-audit/orders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          exam_name: examName,
          requesting_doctor: doctorName,
          unit_location: unitLocation
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setNotification('✅ Pedido de exame criado! IA enviou WhatsApp para o paciente agendar coleta.');
        loadOrders();
        loadAudit();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // 2. Carregar Pedidos de Laboratório
  const loadOrders = async () => {
    try {
      const res = await fetch(`/api/v1/lab-audit/patient/${patientId}`);
      const data = await res.json();
      setOrders(data);
    } catch (err) {
      console.error(err);
    }
  };

  // 3. Carregar Auditoria & Guardião de IA
  const loadAudit = async () => {
    try {
      const res = await fetch(`/api/v1/lab-audit/audit/integrity/${patientId}`);
      const data = await res.json();
      setAuditReport(data);
    } catch (err) {
      console.error(err);
    }
  };

  // 4. Avançar Status do Exame
  const advanceStatus = async (orderId: number, nextStatus: string) => {
    try {
      const res = await fetch(`/api/v1/lab-audit/orders/${orderId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          next_status: nextStatus,
          scheduled_date: '18/08 às 09:00 (Coleta Domiciliar)',
          findings_summary: 'Laudo normal sem alterações detectadas.',
          actor_name: 'Bioquímico Silva (Laboratório Central)'
        })
      });
      const data = await res.json();
      if (data.status === 'success') {
        setNotification(`🔄 Status atualizado para: ${nextStatus}`);
        loadOrders();
        loadAudit();
      }
    } catch (err) {
      console.error(err);
    }
  };

  // 5. Decisão Médica Pós-Consulta
  const makeClinicalDecision = async (decision: 'alta' | 'novos_exames') => {
    try {
      const res = await fetch('/api/v1/clinical-decision/post-consultation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          patient_id: patientId,
          decision: decision,
          doctor_notes: decision === 'alta' ? 'Paciente assintomático. Concedida Alta.' : 'Requer exames complementares de sangue.'
        })
      });
      const data = await res.json();
      setNotification(`👨‍⚕️ ${data.message}`);
      loadAudit();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Banner Superior */}
      <div style={{
        background: 'linear-gradient(135deg, rgba(16,185,129,0.2) 0%, rgba(59,130,246,0.2) 100%)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '16px',
        padding: '24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <div>
          <h2 style={{ margin: 0, color: '#fff', fontSize: '1.6rem' }}>
            🔬 Laboratório, Guardião de IA & Trilha de Auditoria
          </h2>
          <p style={{ margin: '8px 0 0 0', color: '#94a3b8', fontSize: '0.95rem' }}>
            Rastreamento de Coleta em Tempo Real | Cofre Segura (AES-256) | Auditoria de Acessos por IA
          </p>
        </div>
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <span style={{ color: '#94a3b8', fontSize: '0.85rem' }}>ID do Paciente:</span>
          <input
            type="number"
            value={patientId}
            onChange={(e) => setPatientId(Number(e.target.value))}
            style={{ width: '60px', background: '#0f172a', border: '1px solid rgba(255,255,255,0.2)', color: '#fff', padding: '6px', borderRadius: '6px' }}
          />
          <button
            onClick={() => { loadOrders(); loadAudit(); }}
            style={{
              background: '#3b82f6',
              color: '#fff',
              border: 'none',
              borderRadius: '10px',
              padding: '12px 20px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            🔄 Auditar PEP Paciente
          </button>
        </div>
      </div>

      {notification && (
        <div style={{
          background: 'rgba(59,130,246,0.15)',
          border: '1px solid #3b82f6',
          color: '#60a5fa',
          padding: '12px 16px',
          borderRadius: '8px',
          fontWeight: 500
        }}>
          {notification}
        </div>
      )}

      {/* Grid Principal */}
      <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '24px' }}>
        
        {/* Painel de Pedidos de Laboratório */}
        <div style={{ background: '#1e293b', borderRadius: '16px', padding: '20px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#34d399', fontSize: '1.2rem' }}>
            🩸 Central de Laboratório & Coleta de Exames
          </h3>

          {/* Form para prescrever novo exame */}
          <div style={{ background: 'rgba(0,0,0,0.2)', padding: '16px', borderRadius: '10px', marginBottom: '20px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ fontWeight: 600, color: '#f8fafc', fontSize: '0.95rem' }}>➕ Prescrever Novo Exame pelo Médico</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '10px' }}>
              <input
                type="text"
                value={examName}
                onChange={(e) => setExamName(e.target.value)}
                placeholder="Nome do Exame"
                style={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '6px' }}
              />
              <input
                type="text"
                value={doctorName}
                onChange={(e) => setDoctorName(e.target.value)}
                placeholder="Médico Prescritor"
                style={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '6px' }}
              />
              <input
                type="text"
                value={unitLocation}
                onChange={(e) => setUnitLocation(e.target.value)}
                placeholder="Unidade"
                style={{ background: '#0f172a', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '8px', borderRadius: '6px' }}
              />
            </div>
            <button
              onClick={createOrder}
              style={{ background: '#10b981', color: '#fff', border: 'none', borderRadius: '6px', padding: '10px', fontWeight: 600, cursor: 'pointer' }}
            >
              🚀 Prescrever Exame & Disparar Contato WhatsApp IA
            </button>
          </div>

          {/* Lista de Pedidos com os 6 Status */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {orders.length === 0 ? (
              <div style={{ color: '#64748b', textAlign: 'center', padding: '20px' }}>
                Nenhum pedido de exame registrado para o paciente #{patientId}. Prescreva um acima.
              </div>
            ) : (
              orders.map(o => (
                <div key={o.id} style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '14px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={{ fontWeight: 600, color: '#f8fafc', fontSize: '1rem' }}>📄 {o.exam_name}</span>
                    <span style={{ background: '#0284c7', color: '#fff', padding: '4px 10px', borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600 }}>
                      {o.status.toUpperCase()}
                    </span>
                  </div>

                  <div style={{ color: '#94a3b8', fontSize: '0.85rem', marginTop: '6px' }}>
                    👨‍⚕️ Solicitante: {o.requesting_doctor} | 🏥 Unidade: {o.unit}
                  </div>

                  {o.vault_hash && (
                    <div style={{ background: 'rgba(16,185,129,0.1)', color: '#34d399', padding: '6px 10px', borderRadius: '6px', fontSize: '0.8rem', marginTop: '8px' }}>
                      🔐 Cofre Criptografado: {o.vault_hash}
                    </div>
                  )}

                  {/* Botões de Avanço de Status */}
                  <div style={{ display: 'flex', gap: '6px', marginTop: '10px', flexWrap: 'wrap' }}>
                    <button
                      onClick={() => advanceStatus(o.id, 'coleta_agendada')}
                      style={{ background: '#3b82f6', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                    >
                      1. Coleta Agendada
                    </button>
                    <button
                      onClick={() => advanceStatus(o.id, 'em_transporte')}
                      style={{ background: '#8b5cf6', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                    >
                      2. Em Transporte
                    </button>
                    <button
                      onClick={() => advanceStatus(o.id, 'analise_laboratorial')}
                      style={{ background: '#ec4899', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer' }}
                    >
                      3. Análise Lab
                    </button>
                    <button
                      onClick={() => advanceStatus(o.id, 'liberado_cofre_segura')}
                      style={{ background: '#10b981', color: '#fff', border: 'none', padding: '6px 10px', borderRadius: '6px', fontSize: '0.75rem', cursor: 'pointer', fontWeight: 600 }}
                    >
                      4. Liberar Cofre Segura 🔒
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Seção de Decisão Pós-Consulta */}
          <div style={{ marginTop: '24px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '10px', padding: '16px' }}>
            <div style={{ fontWeight: 600, color: '#f3e8ff', marginBottom: '8px' }}>👨‍⚕️ Decisão Médica Pós-Consulta (Resultado dos Exames)</div>
            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                onClick={() => makeClinicalDecision('alta')}
                style={{ flex: 1, background: '#10b981', color: '#fff', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}
              >
                ✅ Conceder Alta Médica (Caso Resolvido)
              </button>
              <button
                onClick={() => makeClinicalDecision('novos_exames')}
                style={{ flex: 1, background: '#f59e0b', color: '#fff', border: 'none', padding: '10px', borderRadius: '8px', fontWeight: 600, cursor: 'pointer' }}
              >
                🔄 Solicitar Novos Exames Complementares
              </button>
            </div>
          </div>
        </div>

        {/* Lado Direito: Guardião de IA & Trilha de Auditoria */}
        <div style={{ background: '#1e293b', borderRadius: '16px', padding: '20px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <h3 style={{ margin: '0 0 16px 0', color: '#a855f7', fontSize: '1.2rem' }}>
            🛡️ Guardião de IA & Auditoria de Acessos (LGPD)
          </h3>

          {!auditReport ? (
            <div style={{ color: '#64748b', textAlign: 'center', padding: '30px' }}>
              Clique em <strong>"Auditar PEP Paciente"</strong> para auditar a integridade e acessos do Prontuário.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              
              {/* Card de Score de Integridade */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div style={{ background: 'rgba(168,85,247,0.1)', border: '1px solid rgba(168,85,247,0.3)', padding: '12px', borderRadius: '8px' }}>
                  <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>SCORE DE INTEGRIDADE IA</span>
                  <div style={{ color: '#a855f7', fontWeight: 700, fontSize: '1.2rem', marginTop: '2px' }}>
                    {auditReport.integrity_score}
                  </div>
                </div>
                <div style={{ background: 'rgba(59,130,246,0.1)', border: '1px solid rgba(59,130,246,0.3)', padding: '12px', borderRadius: '8px' }}>
                  <span style={{ color: '#94a3b8', fontSize: '0.8rem' }}>TOTAL DE ACESSOS AUDITADOS</span>
                  <div style={{ color: '#38bdf8', fontWeight: 700, fontSize: '1.2rem', marginTop: '2px' }}>
                    {auditReport.total_access_logs} Acessos
                  </div>
                </div>
              </div>

              {/* Hash Blockchain SHA-256 do Prontuário */}
              <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px 12px', borderRadius: '8px', fontSize: '0.8rem', color: '#cbd5e1' }}>
                <span style={{ color: '#a855f7', fontWeight: 600 }}>🔗 Hash Único de Integridade (SHA-256):</span>
                <div style={{ fontFamily: 'monospace', color: '#e2e8f0', marginTop: '4px', wordBreak: 'break-all' }}>
                  {auditReport.pep_blockchain_sha256_hash}
                </div>
              </div>

              {/* Tabela de Audit Log (Quem, De Onde, O Que) */}
              <div style={{ background: 'rgba(255,255,255,0.02)', padding: '12px', borderRadius: '8px' }}>
                <div style={{ fontWeight: 600, color: '#f8fafc', marginBottom: '8px', fontSize: '0.9rem' }}>
                  📜 Trilha de Auditoria (Quem Acessou de Onde)
                </div>
                <div style={{ maxHeight: '240px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {auditReport.recent_access_logs.map((log, idx) => (
                    <div key={idx} style={{ background: 'rgba(0,0,0,0.2)', padding: '8px 10px', borderRadius: '6px', fontSize: '0.8rem', color: '#cbd5e1' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', color: '#f8fafc', fontWeight: 600 }}>
                        <span>👤 {log.actor_name} ({log.actor_role})</span>
                        <span style={{ color: '#34d399' }}>{log.status}</span>
                      </div>
                      <div style={{ color: '#94a3b8', fontSize: '0.78rem', marginTop: '2px' }}>
                        📍 Unidade: {log.unit} | IP: {log.ip}
                      </div>
                      <div style={{ color: '#e2e8f0', marginTop: '2px' }}>
                        📌 Ação: {log.action}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          )}
        </div>

      </div>
    </div>
  );
};
