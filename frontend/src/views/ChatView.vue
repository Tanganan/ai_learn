<script setup lang="ts">
import { ChatLineSquare, MagicStick } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import { chatApi } from '@/api/chat'
import { ApiError } from '@/api/client'
import ChatAnswer from '@/components/ChatAnswer.vue'
import ChatInput from '@/components/ChatInput.vue'
import SessionList from '@/components/SessionList.vue'
import type { AnswerStatus, ChatMessage, ChatSession } from '@/types/chat'

const sessions = ref<ChatSession[]>([])
const messages = ref<ChatMessage[]>([])
const activeId = ref<number | null>(null)
const sessionsLoading = ref(true)
const sending = ref(false)
const status = ref<AnswerStatus>('idle')
const errorMessage = ref('')
const lastQuestion = ref('')
const streamText = ref('')
const generating = computed(() => status.value === 'streaming')

/** 当前流式请求的取消器，用户点「停止生成」时使用 */
let streamController: AbortController | null = null

/** 防止快速切换会话时旧请求覆盖新会话 */
let loadToken = 0

function errorText(error: unknown, fallback: string): string {
  return error instanceof ApiError ? error.message : fallback
}

async function loadSessions() {
  sessionsLoading.value = true
  try {
    sessions.value = await chatApi.listSessions()
  } catch (error) {
    ElMessage.error(errorText(error, '会话列表加载失败'))
  } finally {
    sessionsLoading.value = false
  }
}

async function openSession(id: number) {
  if (sending.value) {
    ElMessage.info('回答生成中，请稍候再切换会话')
    return
  }
  const token = ++loadToken
  activeId.value = id
  status.value = 'idle'
  errorMessage.value = ''
  messages.value = []

  try {
    const detail = await chatApi.getSession(id)
    if (token !== loadToken) {
      return
    }
    messages.value = detail.messages
    status.value = detail.messages.length > 0 ? 'success' : 'idle'
  } catch (error) {
    if (token !== loadToken) {
      return
    }
    activeId.value = null
    messages.value = []
    ElMessage.error(errorText(error, '会话加载失败'))
    if (error instanceof ApiError && error.status === 404) {
      await loadSessions()
    }
  }
}

async function handleSubmit(question: string) {
  if (sending.value) {
    return
  }
  lastQuestion.value = question
  sending.value = true
  status.value = 'streaming'
  errorMessage.value = ''
  streamText.value = ''

  // 先乐观展示用户问题，网络失败时也保留上下文
  const optimistic: ChatMessage = {
    id: -Date.now(),
    session_id: activeId.value ?? 0,
    role: 'user',
    content: question,
    created_at: new Date().toISOString(),
  }
  messages.value = [...messages.value, optimistic]

  const controller = new AbortController()
  streamController = controller
  let failed = false

  try {
    await chatApi.streamAsk(
      question,
      activeId.value,
      {
        onMeta(meta) {
          activeId.value = meta.session_id
          optimistic.session_id = meta.session_id
        },
        onDelta(text) {
          streamText.value += text
        },
        onDone(answer) {
          messages.value = [
            ...messages.value.filter((item) => item.id !== optimistic.id),
            { ...optimistic, session_id: answer.session_id },
            answer.message,
          ]
          streamText.value = ''
          status.value = 'success'
        },
        onError(detail) {
          failed = true
          streamText.value = ''
          status.value = 'error'
          errorMessage.value = detail
        },
      },
      controller.signal,
    )

    if (failed) {
      return
    }
    await loadSessions()
  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      await finalizeAborted(optimistic)
      return
    }
    if (error instanceof ApiError && error.status === 404) {
      messages.value = messages.value.filter((item) => item.id !== optimistic.id)
      activeId.value = null
      status.value = 'idle'
      ElMessage.warning('会话已不存在，已刷新列表，请重新提问')
      await loadSessions()
      return
    }
    streamText.value = ''
    status.value = 'error'
    errorMessage.value = errorText(error, '回答生成失败，请稍后重试')
  } finally {
    streamController = null
    sending.value = false
  }
}

/** 用户停止或连接中断：把已收到的内容留成一条本地消息，不让等待白费 */
async function finalizeAborted(optimistic: ChatMessage) {
  const partial = streamText.value.trim()
  streamText.value = ''
  if (partial) {
    messages.value = [
      ...messages.value,
      {
        id: -Date.now(),
        session_id: activeId.value ?? 0,
        role: 'assistant',
        content: partial,
        created_at: new Date().toISOString(),
      },
    ]
    status.value = 'success'
    ElMessage.info('已停止生成，已生成的内容已保留')
  } else {
    messages.value = messages.value.filter((item) => item.id !== optimistic.id)
    status.value = 'idle'
    ElMessage.info('已停止生成')
  }
  await loadSessions()
}

function stopStreaming() {
  if (!streamController) {
    return
  }
  streamController.abort()
}

function startNewSession() {
  if (sending.value) {
    ElMessage.info('回答生成中，请稍候再新建会话')
    return
  }
  loadToken += 1
  activeId.value = null
  messages.value = []
  status.value = 'idle'
  errorMessage.value = ''
  lastQuestion.value = ''
}

async function handleRemove(id: number) {
  if (sending.value) {
    ElMessage.info('回答生成中，请稍候再删除会话')
    return
  }
  try {
    await chatApi.deleteSession(id)
  } catch (error) {
    ElMessage.error(errorText(error, '删除会话失败'))
    return
  }
  if (activeId.value === id) {
    startNewSession()
  }
  ElMessage.success('会话已删除')
  await loadSessions()
}

function handleRetry() {
  if (!lastQuestion.value) {
    ElMessage.info('没有可重试的问题，请重新输入')
    return
  }
  void handleSubmit(lastQuestion.value)
}

onMounted(async () => {
  await loadSessions()
  const latest = sessions.value[0]
  if (latest) {
    await openSession(latest.id)
  }
})
</script>

<template>
  <div class="chat-layout">
    <SessionList
      :sessions="sessions"
      :active-id="activeId"
      :loading="sessionsLoading"
      @select="openSession"
      @create="startNewSession"
      @remove="handleRemove"
    />

    <main class="main-column">
      <header class="page-head">
        <div class="brand">
          <span class="brand-mark">
            <el-icon><MagicStick /></el-icon>
          </span>
          <div>
            <h1>AI Learn 问答</h1>
            <p>Vue 3 + TypeScript + Element Plus · FastAPI + SQLAlchemy</p>
          </div>
        </div>
        <el-tag size="small" effect="plain" round class="session-badge">
          <span class="badge-inner">
            <el-icon><ChatLineSquare /></el-icon>
            {{ activeId ? `会话 #${activeId}` : '新会话' }}
          </span>
        </el-tag>
      </header>

      <ChatAnswer
        class="answer-slot"
        :messages="messages"
        :status="status"
        :error-message="errorMessage"
        :stream-text="streamText"
        @retry="handleRetry"
      />

      <ChatInput :sending="sending" :streaming="generating" @submit="handleSubmit" @stop="stopStreaming" />
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  display: grid;
  grid-template-columns: 320px minmax(0, 820px);
  justify-content: center;
  gap: 18px;
  height: 100%;
  min-height: 0;
}

.main-column {
  display: flex;
  flex-direction: column;
  gap: 16px;
  width: 100%;
  min-height: 0;
  overflow: hidden;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 4px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 11px;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #4d8dff 0%, #2b6cf6 55%, #1d4ed8 100%);
  color: #ffffff;
  font-size: 18px;
  box-shadow: 0 5px 12px -5px rgba(43, 108, 246, 0.5);
}

.brand h1 {
  margin: 0;
  font-size: 19px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.brand p {
  margin: 4px 0 0;
  font-size: 13px;
  line-height: 1.4;
  color: var(--ink-soft);
}

.session-badge {
  border-radius: 999px;
  background: #ffffff;
}

.session-badge .badge-inner {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.answer-slot {
  flex: 1 1 0;
  min-height: 0;
}

@media (max-width: 1024px) {
  .chat-layout {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: 180px minmax(0, 1fr);
    max-width: 100%;
  }

  .page-head {
    display: none;
  }
}
</style>
