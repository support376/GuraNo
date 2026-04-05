import { create } from 'zustand';
import type { Question } from '@/types/question';

interface QuestionState {
  questions: Question[];
  currentIndex: number;
  setQuestions: (q: Question[]) => void;
  setCurrentIndex: (i: number) => void;
  addDraft: (text: string) => void;
  removeDraft: (index: number) => void;
  updateDraft: (index: number, text: string) => void;
  drafts: string[];
  setDrafts: (d: string[]) => void;
}

export const useQuestionStore = create<QuestionState>((set) => ({
  questions: [],
  currentIndex: 0,
  drafts: [''],
  setQuestions: (questions) => set({ questions }),
  setCurrentIndex: (currentIndex) => set({ currentIndex }),
  addDraft: (text) => set((s) => ({ drafts: [...s.drafts, text] })),
  removeDraft: (index) => set((s) => ({ drafts: s.drafts.filter((_, i) => i !== index) })),
  updateDraft: (index, text) =>
    set((s) => ({ drafts: s.drafts.map((d, i) => (i === index ? text : d)) })),
  setDrafts: (drafts) => set({ drafts }),
}));
