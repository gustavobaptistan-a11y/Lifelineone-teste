export type JourneyStage = 
  | "lead_criado"
  | "primeiro_contato"
  | "pre_qualificacao"
  | "agendamento"
  | "consulta_realizada"
  | "exames"
  | "tratamento"
  | "retorno"
  | "alta"
  | "reativacao";

export interface PersonalData {
  id: number;
  name: string;
  phone: string;
  email?: string;
  cpf?: string;
  birth_date?: string;
}

export interface InsuranceData {
  name?: string;
  card_number?: string;
  plan?: string;
}

export interface MedicalInfo {
  attending_doctor?: string;
  doctor_crm?: string;
  specialty?: string;
}

export interface PatientState {
  patient_id: number;
  personal_data: PersonalData;
  insurance: InsuranceData;
  medical_info: MedicalInfo;
  current_stage: JourneyStage;
  active_treatment?: string;
  expected_return_date?: string;
  pending_tasks: any[];
  exams_data: any[];
  active_ticket_id?: string;
  last_interaction: string;
  current_intent?: string;
}

export interface OrchestratorMessageResponse {
  patient_id: number;
  current_stage: JourneyStage;
  detected_intent: string;
  tools_executed: string[];
  tool_outputs: Record<string, any>;
  ai_response: string;
}

export interface EventResponse {
  event_id: string;
  event_type: string;
  patient_id: number;
  actions_triggered: string[];
  new_stage?: string;
}
