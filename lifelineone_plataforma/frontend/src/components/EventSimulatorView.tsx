import React, { useState } from 'react';
import { Zap, RefreshCw, CalendarCheck, FileCheck, DollarSign } from 'lucide-react';
import type { EventResponse } from '../types';

export const EventSimulatorView: React.FC = () => {
  const [eventLogs, setEventLogs] = useState<Array<{ id: string; type: string; actions: string[]; newStage?: string; time: string }>>([
    { id: 'ev-001', type: 'consulta_realizada', actions: ['jornada_atualizada_e_followup_criado'], newStage: 'consulta_realizada', time: '10:15:00' }
  ]);

  const [triggering, setTriggering] = useState(false);

  const triggerEvent = async (eventType: string, payloadData: any) => {
    setTriggering(true);
    const now = new Date().toLocaleTimeString();

    try {
      const res = await fetch('http://localhost:8000/api/v1/events/publish', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_type: eventType,
          patient_id: 1,
          data: payloadData
        })
      });

      if (res.ok) {
        const data: EventResponse = await res.json();
        setEventLogs(prev => [
          { id: data.event_id.slice(0, 8), type: data.event_type, actions: data.actions_triggered, newStage: data.new_stage, time: now },
          ...prev
        ]);
      } else {
        simulateEventLocally(eventType, now);
      }
    } catch (err) {
      simulateEventLocally(eventType, now);
    } finally {
      setTriggering(false);
    }
  };

  const simulateEventLocally = (eventType: string, now: string) => {
    let actions: string[] = [];
    let stage = "";

    if (eventType === "consulta_realizada") {
      actions = ["jornada_atualizada_e_followup_criado"];
      stage = "consulta_realizada";
    } else if (eventType === "exame_disponivel") {
      actions = ["notificacao_exame_enviada"];
      stage = "exames";
    } else if (eventType === "paciente_inativo_180_dias") {
      actions = ["fluxo_reativacao_iniciado"];
      stage = "reativacao";
    } else if (eventType === "pagamento_confirmado") {
      actions = ["proxima_etapa_liberada"];
      stage = "tratamento";
    }

    setEventLogs(prev => [
      { id: Math.random().toString(36).substring(7), type: eventType, actions, newStage: stage, time: now },
      ...prev
    ]);
  };

  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
        <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Zap color="var(--accent-amber)" size={22} />
          Simulador da Arquitetura Baseada em Eventos (Event-Driven System)
        </h3>
        <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
          A IA e a plataforma reagem em tempo real a eventos do sistema, disparando automações da jornada do paciente.
        </p>
      </div>

      {/* Grid de Disparo de Eventos */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px', marginBottom: '24px' }}>
        
        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <CalendarCheck size={16} color="var(--accent-emerald)" /> Consulta Realizada
          </h4>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Atualiza jornada $\rightarrow$ Programa retorno $\rightarrow$ Cria lembrete $\rightarrow$ Cria follow-up.
          </p>
          <button
            className="btn-primary"
            style={{ width: '100%', fontSize: '0.8rem' }}
            disabled={triggering}
            onClick={() => triggerEvent('consulta_realizada', { doctor: 'Dr. Luiz', notes: 'Rinite alérgica' })}
          >
            Disparar Evento
          </button>
        </div>

        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <FileCheck size={16} color="var(--accent-amber)" /> Exame Disponível
          </h4>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Notifica paciente $\rightarrow$ Oferece janela de retorno médico.
          </p>
          <button
            className="btn-primary"
            style={{ width: '100%', fontSize: '0.8rem' }}
            disabled={triggering}
            onClick={() => triggerEvent('exame_disponivel', { exam_name: 'Espirometria' })}
          >
            Disparar Evento
          </button>
        </div>

        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <RefreshCw size={16} color="var(--accent-rose)" /> Paciente Inativo (180d)
          </h4>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Inicia fluxo automático de reativação da jornada.
          </p>
          <button
            className="btn-primary"
            style={{ width: '100%', fontSize: '0.8rem' }}
            disabled={triggering}
            onClick={() => triggerEvent('paciente_inativo_180_dias', {})}
          >
            Disparar Evento
          </button>
        </div>

        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ fontSize: '0.85rem', fontWeight: 700, marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <DollarSign size={16} color="var(--primary-cyan)" /> Pagamento Confirmado
          </h4>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '12px' }}>
            Libera a próxima etapa da jornada no sistema.
          </p>
          <button
            className="btn-primary"
            style={{ width: '100%', fontSize: '0.8rem' }}
            disabled={triggering}
            onClick={() => triggerEvent('pagamento_confirmado', { amount: 'R$ 350,00' })}
          >
            Disparar Evento
          </button>
        </div>

      </div>

      {/* Log de Eventos Executados */}
      <div>
        <h4 style={{ fontSize: '0.9rem', fontWeight: 700, marginBottom: '12px', color: 'var(--text-main)' }}>
          Histórico de Eventos Processados em Tempo Real:
        </h4>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {eventLogs.map((log, index) => (
            <div key={index} style={{
              background: 'rgba(0,0,0,0.3)',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              padding: '10px 14px',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              fontSize: '0.85rem',
              fontFamily: 'var(--font-mono)'
            }}>
              <div>
                <span style={{ color: 'var(--accent-amber)', fontWeight: 600 }}>[{log.time}] {log.type}</span>
                <span style={{ color: 'var(--text-muted)', marginLeft: '12px' }}>Ações: {log.actions.join(', ')}</span>
              </div>
              {log.newStage && (
                <span className="badge badge-emerald">Nova Etapa: {log.newStage}</span>
              )}
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
