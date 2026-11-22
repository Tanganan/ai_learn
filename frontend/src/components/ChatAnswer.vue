<script setup lang="ts">
import { Loading } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { nextTick, ref, watch } from 'vue'

import type { AnswerStatus, ChatMessage } from '@/types/chat'
import { formatMessageTime } from '@/utils/format'
import { renderMarkdown } from '@/utils/markdown'

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

/** 代码块复制：内容取自渲染后的 code 节点，避免重复维护原文 */
async function handleBodyClick(event: MouseEvent) {
  const target = event.target
  if (!(target instanceof HTMLElement)) {
    return
  }
  const button = target.closest<HTMLElement>('[data-copy-code]')
  if (!button) {
    return
  }
  const block = button.closest('.code-block')
  const code = block?.querySelector('code')?.textContent ?? ''
  if (!code) {
    return
  }
  try {
    await navigator.clipboard.writeText(code)
    ElMessage.success({ message: '代码已复制', duration: 1500 })
  } catch {
    ElMessage.error('复制失败，请手动选中代码')
  }
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

    <div ref="bodyRef" class="answer-body" @click="handleBodyClick">
      <div v-if="messages.length === 0 && status === 'idle'" class="answer-empty">
        <p class="empty-title">开始一个新问题</p>
        <p class="empty-text">在下方输入问题，回答会显示在这里；历史会话可以随时切回。</p>
      </div>

      <div class="thread">
        <article v-for="message in messages" :key="message.id" :class="['msg', message.role]">
          <div
            v-if="message.role === 'assistant'"
            class="msg-content md-body"
            v-html="renderMarkdown(message.content)"
          />
          <p v-else class="msg-content plain">{{ message.content }}</p>
          <time class="msg-time">{{ formatMessageTime(message.created_at) }}</time>
        </article>

        <article v-if="status === 'loading'" class="msg assistant loading-msg">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>正在生成回答…</span>
        </article>
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
  padding: 24px 22px;
  background:
    radial-gradient(120% 90% at 50% 0%, #fbfcff 0%, #ffffff 55%),
    #ffffff;
}

.answer-empty {
  max-width: 460px;
  margin: 64px auto 0;
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
  gap: 16px;
  width: 100%;
  max-width: 860px;
  margin: 0 auto;
}

.msg {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.msg.user {
  align-self: flex-end;
  width: fit-content;
  max-width: min(660px, 78%);
  padding: 11px 15px;
  border: 1px solid #dbe6ff;
  border-radius: 12px 12px 4px 12px;
  background: #eff4ff;
}

.msg.assistant {
  align-self: stretch;
  padding: 18px 20px;
  border: 1px solid #edf0f4;
  border-radius: 12px;
  background: #ffffff;
  box-shadow:
    0 1px 2px rgba(16, 24, 40, 0.04),
    0 6px 16px -12px rgba(16, 24, 40, 0.12);
}

.msg-content.plain {
  margin: 0;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.msg-time {
  font-size: 11px;
  color: #9aa3b0;
  font-variant-numeric: tabular-nums;
}

.msg.user .msg-time {
  align-self: flex-end;
}

.loading-msg {
  flex-direction: row;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  color: #6b7482;
  font-size: 13px;
}

.error-box {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  width: 100%;
  max-width: 860px;
  margin: 18px auto 0;
}

.error-box :deep(.el-alert) {
  width: 100%;
}
</style>
