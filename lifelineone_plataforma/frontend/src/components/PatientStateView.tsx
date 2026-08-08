import React from 'react';
import { UserCheck, Shield, Stethoscope, FileText } from 'lucide-react';

export const PatientStateView: React.FC = () => {
  return (
    <div className="glass-panel" style={{ padding: '24px' }}>
      <div style={{ marginBottom: '20px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '1.2rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <UserCheck color="var(--accent-emerald)" size={22} />
            Estado Persistente do Paciente (A Fonte da Verdade)
          </h3>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            Exemplo real da consulta feita pela IA antes de gerar qualquer resposta ao paciente.
          </p>
        </div>
        <span className="badge badge-emerald">ID Paciente: #1</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '20px' }}>
        
        {/* Card 1: Dados Pessoais & Convênio */}
        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--primary-cyan)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Shield size={16} /> Dados Pessoais & Convênio
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
            <div><span style={{ color: 'var(--text-muted)' }}>Nome:</span> Gustavo Baptista</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Telefone:</span> +55 (11) 99999-8888</div>
            <div><span style={{ color: 'var(--text-muted)' }}>E-mail:</span> gustavo@lifeline.one</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Convênio:</span> GEAP (Plano Saúde I)</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Nº Carteira:</span> 9876543210</div>
          </div>
        </div>

        {/* Card 2: Informações Clínicas & Médicas */}
        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-purple)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Stethoscope size={16} /> Prontuário & Quadro Clínico
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
            <div><span style={{ color: 'var(--text-muted)' }}>Médico Responsável:</span> Dr. Luiz</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Especialidade:</span> Pneumologia</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Tratamento Ativo:</span> Tratamento contínuo para Rinite</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Última Consulta:</span> 10/08/2026</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Próximo Retorno:</span> 10/09/2026</div>
          </div>
        </div>

        {/* Card 3: Exames & Tarefas Pendentes */}
        <div style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '16px' }}>
          <h4 style={{ fontSize: '0.9rem', fontWeight: 700, color: 'var(--accent-amber)', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <FileText size={16} /> Exames & Pendências (Follow-up)
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '0.85rem' }}>
            <div><span style={{ color: 'var(--text-muted)' }}>Exame Realizado:</span> Espirometria (Laudo disponível)</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Tarefa Pendente:</span> Lembrete de retorno programado</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Ticket Ativo:</span> Nenhum (Atendimento automático IA)</div>
            <div><span style={{ color: 'var(--text-muted)' }}>Intenção Atual:</span> duvida_convenio</div>
          </div>
        </div>

      </div>
    </div>
  );
};
