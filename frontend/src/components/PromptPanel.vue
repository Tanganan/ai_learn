<script setup lang="ts">
import { Check, EditPen, InfoFilled, RefreshLeft } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import { ApiError } from '@/api/client'
import { promptApi } from '@/api/prompt'
import type { SystemPrompt } from '@/types/chat'

const loading = ref(true)
const saving = ref(false)
const resetting = ref(false)
const draft = ref('')
const saved = ref('')
const isDefault = ref(true)
const updatedAt = ref<string | null>(null)
const maxLength = 2000

const dirty = computed(() => draft.value.trim() !== saved.value.trim())

function formatTime(value: string | null): string {
  if (!value) {
    return ''
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return ''
  }
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

function apply(data: SystemPrompt) {
  draft.value = data.prompt
  saved.value = data.prompt
  isDefault.value = data.is_default
  updatedAt.value = formatTime(data.updated_at)
}

async function load() {
  loading.value = true
  try {
    apply(await promptApi.get())
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : '提示词加载失败')
  } finally {
    loading.value = false
  }
}

async function save() {
  const value = draft.value.trim()
  if (!value) {
    ElMessage.warning('提示词不能为空')
    return
  }
  saving.value = true
  try {
    apply(await promptApi.update(value))
    ElMessage.success('提示词已保存，下一次回答立即生效')
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

async function reset() {
  try {
    await ElMessageBox.confirm('恢复默认会丢弃当前自定义的提示词，确认继续？', '恢复默认提示词', {
      confirmButtonText: '恢复默认',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  resetting.value = true
  try {
    apply(await promptApi.reset())
    ElMessage.success('已恢复默认提示词')
  } catch (error) {
    ElMessage.error(error instanceof ApiError ? error.message : '恢复失败，请稍后重试')
  } finally {
    resetting.value = false
  }
}

onMounted(load)
</script>

<template>
  <section class="prompt-panel">
    <header class="prompt-head">
      <div class="head-title">
        <h2>
          <el-icon class="title-icon"><EditPen /></el-icon>
          系统提示词
        </h2>
        <el-tag v-if="isDefault" size="small" type="info" effect="plain">默认</el-tag>
        <el-tag v-else size="small" type="success" effect="plain">自定义</el-tag>
      </div>
      <span class="head-hint">保存后对下一次提问立即生效</span>
    </header>

    <div class="prompt-body">
      <p class="prompt-intro">
        这段文字会作为 system message 随每次提问一起发给模型，用来限定它能回答的范围。
        例如只回答考研相关的问题：问到天气、娱乐、编程时，模型会说明无法回答，并把你引回考研话题。
      </p>

      <el-input
        v-model="draft"
        type="textarea"
        :rows="16"
        resize="none"
        :maxlength="maxLength"
        :disabled="loading"
        placeholder="在这里写系统提示词，例如：你是考研助手，只回答考研相关问题…"
        class="prompt-editor"
      />

      <div class="prompt-tips">
        <span class="tip">
          <el-icon><InfoFilled /></el-icon>
          写得越具体，边界越稳；建议把允许的范围和拒绝后怎么引导都写上。
        </span>
        <span class="count">{{ draft.length }} / {{ maxLength }}</span>
      </div>
    </div>

    <footer class="prompt-foot">
      <span class="foot-status">
        {{ isDefault ? '当前使用默认提示词' : `已自定义${updatedAt ? ` · ${updatedAt}` : ''}` }}
      </span>
      <div class="foot-actions">
        <el-button
          plain
          :icon="RefreshLeft"
          :loading="resetting"
          :disabled="loading || isDefault"
          @click="reset"
        >
          恢复默认
        </el-button>
        <el-button
          type="primary"
          :icon="Check"
          :loading="saving"
          :disabled="loading || !dirty || !draft.trim()"
          @click="save"
        >
          保存提示词
        </el-button>
      </div>
    </footer>
  </section>
</template>

<style scoped>
.prompt-panel {
  display: flex;
  flex: 1 1 0;
  flex-direction: column;
  min-height: 0;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel-bg);
  overflow: hidden;
}

.prompt-head {
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
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}

.title-icon {
  font-size: 16px;
  color: #5b6472;
}

.head-hint {
  font-size: 12.5px;
  color: var(--ink-soft);
}

.prompt-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 12px;
  min-height: 0;
  padding: 20px 24px 16px;
  overflow-y: auto;
}

.prompt-intro {
  margin: 0;
  padding: 12px 14px;
  border: 1px solid #e4edff;
  border-radius: 10px;
  background: #f5f8ff;
  font-size: 13.5px;
  line-height: 1.8;
  color: #4a5768;
}

.prompt-editor {
  flex: 1;
  min-height: 240px;
}

.prompt-editor :deep(.el-textarea__inner) {
  height: 100%;
  min-height: 240px;
  border-radius: 12px;
  background: #fafbfc;
  box-shadow: 0 0 0 1px #e6e8eb inset;
  padding: 16px 18px;
  font-size: 14.5px;
  line-height: 1.8;
  color: #2c333d;
}

.prompt-editor :deep(.el-textarea__inner:focus) {
  background: #ffffff;
  box-shadow:
    0 0 0 1px #2b6cf6 inset,
    0 0 0 3px rgba(43, 108, 246, 0.1);
}

.prompt-tips {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  font-size: 12.5px;
  color: #9099a7;
}

.tip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.tip .el-icon {
  font-size: 13px;
}

.count {
  font-variant-numeric: tabular-nums;
}

.prompt-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-top: 1px solid var(--line);
  background: #fbfcfd;
}

.foot-status {
  font-size: 12.5px;
  color: var(--ink-soft);
}

.foot-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.foot-actions .el-button {
  height: 38px;
  border-radius: 9px;
  font-size: 14px;
  padding: 0 18px;
}

@media (max-width: 600px) {
  .prompt-body {
    padding: 14px;
  }

  .prompt-head {
    padding: 14px 16px;
  }

  .prompt-head .head-hint {
    display: none;
  }

  .prompt-foot {
    flex-wrap: wrap;
    padding: 12px 14px;
  }
}
</style>
