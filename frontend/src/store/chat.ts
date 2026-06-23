import { create } from "zustand"
import type { RagAnswerOut } from "@/types"

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: RagAnswerOut["sources"]
  isRefusal?: boolean
}

interface ChatState {
  messages: ChatMessage[]
  isLoading: boolean
  ollamaError: { host: string } | null
  addMessage: (msg: ChatMessage) => void
  setLoading: (loading: boolean) => void
  setOllamaError: (error: { host: string } | null) => void
  reset: () => void
}

export const useChatStore = create<ChatState>()((set) => ({
  messages: [],
  isLoading: false,
  ollamaError: null,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  setLoading: (loading) => set({ isLoading: loading }),
  setOllamaError: (error) => set({ ollamaError: error }),
  reset: () =>
    set({ messages: [], isLoading: false, ollamaError: null }),
}))
