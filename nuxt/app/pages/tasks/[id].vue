<template>
  <div class="task-detail-page" v-if="task">
    <PageHeader :title="task.name" :description="`Cron: ${task.cron_expression}`">
      <template #actions>
        <a-button v-if="authStore.isAdmin" type="primary" @click="handleExecute">
          <PlayCircleOutlined /> Execute Now
        </a-button>
        <a-button v-if="authStore.isAdmin" danger @click="handleDelete">
          <DeleteOutlined /> Delete
        </a-button>
      </template>
    </PageHeader>

    <a-card title="Task Info" class="detail-card">
      <a-descriptions :column="2" size="small">
        <a-descriptions-item label="Name">{{ task.name }}</a-descriptions-item>
        <a-descriptions-item label="Cron">{{ task.cron_expression }}</a-descriptions-item>
        <a-descriptions-item label="Timezone">{{ task.timezone }}</a-descriptions-item>
        <a-descriptions-item label="Enabled"><a-switch :checked="task.enabled" disabled /></a-descriptions-item>
        <a-descriptions-item label="Description" :span="2">{{ task.description || '—' }}</a-descriptions-item>
      </a-descriptions>
    </a-card>

    <a-card title="Reports" class="detail-card">
      <template #extra>
        <a-button v-if="authStore.isAdmin" size="small" type="primary" @click="showReportForm = true">
          <PlusOutlined /> Add Report
        </a-button>
      </template>
      <a-table :dataSource="reports" :columns="reportColumns" rowKey="id" :pagination="false" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'actions'">
            <a-button v-if="authStore.isAdmin" size="small" danger @click="handleDeleteReport(record)">Delete</a-button>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-card title="Execution Logs" class="detail-card">
      <a-table :dataSource="executionLogs" :columns="execColumns" rowKey="id" :pagination="false" size="small">
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'status'">
            <a-tag :color="record.status === 'completed' ? 'green' : record.status === 'failed' ? 'red' : 'orange'">
              {{ record.status }}
            </a-tag>
          </template>
        </template>
      </a-table>
    </a-card>

    <a-modal v-model:open="showReportForm" title="Add Report" @ok="handleAddReport" :confirmLoading="saving">
      <a-form layout="vertical">
        <a-form-item label="Name" required>
          <a-input v-model:value="reportForm.name" />
        </a-form-item>
        <a-form-item label="SQL Query" required>
          <a-textarea v-model:value="reportForm.sql_query" :rows="6" />
        </a-form-item>
        <a-form-item label="Sheet Name">
          <a-input v-model:value="reportForm.sheet_name" placeholder="Sheet1" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import { PlayCircleOutlined, DeleteOutlined, PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '~/stores/auth'
import type { TaskResponse, ReportDefinitionResponse, TaskExecutionLog } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const headers = { Authorization: `Bearer ${authStore.token}` }

const taskId = computed(() => Number(route.params.id))
const task = ref<TaskResponse | null>(null)
const reports = ref<ReportDefinitionResponse[]>([])
const executionLogs = ref<TaskExecutionLog[]>([])
const showReportForm = ref(false)
const saving = ref(false)
const reportForm = reactive({ name: '', sql_query: '', sheet_name: 'Sheet1', format: 'xlsx', sort_order: 0 })

const reportColumns = [
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Format', dataIndex: 'format', key: 'format', width: 80 },
  { title: 'Sheet', dataIndex: 'sheet_name', key: 'sheet_name', width: 100 },
  { title: 'Order', dataIndex: 'sort_order', key: 'sort_order', width: 60 },
  { title: 'Actions', key: 'actions', width: 80 },
]

const execColumns = [
  { title: 'Status', dataIndex: 'status', key: 'status', width: 100 },
  { title: 'Started', dataIndex: 'started_at', key: 'started_at', width: 180 },
  { title: 'Duration', dataIndex: 'duration_ms', key: 'duration_ms', width: 100 },
  { title: 'Rows', dataIndex: 'rows_processed', key: 'rows', width: 80 },
  { title: 'Error', dataIndex: 'error_message', key: 'error' },
]

async function fetchAll() {
  try {
    const [t, r, l] = await Promise.all([
      $fetch(`/api/tasks/${taskId.value}`, { baseURL: config.public.apiBaseUrl, headers }),
      $fetch(`/api/tasks/${taskId.value}/reports`, { baseURL: config.public.apiBaseUrl, headers }),
      $fetch(`/api/tasks/${taskId.value}/logs`, { baseURL: config.public.apiBaseUrl, headers }),
    ])
    task.value = t as TaskResponse
    reports.value = r as ReportDefinitionResponse[]
    executionLogs.value = l as TaskExecutionLog[]
  } catch (e) {
    message.error('Failed to load task details')
    router.push('/tasks')
  }
}

async function handleExecute() {
  try {
    await $fetch(`/api/tasks/${taskId.value}/execute`, {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      headers,
    })
    message.success('Task execution started')
    await fetchAll()
  } catch (e: any) {
    message.error(e.message || 'Execute failed')
  }
}

async function handleDelete() {
  try {
    await $fetch(`/api/tasks/${taskId.value}`, {
      baseURL: config.public.apiBaseUrl,
      method: 'DELETE',
      headers,
    })
    message.success('Task deleted')
    router.push('/tasks')
  } catch (e: any) {
    message.error(e.message || 'Delete failed')
  }
}

async function handleAddReport() {
  if (!reportForm.name || !reportForm.sql_query) return
  saving.value = true
  try {
    await $fetch(`/api/tasks/${taskId.value}/reports`, {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      headers,
      body: reportForm,
    })
    message.success('Report added')
    showReportForm.value = false
    reportForm.name = ''
    reportForm.sql_query = ''
    await fetchAll()
  } catch (e: any) {
    message.error(e.message || 'Failed to add report')
  } finally {
    saving.value = false
  }
}

async function handleDeleteReport(record: ReportDefinitionResponse) {
  try {
    await $fetch(`/api/tasks/${taskId.value}/reports/${record.id}`, {
      baseURL: config.public.apiBaseUrl,
      method: 'DELETE',
      headers,
    })
    message.success('Report deleted')
    await fetchAll()
  } catch (e: any) {
    message.error(e.message || 'Delete failed')
  }
}

onMounted(fetchAll)
</script>

<style scoped>
.detail-card {
  margin-bottom: 16px;
}
</style>
