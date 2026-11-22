import type { ChatAnswer, ChatSession, ChatSessionDetail, ChatStreamMeta } from '@/types/chat'

import { postStream, request } from './client'

export interface ChatStreamHandlers {
  onMeta?: (meta: ChatStreamMeta) => void
  onDelta?: (text: string) => void
  onDone?: (answer: ChatAnswer) => void
  onError?: (detail: string) => void
}

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

  /** 流式提问：边收边回调，模型不可用时通过 onError 给出可读原因 */
  streamAsk(
    question: string,
    sessionId: number | null,
    handlers: ChatStreamHandlers,
    signal?: AbortSignal,
  ): Promise<void> {
    return postStream('/chat/stream', { question, session_id: sessionId }, signal, (event, data) => {
      if (event === 'meta') {
        handlers.onMeta?.(data as ChatStreamMeta)
        return
      }
      if (event === 'delta') {
        const text = (data as { text?: string }).text
        if (text) {
          handlers.onDelta?.(text)
        }
        return
      }
      if (event === 'done') {
        handlers.onDone?.(data as ChatAnswer)
        return
      }
      if (event === 'error') {
        const detail = (data as { detail?: string }).detail
        handlers.onError?.(detail || '回答生成失败，请稍后重试')
      }
    })
  },
}
