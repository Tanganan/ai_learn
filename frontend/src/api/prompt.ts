import type { SystemPrompt } from '@/types/chat'

import { request } from './client'

export const promptApi = {
  get(): Promise<SystemPrompt> {
    return request<SystemPrompt>('/prompt')
  },

  update(prompt: string): Promise<SystemPrompt> {
    return request<SystemPrompt>('/prompt', { method: 'PUT', body: { prompt } })
  },

  reset(): Promise<SystemPrompt> {
    return request<SystemPrompt>('/prompt/reset', { method: 'POST' })
  },
}
