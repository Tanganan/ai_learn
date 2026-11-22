export type MessageRole = 'user' | 'assistant'

export interface ChatMessage {
  id: number
  session_id: number
  role: MessageRole
  content: string
  created_at: string
}

export interface ChatSession {
  id: number
  title: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[]
}

export interface ChatAnswer {
  session_id: number
  title: string
  answer: string
  message: ChatMessage
  created_at: string
}

/** 回答区域的状态：空闲 / 生成中（流式）/ 成功回答 / 模型不可用 */
export type AnswerStatus = 'idle' | 'streaming' | 'success' | 'error'

/** 流式响应的会话信息帧 */
export interface ChatStreamMeta {
  session_id: number
  title: string
}
