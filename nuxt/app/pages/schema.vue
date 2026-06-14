<template>
  <div class="schema-page">
    <PageHeader title="Database Schema" description="Browse database tables and columns" />

    <a-row :gutter="16">
      <a-col :span="8">
        <a-card title="Tables">
          <a-input-search v-model:value="tableFilter" placeholder="Search tables..." style="margin-bottom: 12px" />
          <a-menu
            mode="inline"
            :selected-keys="[selectedTable]"
            style="border-inline-end: none; max-height: 500px; overflow-y: auto"
          >
            <a-menu-item
              v-for="table in filteredTables"
              :key="table"
              @click="selectedTable = table"
            >
              <TableOutlined /> {{ table }}
            </a-menu-item>
          </a-menu>
        </a-card>
      </a-col>
      <a-col :span="16">
        <a-card v-if="selectedTable && schema[selectedTable]" :title="`${selectedTable} Columns`">
          <a-table
            :dataSource="schema[selectedTable]"
            :columns="colColumns"
            rowKey="column"
            :pagination="false"
            size="small"
          />
          <a-divider />
          <a-button @click="loadPreview" :loading="previewLoading">Preview Data (LIMIT 10)</a-button>
          <a-table
            v-if="previewData.length"
            :dataSource="previewData"
            :columns="previewColumns"
            rowKey="row"
            size="small"
            style="margin-top: 12px"
            :scroll="{ x: 'max-content' }"
          />
        </a-card>
        <a-card v-else>
          <a-empty description="Select a table to view its schema" />
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { TableOutlined } from '@ant-design/icons-vue'

definePageMeta({ middleware: 'auth' })

const config = useRuntimeConfig()
const authStore = useAuthStore()
const headers = { Authorization: `Bearer ${authStore.token}` }

const schema = ref<Record<string, any[]>>({})
const selectedTable = ref('')
const tableFilter = ref('')
const previewData = ref<any[]>([])
const previewLoading = ref(false)

const filteredTables = computed(() => {
  const tables = Object.keys(schema.value)
  if (!tableFilter.value) return tables
  return tables.filter((t) => t.toLowerCase().includes(tableFilter.value.toLowerCase()))
})

const colColumns = [
  { title: 'Column', dataIndex: 'column', key: 'column' },
  { title: 'Type', dataIndex: 'type', key: 'type' },
  { title: 'Nullable', dataIndex: 'nullable', key: 'nullable', width: 80 },
  { title: 'Key', dataIndex: 'key', key: 'key', width: 80 },
  { title: 'Default', dataIndex: 'default', key: 'default' },
  { title: 'Extra', dataIndex: 'extra', key: 'extra' },
]

const previewColumns = ref<any[]>([])

async function fetchSchema() {
  try {
    const res = await $fetch('/api/n8n/schema', { baseURL: config.public.apiBaseUrl, headers })
    schema.value = res as Record<string, any[]>
    const keys = Object.keys(res)
    if (keys.length > 0) selectedTable.value = keys[0]
  } catch (e) {
    console.error('Failed to load schema:', e)
  }
}

  async function loadPreview() {
    if (!selectedTable.value) return
    previewLoading.value = true
    try {
      const res = await $fetch('/api/query', {
        baseURL: config.public.apiBaseUrl,
        method: 'POST',
        headers,
        body: { question: `Show me the first 10 rows from ${selectedTable.value}` },
      })
      if (res.sql_query) {
        previewData.value = [{ row: 'Use the Query tab to run custom SQL against this table' }]
      }
    } catch (e) {
      console.error('Preview failed:', e)
    } finally {
      previewLoading.value = false
    }
  }

onMounted(fetchSchema)
</script>
