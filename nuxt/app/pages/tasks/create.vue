<template>
  <div class="create-task-page" v-if="authStore.isAdmin">
    <PageHeader title="Create Task" description="Define a new scheduled report task">
      <template #actions>
        <a-button @click="router.push('/tasks')">Cancel</a-button>
      </template>
    </PageHeader>

    <a-card>
      <a-form layout="vertical" :model="form">
        <a-form-item label="Task Name" required>
          <a-input v-model:value="form.name" placeholder="Daily Sales Report" />
        </a-form-item>
        <a-form-item label="Description">
          <a-textarea v-model:value="form.description" :rows="2" />
        </a-form-item>
        <a-form-item label="Cron Expression" required help="Format: minute hour day month weekday">
          <a-input v-model:value="form.cron_expression" placeholder="0 8 * * *" />
          <div style="margin-top: 4px;">
            <a-tag v-for="preset in presets" :key="preset.cron" style="cursor: pointer" @click="form.cron_expression = preset.cron">
              {{ preset.label }}
            </a-tag>
          </div>
        </a-form-item>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="Timezone">
              <a-select v-model:value="form.timezone" :options="timezones" />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="Max Retries">
              <a-input-number v-model:value="form.max_retries" :min="0" :max="10" />
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item>
          <a-button type="primary" :loading="saving" @click="handleCreate">Create Task</a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import { useAuthStore } from '~/stores/auth'

definePageMeta({ middleware: 'auth' })

const router = useRouter()
const authStore = useAuthStore()
const config = useRuntimeConfig()
const headers = { Authorization: `Bearer ${authStore.token}` }

const saving = ref(false)

const form = reactive({
  name: '',
  description: '',
  cron_expression: '0 8 * * *',
  timezone: 'UTC',
  enabled: true,
  max_retries: 0,
  retry_delay_minutes: 5,
})

const presets = [
  { label: 'Daily 8 AM', cron: '0 8 * * *' },
  { label: 'Daily 6 PM', cron: '0 18 * * *' },
  { label: 'Every Hour', cron: '0 * * * *' },
  { label: 'Monday 9 AM', cron: '0 9 * * 1' },
  { label: 'Month Start', cron: '0 9 1 * *' },
]

const timezones = ['UTC', 'America/New_York', 'America/Chicago', 'America/Denver', 'America/Los_Angeles', 'Europe/London', 'Europe/Paris', 'Asia/Tokyo', 'Asia/Shanghai', 'Australia/Sydney'].map(tz => ({ label: tz, value: tz }))

async function handleCreate() {
  if (!form.name || !form.cron_expression) return
  saving.value = true
  try {
    await $fetch('/api/tasks', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      headers,
      body: form,
    })
    message.success('Task created')
    router.push('/tasks')
  } catch (e: any) {
    message.error(e.message || 'Create failed')
  } finally {
    saving.value = false
  }
}
</script>
