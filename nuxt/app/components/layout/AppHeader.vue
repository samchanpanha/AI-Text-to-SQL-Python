<template>
  <div class="header">
    <div class="header-left">
      <MenuUnfoldOutlined v-if="appStore.sidebarCollapsed" class="header-trigger" @click="appStore.toggleSidebar()" />
      <MenuFoldOutlined v-else class="header-trigger" @click="appStore.toggleSidebar()" />
      <a-breadcrumb class="header-breadcrumb">
        <a-breadcrumb-item>{{ currentTab?.title || 'Dashboard' }}</a-breadcrumb-item>
      </a-breadcrumb>
    </div>
    <div class="header-right">
      <a-tooltip title="Toggle Theme">
        <SunOutlined v-if="appStore.isDark" class="header-icon" @click="appStore.toggleTheme()" />
        <MoonOutlined v-else class="header-icon" @click="appStore.toggleTheme()" />
      </a-tooltip>
      <a-dropdown :trigger="['click']">
        <span class="header-user">
          <a-avatar :size="28" style="background-color: #1890ff">
            {{ authStore.username.charAt(0).toUpperCase() }}
          </a-avatar>
          <span class="header-username">{{ authStore.username }}</span>
        </span>
        <template #overlay>
          <a-menu>
            <a-menu-item @click="router.push('/profile')">
              <UserOutlined /> Profile
            </a-menu-item>
            <a-menu-divider />
            <a-menu-item @click="handleLogout">
              <LogoutOutlined /> Logout
            </a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '~/stores/app'
import { useAuthStore } from '~/stores/auth'
import { useTabsStore } from '~/stores/tabs'
import {
  MenuUnfoldOutlined, MenuFoldOutlined, SunOutlined, MoonOutlined,
  UserOutlined, LogoutOutlined,
} from '@ant-design/icons-vue'

const router = useRouter()
const appStore = useAppStore()
const authStore = useAuthStore()
const tabsStore = useTabsStore()

const currentTab = computed(() => tabsStore.activeTab)

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.header {
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  flex-shrink: 0;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-trigger {
  font-size: 18px;
  cursor: pointer;
  color: #666;
}
.header-trigger:hover {
  color: #1890ff;
}
.header-breadcrumb {
  font-size: 14px;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}
.header-icon {
  font-size: 18px;
  cursor: pointer;
  color: #666;
}
.header-icon:hover {
  color: #1890ff;
}
.header-user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}
.header-user:hover {
  background: #f5f5f5;
}
.header-username {
  font-size: 14px;
}
</style>
