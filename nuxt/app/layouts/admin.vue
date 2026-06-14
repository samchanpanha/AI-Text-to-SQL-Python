<template>
  <div class="admin-layout" :class="{ 'sidebar-collapsed': appStore.sidebarCollapsed }">
    <AppSidebar />
    <div class="admin-main">
      <AppHeader />
      <AppTabs />
      <div class="admin-content">
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useAppStore } from '~/stores/app'
const appStore = useAppStore()
</script>

<style scoped>
.admin-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}
.admin-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  margin-left: 220px;
  transition: margin-left 0.2s;
}
.sidebar-collapsed .admin-main {
  margin-left: 80px;
}
.admin-content {
  flex: 1;
  overflow: auto;
  padding: 16px 24px;
  background: #f5f5f5;
}
:root .admin-content {
  background: #f5f5f5;
}
</style>
