<template>
  <div class="query-page">
    <div class="query-input-area">
      <a-textarea
        v-model:value="question"
        :rows="3"
        placeholder="Ask a question about your data... e.g., What were our top 5 products last month?"
        :disabled="loading"
        @keydown.ctrl.enter="handleQuery"
      />
      <div class="query-actions">
        <a-button type="primary" :loading="loading" :disabled="!question.trim()" @click="handleQuery">
          <template #icon><SendOutlined /></template>
          Ask
        </a-button>
        <span class="query-hint">Ctrl + Enter to send</span>
      </div>
    </div>

    <div v-if="loading" class="query-loading">
      <a-skeleton active />
      <a-skeleton active />
    </div>

    <div v-if="result && !loading" class="query-result">
      <a-card class="result-card">
        <template #title>
          <CheckCircleOutlined style="color: #52c41a" /> Answer
        </template>
        <div class="result-answer">{{ result.answer }}</div>
        <a-divider />
        <div class="result-meta">
          <a-space>
            <a-tag v-if="result.row_count !== null">{{ result.row_count }} rows</a-tag>
            <a-tag v-if="result.execution_time_ms !== null">{{ result.execution_time_ms }}ms</a-tag>
          </a-space>
        </div>
      </a-card>

      <a-card v-if="result.sql_query" class="result-sql">
        <template #title>
          <CodeOutlined /> SQL Query
          <a-button size="small" type="link" @click="copySql">
            <CopyOutlined /> Copy
          </a-button>
        </template>
        <pre class="sql-code"><code>{{ result.sql_query }}</code></pre>
      </a-card>
    </div>

    <div v-if="error && !loading" class="query-error">
      <a-alert :message="error" type="error" show-icon />
    </div>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import { SendOutlined, CheckCircleOutlined, CodeOutlined, CopyOutlined } from '@ant-design/icons-vue'
import type { QueryResponse } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const config = useRuntimeConfig()
const authStore = useAuthStore()
const headers = { Authorization: `Bearer ${authStore.token}` }

const question = ref('')
const loading = ref(false)
const result = ref<QueryResponse | null>(null)
const error = ref('')

async function handleQuery() {
  const q = question.value.trim()
  if (!q || loading.value) return
  loading.value = true
  result.value = null
  error.value = ''
  try {
    const res = await $fetch('/api/query', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      headers,
      body: { question: q },
    })
    result.value = res as QueryResponse
  } catch (e: any) {
    error.value = e.data?.detail || e.message || 'Query failed'
  } finally {
    loading.value = false
  }
}

function copySql() {
  if (result.value?.sql_query) {
    navigator.clipboard.writeText(result.value.sql_query)
    message.success('SQL copied to clipboard')
  }
}
</script>

<style scoped>
.query-page {
  max-width: 900px;
}
.query-input-area {
  margin-bottom: 16px;
  background: #fff;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #f0f0f0;
}
.query-actions {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.query-hint {
  font-size: 12px;
  color: #999;
}
.query-loading {
  padding: 24px;
}
.query-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.result-answer {
  font-size: 15px;
  line-height: 1.6;
  white-space: pre-wrap;
}
.result-meta {
  margin-top: 8px;
}
.sql-code {
  background: #f6f8fa;
  padding: 16px;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 13px;
  margin: 0;
}
</style>
