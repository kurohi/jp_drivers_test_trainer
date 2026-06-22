// RAG types mirrored from backend src/schemas/rag.py

import type { Language } from "./ui_meta";

export interface RagQueryIn {
  question: string;
  language: Language;
  k: number;
}

export interface RagSourceOut {
  source_url: string;
  title: string;
  snippet: string;
}

export interface RagAnswerOut {
  answer: string;
  sources: RagSourceOut[];
}
