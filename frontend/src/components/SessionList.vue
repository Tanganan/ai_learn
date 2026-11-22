<script setup lang="ts">
import { ChatDotRound, ChatRound, Clock, Delete, EditPen, Plus } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

import type { ChatSession } from '@/types/chat'
import { formatSessionTime } from '@/utils/format'

const props = defineProps<{
  sessions: ChatSession[]
  activeId: number | null
  loading: boolean
  mode: 'chat' | 'prompt'
}>()

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'create'): void
  (e: 'remove', id: number): void
  (e: 'switch-mode', mode: 'chat' | 'prompt'): void
}>()

async function handleRemove(id: number) {
  try {
    await ElMessageBox.confirm('删除后该会话的消息无法恢复，确认删除？', '删除会话', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  emit('remove', id)
}

function handleSelect(id: number) {
  if (id !== props.activeId) {
    emit('select', id)
  }
}
</script>

<template>
  <aside class="session-panel">
    <header class="panel-head">
      <div class="mode-switch" role="tablist">
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'chat'"
          :class="['mode-btn', { active: mode === 'chat' }]"
          @click="emit('switch-mode', 'chat')"
        >
          <el-icon><ChatDotRound /></el-icon>
          <span>会话</span>
        </button>
        <button
          type="button"
          role="tab"
          :aria-selected="mode === 'prompt'"
          :class="['mode-btn', { active: mode === 'prompt' }]"
          @click="emit('switch-mode', 'prompt')"
        >
          <el-icon><EditPen /></el-icon>
          <span>提示词</span>
        </button>
      </div>
      <el-button
        circle
        plain
        :icon="Plus"
        aria-label="新建会话"
        title="新建会话"
        @click="emit('create')"
      />
    </header>

    <div class="panel-body">
      <div v-if="loading" class="panel-empty">正在加载会话…</div>
      <div v-else-if="sessions.length === 0" class="panel-empty">
        还没有保存的会话，<br />先提一个问题吧
      </div>
      <ul v-else class="session-list">
        <li
          v-for="item in sessions"
          :key="item.id"
          :class="['session-item', { active: item.id === activeId }]"
          @click="handleSelect(item.id)"
        >
          <div class="item-main">
            <span class="item-title" :title="item.title">{{ item.title }}</span>
            <span class="item-meta">
              <el-icon><Clock /></el-icon>
              <span>{{ formatSessionTime(item.updated_at) }}</span>
              <span class="meta-dot">·</span>
              <el-icon><ChatRound /></el-icon>
              <span>{{ item.message_count }} 条</span>
            </span>
          </div>
          <el-button
            text
            class="item-delete"
            :icon="Delete"
            aria-label="删除会话"
            title="删除会话"
            @click.stop="handleRemove(item.id)"
          />
        </li>
      </ul>
    </div>
  </aside>
</template>

<style scoped>
.session-panel {
  display: flex;
  flex-direction: column;
  min-height: 0;
  height: 100%;
  border: 1px solid var(--line);
  border-radius: 14px;
  background: var(--panel-bg);
  overflow: hidden;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 12px;
  border-bottom: 1px solid var(--line);
}

.mode-switch {
  display: flex;
  gap: 3px;
  padding: 3px;
  border-radius: 10px;
  background: #f2f4f7;
}

.mode-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 30px;
  padding: 0 11px;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: #5b6472;
  font-size: 13.5px;
  line-height: 1;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;
}

.mode-btn .el-icon {
  font-size: 15px;
}

.mode-btn:hover {
  color: #2b6cf6;
}

.mode-btn.active {
  background: #ffffff;
  color: #2b6cf6;
  font-weight: 500;
  box-shadow: 0 1px 3px rgba(16, 24, 40, 0.08);
}

.panel-body {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  padding: 8px;
}

.panel-empty {
  padding: 28px 12px;
  font-size: 13px;
  line-height: 1.9;
  text-align: center;
  color: var(--ink-soft);
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.session-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition:
    background-color 0.15s ease,
    box-shadow 0.15s ease;
}

.session-item:hover {
  background: #f2f4f7;
}

.session-item.active {
  background: #eef3ff;
  box-shadow: inset 2px 0 0 #2b6cf6;
}

.session-item.active .item-title {
  color: #2b6cf6;
}

.item-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.item-title {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.item-meta {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #9099a7;
}

.item-meta .el-icon {
  font-size: 12.5px;
  color: #b3bac5;
}

.meta-dot {
  margin: 0 1px;
  color: #c3c9d2;
}

.item-delete {
  opacity: 0;
  transition: opacity 0.15s ease;
}

.session-item:hover .item-delete,
.session-item.active .item-delete {
  opacity: 1;
}
</style>
