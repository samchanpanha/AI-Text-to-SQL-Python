<template>
  <div class="login-card">
    <div class="login-header">
      <DatabaseOutlined class="login-icon" />
      <h1>Text-to-SQL Admin</h1>
      <p>Ask questions about your data in plain English</p>
    </div>
    <a-form :model="form" @submit.prevent="handleLogin" layout="vertical">
      <a-form-item label="Username" name="username" :rules="[{ required: true, message: 'Please enter username' }]">
        <a-input v-model:value="form.username" size="large" placeholder="Username" autocomplete="username">
          <template #prefix><UserOutlined /></template>
        </a-input>
      </a-form-item>
      <a-form-item label="Password" name="password" :rules="[{ required: true, message: 'Please enter password' }]">
        <a-input-password v-model:value="form.password" size="large" placeholder="Password" autocomplete="current-password">
          <template #prefix><LockOutlined /></template>
        </a-input-password>
      </a-form-item>
      <a-form-item>
        <a-button type="primary" html-type="submit" :loading="loading" block size="large">
          Log In
        </a-button>
      </a-form-item>
    </a-form>
    <div v-if="error" class="login-error">
      <a-alert :message="error" type="error" show-icon closable @close="error = ''" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { DatabaseOutlined, UserOutlined, LockOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '~/stores/auth'
import { useAuth } from '~/composables/useAuth'

definePageMeta({ layout: 'default', middleware: 'auth' })

const authStore = useAuthStore()
const { login } = useAuth()
const router = useRouter()

const form = reactive({ username: 'admin', password: '' })
const loading = ref(false)
const error = ref('')

async function handleLogin() {
  if (!form.username || !form.password) return
  loading.value = true
  error.value = ''
  try {
    await login(form.username, form.password)
    router.push('/dashboard')
  } catch (e: any) {
    error.value = e.message || 'Invalid username or password'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  padding: 40px;
}
.login-header {
  text-align: center;
  margin-bottom: 32px;
}
.login-icon {
  font-size: 48px;
  color: #1890ff;
}
.login-header h1 {
  margin: 12px 0 4px;
  font-size: 24px;
}
.login-header p {
  margin: 0;
  color: #999;
  font-size: 14px;
}
.login-error {
  margin-top: 16px;
}
</style>
