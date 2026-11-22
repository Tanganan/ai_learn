<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'

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
  status.value = 'loading'
  errorMessage.value = ''

  // 先乐观展示用户问题，网络失败时也保留上下文
  const optimistic: ChatMessage = {
    id: -Date.now(),
    session_id: activeId.value ?? 0,
    role: 'user',
    content: question,
    created_at: new Date().toISOString(),
  }
  messages.value = [...messages.value, optimistic]

  try {
    const answer = await chatApi.ask(question, activeId.value)
    activeId.value = answer.session_id
    messages.value = [
      ...messages.value.filter((item) => item.id !== optimistic.id),
      { ...optimistic, session_id: answer.session_id },
      answer.message,
    ]
    status.value = 'success'
    await loadSessions()
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      messages.value = messages.value.filter((item) => item.id !== optimistic.id)
      activeId.value = null
      status.value = 'idle'
      ElMessage.warning('会话已不存在，已刷新列表，请重新提问')
      await loadSessions()
      return
    }
    status.value = 'error'
    errorMessage.value = errorText(error, '回答生成失败，请稍后重试')
  } finally {
    sending.value = false
  }
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
          <span class="brand-mark">AI</span>
          <div>
            <h1>AI Learn 问答</h1>
            <p>Vue 3 + TypeScript + Element Plus · FastAPI + SQLAlchemy</p>
          </div>
        </div>
        <el-tag size="small" effect="plain" round>
          {{ activeId ? `会话 #${activeId}` : '新会话' }}
        </el-tag>
      </header>

      <ChatAnswer
        class="answer-slot"
        :messages="messages"
        :status="status"
        :error-message="errorMessage"
        @retry="handleRetry"
      />

      <ChatInput :sending="sending" @submit="handleSubmit" />
    </main>
  </div>
</template>

<style scoped>
.chat-layout {
  display: grid;
  grid-template-columns: 272px minmax(0, 1fr);
  gap: 16px;
  height: 100%;
  min-height: 0;
}

.main-column {
  display: flex;
  flex-direction: column;
  gap: 12px;
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
  gap: 10px;
}

.brand-mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: #2b6cf6;
  color: #ffffff;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.brand h1 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
}

.brand p {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--ink-soft);
}

.answer-slot {
  flex: 1 1 0;
  min-height: 0;
}

@media (max-width: 900px) {
  .chat-layout {
    grid-template-columns: minmax(0, 1fr);
    grid-template-rows: 180px minmax(0, 1fr);
  }

  .page-head {
    display: none;
  }
}
</style>
