import type { ChatAnswer, ChatSession, ChatSessionDetail } from '@/types/chat'

import { request } from './client'

export const chatApi = {
  listSessions(): Promise<ChatSession[]> {
    return request<ChatSession[]>('/sessions')
  },

  createSession(): Promise<ChatSession> {
    return request<ChatSession>('/sessions', { method: 'POST' })
  },

  getSession(sessionId: number, signal?: AbortSignal): Promise<ChatSessionDetail> {
    return request<ChatSessionDetail>(`/sessions/${sessionId}`, { signal })
  },

  deleteSession(sessionId: number): Promise<void> {
    return request<void>(`/sessions/${sessionId}`, { method: 'DELETE' })
  },

  ask(question: string, sessionId: number | null, signal?: AbortSignal): Promise<ChatAnswer> {
    return request<ChatAnswer>('/chat', {
      method: 'POST',
      body: { question, session_id: sessionId },
      signal,
    })
  },
}
