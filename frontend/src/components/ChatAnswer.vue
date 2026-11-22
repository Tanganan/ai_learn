<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
import { nextTick, ref, watch } from 'vue'

import type { AnswerStatus, ChatMessage } from '@/types/chat'
import { formatMessageTime } from '@/utils/format'

const props = defineProps<{
  messages: ChatMessage[]
  status: AnswerStatus
  errorMessage: string
}>()

const emit = defineEmits<{
  (e: 'retry'): void
}>()

const bodyRef = ref<HTMLDivElement | null>(null)

function scrollToBottom() {
  const el = bodyRef.value
  if (!el) {
    return
  }
  el.scrollTop = el.scrollHeight
}

watch(
  () => [props.messages.length, props.status] as const,
  () => {
    nextTick(scrollToBottom)
  },
)
</script>

<template>
  <section class="answer-panel">
    <header class="answer-head">
      <div class="head-title">
        <h2>回答</h2>
        <el-tag v-if="status === 'loading'" size="small" type="info" effect="light">加载中</el-tag>
        <el-tag v-else-if="status === 'error'" size="small" type="danger" effect="light">
          模型不可用
        </el-tag>
        <el-tag v-else-if="status === 'success'" size="small" type="success" effect="light">
          已返回
        </el-tag>
      </div>
      <span class="head-hint">回答由后端调用模型生成</span>
    </header>

    <div ref="bodyRef" class="answer-body">
      <div v-if="messages.length === 0 && status === 'idle'" class="answer-empty">
        <p class="empty-title">开始一个新问题</p>
        <p class="empty-text">在下方输入问题，回答会显示在这里；历史会话可以随时切回。</p>
      </div>

      <div class="thread">
        <div
          v-for="message in messages"
          :key="message.id"
          :class="['bubble-row', message.role]"
        >
          <div class="bubble">
            <p class="bubble-text">{{ message.content }}</p>
            <span class="bubble-time">{{ formatMessageTime(message.created_at) }}</span>
          </div>
        </div>

        <div v-if="status === 'loading'" class="bubble-row assistant">
          <div class="bubble loading-bubble">
            <el-icon class="is-loading"><Loading /></el-icon>
            <span>正在生成回答…</span>
          </div>
        </div>
      </div>

      <div v-if="status === 'error'" class="error-box">
        <el-alert
          type="error"
          :closable="false"
          show-icon
          title="模型当前不可用"
          :description="errorMessage || '请稍后重试，或检查后端模型配置。'"
        />
        <el-button size="small" plain @click="emit('retry')">用同一个问题重试</el-button>
      </div>

      <div v-else-if="messages.length === 0 && status === 'success'" class="answer-empty">
        <p class="empty-text">这个问题还没有留下回答。</p>
      </div>
    </div>
  </section>
</template>

<style scoped>
.answer-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel-bg);
  overflow: hidden;
}

.answer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 20px;
  border-bottom: 1px solid var(--line);
}

.head-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.head-title h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.head-hint {
  font-size: 12px;
  color: var(--ink-soft);
}

.answer-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 20px;
  background: linear-gradient(180deg, #fbfcfe 0%, #ffffff 60%);
}

.answer-empty {
  max-width: 460px;
  margin: 56px auto 0;
  text-align: center;
}

.empty-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 600;
}

.empty-text {
  margin: 0;
  font-size: 13px;
  line-height: 1.8;
  color: var(--ink-soft);
}

.thread {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.bubble-row {
  display: flex;
}

.bubble-row.user {
  justify-content: flex-end;
}

.bubble-row.assistant {
  justify-content: flex-start;
}

.bubble {
  max-width: min(680px, 78%);
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid var(--line);
  background: #f7f8fa;
}

.bubble-row.user .bubble {
  border-color: #d6e2ff;
  background: #eef3ff;
}

.bubble-text {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.bubble-time {
  display: block;
  margin-top: 6px;
  font-size: 11px;
  color: var(--ink-soft);
  text-align: right;
}

.loading-bubble {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--ink-soft);
}

.error-box {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  margin-top: 16px;
}

.error-box :deep(.el-alert) {
  width: 100%;
}
</style>
