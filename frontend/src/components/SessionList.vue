<script setup lang="ts">
import { Delete, Plus } from '@element-plus/icons-vue'
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
        <h2>会话</h2>
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
              {{ formatSessionTime(item.updated_at) }} · {{ item.message_count }} 条消息
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
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}

.panel-head p {
  margin: 4px 0 0;
  font-size: 12px;
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
  padding: 10px 10px;
  border-radius: 10px;
  cursor: pointer;
  transition: background-color 0.15s ease;
}

.session-item:hover {
  background: #f2f4f7;
}

.session-item.active {
  background: #eef3ff;
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
  font-size: 13px;
  font-weight: 500;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.item-meta {
  font-size: 11px;
  color: var(--ink-soft);
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
