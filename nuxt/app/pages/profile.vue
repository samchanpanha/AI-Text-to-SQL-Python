<template>
  <div class="profile-page">
    <PageHeader title="Profile" description="Your account settings and API key" />

    <a-row :gutter="16">
      <a-col :span="12">
        <a-card title="Account Info">
          <a-descriptions :column="1" size="large">
            <a-descriptions-item label="Username">{{ authStore.user?.username }}</a-descriptions-item>
            <a-descriptions-item label="Email">{{ authStore.user?.email }}</a-descriptions-item>
            <a-descriptions-item label="Role">
              <a-tag :color="authStore.isAdmin ? 'red' : 'blue'">{{ authStore.user?.role }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="Rate Limit">{{ authStore.user?.rate_limit_per_minute }} requests/minute</a-descriptions-item>
            <a-descriptions-item label="Created">{{ authStore.user?.created_at }}</a-descriptions-item>
          </a-descriptions>
        </a-card>
      </a-col>
      <a-col :span="12">
        <a-card title="API Key">
          <p style="color: #999; font-size: 13px;">
            Use this key for programmatic access via the <code>X-API-Key</code> header.
            This key will only be shown once after regeneration.
          </p>
          <a-input-search
            v-model:value="displayKey"
            :readonly="true"
            placeholder="Click regenerate to create a key"
          >
            <template #enterButton>
              <a-button @click="handleRegenerate" :loading="generating">Regenerate</a-button>
            </template>
          </a-input-search>
          <div v-if="newKey" style="margin-top: 12px">
            <a-alert
              type="warning"
              message="Save this key — it will not be shown again"
              :description="newKey"
              show-icon
              closable
              @close="newKey = ''"
            />
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import { useAuthStore } from '~/stores/auth'
import { useAuth } from '~/composables/useAuth'

definePageMeta({ middleware: 'auth' })

const authStore = useAuthStore()
const { regenerateApiKey } = useAuth()

const displayKey = ref(authStore.user?.api_key ? maskKey(authStore.user.api_key) : '')
const generating = ref(false)
const newKey = ref('')

function maskKey(key: string): string {
  if (key.length <= 12) return key
  return key.slice(0, 8) + '...' + key.slice(-4)
}

async function handleRegenerate() {
  generating.value = true
  try {
    const key = await regenerateApiKey()
    newKey.value = key
    displayKey.value = maskKey(key)
  } catch (e: any) {
    message.error(e.message || 'Failed to regenerate key')
  } finally {
    generating.value = false
  }
}
</script>
