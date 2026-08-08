import React, { useState } from 'react';
import { Send, Bot, User, CheckCircle2, Terminal, Sparkles } from 'lucide-react';
import type { OrchestratorMessageResponse } from '../types';

export const AIOrchestratorView: React.FC = () => {
  const [phone, setPhone] = useState('5511999998888');
  const [name, setName] = useState('Gustavo Baptista');
  const [message, setMessage] = useState('Olá, gostaria de agendar uma consulta com Pneumologista.');
  const [loading, setLoading] = useState(false);

  const [chatHistory, setChatHistory] = useState<Array<{ sender: 'user' | 'ai'; text: string; time: string }>>([
    { sender: 'user', text: 'Oi', time: '10:00' },
    { sender: 'ai', text: 'Olá, Gustavo (Convênio: GEAP)! Como posso ajudar você hoje?', time: '10:00' }
  ]);

  const [lastReasoning, setLastReasoning] = useState<OrchestratorMessageResponse | null>({
    patient_id: 1,
    current_stage: 'pre_qualificacao',
    detected_intent: 'agendamento',
    tools_executed: ['consultar_agenda'],
    tool_outputs: {
      agenda_slots: [
        { doctor: 'Dr. Luiz', date: '10/08 às 09:00' },
        { doctor: 'Dr. Luiz', date: '10/08 às 14:30' }
      ]
    },
    ai_response: 'Olá, Gustavo! Verifiquei sua jornada (pre_qualificacao). Temos os seguintes horários disponíveis com Dr. Luiz: Dr. Luiz (10/08 às 09:00). Qual horário prefere?'
  });

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim() || loading) return;

    const userText = message;
    setMessage('');
    setLoading(true);

    const now = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    setChatHistory(prev => [...prev, { sender: 'user', text: userText, time: now }]);

    try {
      const res = await fetch('http://localhost:8000/api/v1/orchestrator/message', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          phone: phone,
          message: userText,
          patient_name: name
        })
      });

      if (res.ok) {
        const data: OrchestratorMessageResponse = await res.json();
        setLastReasoning(data);
        setChatHistory(prev => [...prev, { sender: 'ai', text: data.ai_response, time: now }]);
      } else {
        simulateLocalResponse(userText, now);
      }
    } catch (err) {
      simulateLocalResponse(userText, now);
    } finally {
      setLoading(false);
    }
  };

  const simulateLocalResponse = (userText: string, now: string) => {
    const textLower = userText.toLowerCase();
    let intent = "duvida_geral";
    let tools: string[] = [];
    let response = `Olá, ${name}! Entendi sua mensagem. Como posso ajudar com sua consulta?`;

    if (textLower.includes("agendar") || textLower.includes("consulta")) {
      intent = "agendamento";
      tools = ["consultar_agenda"];
      response = `Olá, ${name}! Verifiquei sua jornada. Temos horários com Dr. Luiz no dia 10/08 às 09:00 e 14:30. Qual prefere?`;
    } else if (textLower.includes("convenio") || textLower.includes("geap")) {
      intent = "duvida_convenio";
      tools = ["consultar_convenios"];
      response = `Olá, ${name}! Sim, atendemos o convênio GEAP perfeitamente. Gostaria de prosseguir com o agendamento?`;
    }

    const simData: OrchestratorMessageResponse = {
      patient_id: 1,
      current_stage: intent === "agendamento" ? "pre_qualificacao" : "agendamento",
      detected_intent: intent,
      tools_executed: tools,
      tool_outputs: { convenios: ["GEAP", "Unimed", "Bradesco Saúde"] },
      ai_response: response
    };

    setLastReasoning(simData);
    setChatHistory(prev => [...prev, { sender: 'ai', text: response, time: now }]);
  };

  const stepsList = [
    { num: 1, title: 'Identificar Paciente', desc: `Telefone: ${phone} | Nome: ${name}` },
    { num: 2, title: 'Buscar Estado da Jornada', desc: `Estágio Atual: ${lastReasoning?.current_stage || 'lead_criado'}` },
    { num: 3, title: 'Buscar Contexto (3 Níveis)', desc: 'Recente: 10 msgs | Resumo: Ativo | Fonte da Verdade: PostgreSQL' },
    { num: 4, title: 'Informações Clínicas Permitidas', desc: 'Médico: Dr. Luiz | Diagnóstico: Rinite Alérgica' },
    { num: 5, title: 'Informações Comerciais', desc: 'Convênio: GEAP (Carteira: 987654)' },
    { num: 6, title: 'Eventos Pendentes', desc: 'Retorno em 10/09 | Follow-up: Enviar guia' },
    { num: 7, title: 'Entender Intenção Atual', desc: `Intenção Detectada: ${lastReasoning?.detected_intent || 'duvida_geral'}` },
    { num: 8, title: 'Decidir Próxima Ação', desc: 'Acionar ferramentas da plataforma antes de responder' },
    { num: 9, title: 'Executar Ferramentas (Tools)', desc: `Tools executadas: ${lastReasoning?.tools_executed.join(', ') || 'Nenhuma'}` },
    { num: 10, title: 'Atualizar Jornada', desc: 'Mover etapa do paciente se necessário' },
    { num: 11, title: 'Responder Naturalmente', desc: 'Geração de resposta humanizada baseada no estado real' }
  ];

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
      
      {/* SIMULADOR DE CHAT (CANAL DE COMUNICAÇÃO) */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '650px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
          <div>
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bot color="var(--primary-cyan)" size={20} />
              Simulador de Canal (WhatsApp / Instagram)
            </h3>
            <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>O WhatsApp é apenas o canal. A inteligência está na plataforma.</p>
          </div>
          <span className="badge badge-cyan">Canal Ativo</span>
        </div>

        {/* Form para simular paciente */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Nome Paciente</label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
            />
          </div>
          <div>
            <label style={{ fontSize: '0.7rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Telefone / WhatsApp</label>
            <input
              type="text"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              style={{ width: '100%', padding: '8px 12px', background: 'rgba(0,0,0,0.3)', border: '1px solid var(--border-color)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
            />
          </div>
        </div>

        {/* Chat Messages Body */}
        <div style={{ flex: 1, overflowY: 'auto', paddingRight: '8px', display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '16px' }}>
          {chatHistory.map((msg, index) => (
            <div key={index} style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.sender === 'user' ? 'flex-end' : 'flex-start'
            }}>
              <div style={{
                maxWidth: '85%',
                padding: '12px 16px',
                borderRadius: msg.sender === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                background: msg.sender === 'user' ? 'linear-gradient(135deg, #00f2fe 0%, #3b82f6 100%)' : 'rgba(30, 41, 59, 0.9)',
                color: msg.sender === 'user' ? '#07090e' : '#fff',
                fontSize: '0.9rem',
                fontWeight: msg.sender === 'user' ? 600 : 400,
                boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
              }}>
                <div style={{ fontSize: '0.7rem', opacity: 0.8, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '4px' }}>
                  {msg.sender === 'user' ? <User size={12} /> : <Bot size={12} />}
                  {msg.sender === 'user' ? name : 'Lifeline AI Orchestrator'} • {msg.time}
                </div>
                {msg.text}
              </div>
            </div>
          ))}
          {loading && (
            <div style={{ fontSize: '0.8rem', color: 'var(--primary-cyan)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Sparkles size={14} className="spin" /> Executando os 11 passos de raciocínio da IA...
            </div>
          )}
        </div>

        {/* Send Form */}
        <form onSubmit={handleSendMessage} style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            placeholder="Digite como se fosse o paciente..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            style={{
              flex: 1,
              padding: '12px 16px',
              background: 'rgba(0,0,0,0.4)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              color: '#fff',
              fontSize: '0.9rem'
            }}
          />
          <button type="submit" className="btn-primary" disabled={loading}>
            <Send size={16} /> Enviar
          </button>
        </form>
      </div>

      {/* INSPECTOR DOS 11 PASSOS DE RACIOCÍNIO DA IA */}
      <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', height: '650px', overflowY: 'auto' }}>
        <div style={{ marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '12px' }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Terminal color="var(--accent-purple)" size={20} />
            Inspeção dos 11 Passos (AI Reasoning Engine)
          </h3>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>A IA consulta a plataforma antes de cada resposta. Nunca confia apenas no histórico.</p>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {stepsList.map((step) => (
            <div key={step.num} style={{
              background: 'rgba(15, 23, 42, 0.6)',
              border: '1px solid var(--border-color)',
              borderRadius: '10px',
              padding: '10px 14px',
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              transition: 'all 0.2s ease'
            }}>
              <div style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #a855f7 0%, #4f46e5 100%)',
                color: '#fff',
                fontSize: '0.75rem',
                fontWeight: 700,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                {step.num}
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h4 style={{ fontSize: '0.85rem', fontWeight: 700 }}>{step.title}</h4>
                  <CheckCircle2 size={14} color="var(--accent-emerald)" />
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                  {step.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
