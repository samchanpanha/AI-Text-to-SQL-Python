<template>
  <div class="sidebar">
    <div class="sidebar-logo" @click="navigateTo('/dashboard')">
      <DatabaseOutlined class="sidebar-logo-icon" />
      <span v-if="!appStore.sidebarCollapsed" class="sidebar-logo-text">Text-to-SQL</span>
    </div>
    <a-menu
      :selected-keys="[activeKey]"
      :inline-collapsed="appStore.sidebarCollapsed"
      mode="inline"
      class="sidebar-menu"
      @click="handleMenuClick"
    >
      <a-menu-item key="/dashboard">
        <DashboardOutlined />
        <span>Dashboard</span>
      </a-menu-item>
      <a-menu-item key="/query">
        <SearchOutlined />
        <span>Query</span>
      </a-menu-item>
      <a-menu-item key="/chat">
        <MessageOutlined />
        <span>Chat</span>
      </a-menu-item>
      <a-menu-item key="/tasks">
        <ScheduleOutlined />
        <span>Tasks</span>
      </a-menu-item>
      <a-sub-menu key="logs" title="Logs">
        <template #icon><FileTextOutlined /></template>
        <a-menu-item key="/logs/audit">Audit Logs</a-menu-item>
        <a-menu-item key="/logs/llm">LLM Logs</a-menu-item>
        <a-menu-item key="/logs/executions">Executions</a-menu-item>
      </a-sub-menu>
      <a-menu-item key="/schema">
        <TableOutlined />
        <span>Schema</span>
      </a-menu-item>
      <a-menu-item v-if="authStore.isAdmin" key="/admin/users">
        <TeamOutlined />
        <span>Users</span>
      </a-menu-item>
    </a-menu>
    <div class="sidebar-footer">
      <a-menu mode="inline" :inline-collapsed="appStore.sidebarCollapsed" selectable>
        <a-menu-item key="/profile">
          <UserOutlined />
          <span>Profile</span>
        </a-menu-item>
      </a-menu>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '~/stores/app'
import { useAuthStore } from '~/stores/auth'
import { useTabsStore } from '~/stores/tabs'
import {
  DatabaseOutlined, DashboardOutlined, SearchOutlined, MessageOutlined,
  ScheduleOutlined, FileTextOutlined, TableOutlined, TeamOutlined, UserOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const tabsStore = useTabsStore()

const route = useRoute()
const activeKey = computed(() => {
  const path = route.path
  if (path.startsWith('/tasks')) return '/tasks'
  if (path.startsWith('/logs/audit')) return '/logs/audit'
  if (path.startsWith('/logs/llm')) return '/logs/llm'
  if (path.startsWith('/logs/executions')) return '/logs/executions'
  if (path.startsWith('/logs')) return '/logs/audit'
  if (path.startsWith('/admin')) return '/admin/users'
  return path
})

function handleMenuClick({ key }: { key: string }) {
  router.push(key)
}
</script>

<style scoped>
.sidebar {
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
  width: 220px;
  background: #001529;
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
  z-index: 100;
}
.sidebar-collapsed .sidebar {
  width: 80px;
}
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  cursor: pointer;
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.sidebar-logo-icon {
  font-size: 24px;
  color: #1890ff;
}
.sidebar-logo-text {
  white-space: nowrap;
  overflow: hidden;
}
.sidebar-menu {
  flex: 1;
  overflow-y: auto;
  border-inline-end: none !important;
}
.sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
:deep(.sidebar-menu.ant-menu-dark),
:deep(.sidebar-footer .ant-menu-dark) {
  background: transparent;
}
</style>
