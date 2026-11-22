<script setup lang="ts">
import { Lock, Promotion } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'

import { EMPTY_INPUT_HINT } from '@/utils/format'

const props = withDefaults(
  defineProps<{
    sending: boolean
    placeholder?: string
  }>(),
  { placeholder: '输入你的问题，Enter 发送，Shift + Enter 换行' },
)

const emit = defineEmits<{
  (e: 'submit', question: string): void
}>()

const draft = ref('')
const maxLength = 4000

function submit() {
  if (props.sending) {
    return
  }
  const question = draft.value.trim()
  if (!question) {
    ElMessage.warning(EMPTY_INPUT_HINT)
    return
  }
  emit('submit', question)
  draft.value = ''
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey) {
    return
  }
  // 中文输入法选词时按 Enter 不应该直接发送
  if (event.isComposing) {
    return
  }
  event.preventDefault()
  submit()
}
</script>

<template>
  <section class="input-panel">
    <el-input
      v-model="draft"
      type="textarea"
      :rows="3"
      resize="none"
      :maxlength="maxLength"
      show-word-limit
      :placeholder="placeholder"
      :disabled="sending"
      @keydown="handleKeydown"
    />
    <div class="input-foot">
      <span class="foot-hint">
        <el-icon><Lock /></el-icon>
        <span>请求统一发往后端 /api，浏览器不接触模型与数据库</span>
      </span>
      <el-button
        class="send-btn"
        type="primary"
        :icon="Promotion"
        :loading="sending"
        @click="submit"
      >
        {{ sending ? '生成中' : '发送' }}
      </el-button>
    </div>
  </section>
</template>

<style scoped>
.input-panel {
  display: flex;
  flex-shrink: 0;
  flex-direction: column;
  gap: 10px;
  padding: 13px 16px 15px;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel-bg);
}

.input-panel :deep(.el-textarea__inner) {
  border-radius: 10px;
  box-shadow: none;
  background: #f7f8fa;
  font-size: 14.5px;
  line-height: 1.75;
  padding: 12px 14px;
}

.input-panel :deep(.el-textarea__inner:focus) {
  background: #ffffff;
  box-shadow: 0 0 0 1px #2b6cf6 inset;
}

.input-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.foot-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  line-height: 1.5;
  color: #9099a7;
}

.foot-hint .el-icon {
  font-size: 12px;
}

.send-btn {
  height: 38px;
  padding: 0 20px;
  border-radius: 9px;
  font-size: 13.5px;
  font-weight: 500;
  letter-spacing: 0.02em;
  box-shadow: 0 4px 10px -4px rgba(43, 108, 246, 0.45);
}
</style>
