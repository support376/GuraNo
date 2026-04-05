import axios from 'axios';
import type { Session } from '@/types/session';
import type { Question } from '@/types/question';
import type { ReportData } from '@/types/analysis';

const api = axios.create({
  baseURL: '/api',
});

export const sessionApi = {
  create: (hrSource: string) =>
    api.post<Session>('/sessions', { hr_source: hrSource }).then(r => r.data),
  get: (id: string) =>
    api.get<Session>(`/sessions/${id}`).then(r => r.data),
  list: () =>
    api.get<Session[]>('/sessions').then(r => r.data),
};

export const questionApi = {
  bulkCreate: (sessionId: string, questions: { text: string; category?: string }[]) =>
    api.post<Question[]>('/questions/bulk', { session_id: sessionId, questions }).then(r => r.data),
  getBySession: (sessionId: string) =>
    api.get<Question[]>(`/questions/session/${sessionId}`).then(r => r.data),
  delete: (id: string) =>
    api.delete(`/questions/${id}`).then(r => r.data),
};

export const reportApi = {
  get: (sessionId: string) =>
    api.get<ReportData>(`/reports/session/${sessionId}`).then(r => r.data),
};
