<template>
  <div class="tasks-page">
    <div class="tasks-header">
      <PageHeader title="Scheduled Tasks" description="Manage automated report generation tasks">
        <template #actions>
          <a-button v-if="authStore.isAdmin" type="primary" @click="router.push('/tasks/create')">
            <PlusOutlined /> Create Task
          </a-button>
        </template>
      </PageHeader>
    </div>
    <a-table
      :dataSource="tasks"
      :columns="columns"
      :loading="loading"
      rowKey="id"
      :pagination="{ pageSize: 20, showSizeChanger: true }"
      @row="(record) => ({ style: { cursor: 'pointer' }, onClick: () => router.push(`/tasks/${record.id}`) })"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'enabled'">
          <a-switch :checked="record.enabled" disabled />
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click.stop="router.push(`/tasks/${record.id}`)">Detail</a-button>
            <a-button v-if="authStore.isAdmin" size="small" danger @click.stop="handleDelete(record)">Delete</a-button>
          </a-space>
        </template>
      </template>
    </a-table>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '~/stores/auth'
import type { TaskResponse } from '~/types/api'

definePageMeta({ middleware: 'auth' })

const router = useRouter()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const headers = { Authorization: `Bearer ${authStore.token}` }

const tasks = ref<TaskResponse[]>([])
const loading = ref(true)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: 'Name', dataIndex: 'name', key: 'name' },
  { title: 'Cron', dataIndex: 'cron_expression', key: 'cron', width: 130 },
  { title: 'Timezone', dataIndex: 'timezone', key: 'timezone', width: 100 },
  { title: 'Enabled', dataIndex: 'enabled', key: 'enabled', width: 80 },
  { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: 'Actions', key: 'actions', width: 140 },
]

async function fetchTasks() {
  loading.value = true
  try {
    const res = await $fetch('/api/tasks', { baseURL: config.public.apiBaseUrl, headers })
    tasks.value = res as TaskResponse[]
  } catch (e) {
    console.error('Failed to load tasks:', e)
  } finally {
    loading.value = false
  }
}

async function handleDelete(record: TaskResponse) {
  try {
    await $fetch(`/api/tasks/${record.id}`, {
      baseURL: config.public.apiBaseUrl,
      method: 'DELETE',
      headers,
    })
    message.success('Task deleted')
    await fetchTasks()
  } catch (e: any) {
    message.error(e.message || 'Delete failed')
  }
}

onMounted(fetchTasks)
</script>

<style scoped>
.tasks-header {
  margin-bottom: 16px;
}
</style>
