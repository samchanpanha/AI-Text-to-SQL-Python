<template>
  <div class="tabs-bar" v-if="tabsStore.tabs.length > 1">
    <a-tabs
      v-model:activeKey="tabsStore.activeKey"
      type="editable-card"
      hideAdd
      size="small"
      @tabClick="handleTabClick"
      @edit="handleTabClose"
    >
      <a-tab-pane
        v-for="tab in tabsStore.tabs"
        :key="tab.key"
        :tab="tab.title"
        :closable="tab.closable"
      />
    </a-tabs>
    <a-dropdown :trigger="['click']" class="tabs-dropdown">
      <span class="tabs-more"><DownOutlined /></span>
      <template #overlay>
        <a-menu @click="handleDropdownClick">
          <a-menu-item key="close-others">Close Others</a-menu-item>
          <a-menu-item key="close-all">Close All</a-menu-item>
          <a-menu-item key="close-right">Close to the Right</a-menu-item>
          <a-menu-divider />
          <a-menu-item key="refresh">Refresh Current</a-menu-item>
        </a-menu>
      </template>
    </a-dropdown>
  </div>
</template>

<script setup lang="ts">
import { useTabsStore } from '~/stores/tabs'
import { DownOutlined } from '@ant-design/icons-vue'

const router = useRouter()
const tabsStore = useTabsStore()

function handleTabClick(key: string) {
  router.push(key)
}

function handleTabClose(key: string | MouseEvent) {
  if (typeof key === 'string') {
    tabsStore.closeTab(key)
  }
}

function handleDropdownClick({ key }: { key: string }) {
  const active = tabsStore.activeKey
  switch (key) {
    case 'close-others': tabsStore.closeOthers(active); break
    case 'close-all': tabsStore.closeAll(); break
    case 'close-right': tabsStore.closeRight(active); break
    case 'refresh': tabsStore.refresh(active); break
  }
}
</script>

<style scoped>
.tabs-bar {
  display: flex;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #f0f0f0;
  padding: 0 8px;
  flex-shrink: 0;
}
.tabs-bar :deep(.ant-tabs) {
  flex: 1;
  margin-bottom: 0;
}
.tabs-bar :deep(.ant-tabs-nav) {
  margin-bottom: 0;
}
.tabs-more {
  cursor: pointer;
  padding: 0 8px;
  color: #999;
  font-size: 12px;
}
.tabs-more:hover {
  color: #1890ff;
}
</style>
