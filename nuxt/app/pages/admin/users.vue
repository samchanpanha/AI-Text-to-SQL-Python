<template>
  <div class="users-page" v-if="authStore.isAdmin">
    <div class="users-header">
      <PageHeader title="User Management" description="Manage system users and roles">
        <template #actions>
          <a-button type="primary" @click="showForm = true; editingUser = null">
            <PlusOutlined /> Create User
          </a-button>
        </template>
      </PageHeader>
    </div>
    <a-table
      :dataSource="users"
      :columns="columns"
      :loading="loading"
      rowKey="id"
      :pagination="{ pageSize: 20, showSizeChanger: true }"
    >
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'role'">
          <a-tag :color="record.role === 'admin' ? 'red' : 'blue'">{{ record.role }}</a-tag>
        </template>
        <template v-if="column.key === 'is_active'">
          <a-switch :checked="record.is_active" disabled />
        </template>
        <template v-if="column.key === 'rate_limit'">
          {{ record.rate_limit_per_minute }}/min
        </template>
        <template v-if="column.key === 'actions'">
          <a-space>
            <a-button size="small" @click="editUser(record)">Edit</a-button>
            <a-button size="small" danger @click="handleDelete(record)">Delete</a-button>
          </a-space>
        </template>
      </template>
    </a-table>

    <a-modal
      v-model:open="showForm"
      :title="editingUser ? 'Edit User' : 'Create User'"
      @ok="handleSave"
      :confirmLoading="saving"
    >
      <a-form layout="vertical">
        <a-form-item label="Username" required>
          <a-input v-model:value="form.username" />
        </a-form-item>
        <a-form-item label="Email" required>
          <a-input v-model:value="form.email" />
        </a-form-item>
        <a-form-item label="Password" :required="!editingUser">
          <a-input-password v-model:value="form.password" :placeholder="editingUser ? 'Leave blank to keep current' : ''" />
        </a-form-item>
        <a-form-item label="Role">
          <a-select v-model:value="form.role" :options="[{ label: 'User', value: 'user' }, { label: 'Admin', value: 'admin' }]" />
        </a-form-item>
        <a-form-item v-if="editingUser" label="Active">
          <a-switch v-model:checked="form.is_active" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup lang="ts">
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useAuthStore } from '~/stores/auth'
import type { User, UserCreate, UserUpdate } from '~/types/auth'

definePageMeta({ middleware: 'auth' })

const authStore = useAuthStore()
const config = useRuntimeConfig()
const headers = { Authorization: `Bearer ${authStore.token}` }

const users = ref<User[]>([])
const loading = ref(true)
const saving = ref(false)
const showForm = ref(false)
const editingUser = ref<User | null>(null)
const form = reactive({ username: '', email: '', password: '', role: 'user', is_active: true })

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
  { title: 'Username', dataIndex: 'username', key: 'username' },
  { title: 'Email', dataIndex: 'email', key: 'email' },
  { title: 'Role', dataIndex: 'role', key: 'role', width: 80 },
  { title: 'Active', dataIndex: 'is_active', key: 'is_active', width: 80 },
  { title: 'Rate Limit', dataIndex: 'rate_limit_per_minute', key: 'rate_limit', width: 100 },
  { title: 'Created', dataIndex: 'created_at', key: 'created_at', width: 180 },
  { title: 'Actions', key: 'actions', width: 130 },
]

async function fetchUsers() {
  loading.value = true
  try {
    const res = await $fetch('/api/auth/users', { baseURL: config.public.apiBaseUrl, headers })
    users.value = res as User[]
  } catch (e) {
    console.error('Failed to load users:', e)
  } finally {
    loading.value = false
  }
}

function editUser(user: User) {
  editingUser.value = user
  form.username = user.username
  form.email = user.email
  form.role = user.role
  form.password = ''
  form.is_active = user.is_active
  showForm.value = true
}

async function handleSave() {
  saving.value = true
  try {
    if (editingUser.value) {
      const body: UserUpdate = { username: form.username, email: form.email, role: form.role as 'admin' | 'user', is_active: form.is_active }
      if (form.password) body.password = form.password
      await $fetch(`/api/auth/users/${editingUser.value.id}`, {
        baseURL: config.public.apiBaseUrl,
        method: 'PUT',
        headers,
        body,
      })
      message.success('User updated')
    } else {
      await $fetch('/api/auth/users', {
        baseURL: config.public.apiBaseUrl,
        method: 'POST',
        headers,
        body: { username: form.username, email: form.email, password: form.password, role: form.role },
      })
      message.success('User created')
    }
    showForm.value = false
    await fetchUsers()
  } catch (e: any) {
    message.error(e.message || 'Save failed')
  } finally {
    saving.value = false
  }
}

async function handleDelete(record: User) {
  try {
    await $fetch(`/api/auth/users/${record.id}`, {
      baseURL: config.public.apiBaseUrl,
      method: 'DELETE',
      headers,
    })
    message.success('User deleted')
    await fetchUsers()
  } catch (e: any) {
    message.error(e.message || 'Delete failed')
  }
}

onMounted(fetchUsers)
</script>

<style scoped>
.users-header {
  margin-bottom: 16px;
}
</style>
