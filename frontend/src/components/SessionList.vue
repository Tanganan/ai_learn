<script setup lang="ts">
import { ChatDotRound, ChatRound, Clock, Delete, Plus } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

import type { ChatSession } from '@/types/chat'
import { formatSessionTime } from '@/utils/format'

const props = defineProps<{
  sessions: ChatSession[]
  activeId: number | null
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'select', id: number): void
  (e: 'create'): void
  (e: 'remove', id: number): void
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
      <div>
        <h2>
          <el-icon class="title-icon"><ChatDotRound /></el-icon>
          会话
        </h2>
        <p>按最近更新排序</p>
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
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 16px 12px;
  border-bottom: 1px solid var(--line);
}

.panel-head h2 {
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

.panel-head p {
  margin: 5px 0 0;
  font-size: 12.5px;
  color: var(--ink-soft);
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
