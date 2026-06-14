import { defineStore } from 'pinia'

export interface TabItem {
  key: string
  title: string
  icon?: string
  closable: boolean
  keepAlive: boolean
}

interface TabsState {
  tabs: TabItem[]
  activeKey: string
}

const DEFAULT_TABS: TabItem[] = [
  { key: '/dashboard', title: 'Dashboard', icon: 'DashboardOutlined', closable: false, keepAlive: true },
]

export const useTabsStore = defineStore('tabs', {
  state: (): TabsState => ({
    tabs: [...DEFAULT_TABS],
    activeKey: '/dashboard',
  }),
  getters: {
    activeTab: (state) => state.tabs.find((t) => t.key === state.activeKey),
    tabKeys: (state) => state.tabs.map((t) => t.key),
  },
  actions: {
    openTab(tab: TabItem) {
      const exists = this.tabs.find((t) => t.key === tab.key)
      if (!exists) {
        this.tabs.push(tab)
      }
      this.activeKey = tab.key
    },
    closeTab(key: string) {
      const idx = this.tabs.findIndex((t) => t.key === key)
      if (idx === -1 || !this.tabs[idx].closable) return
      this.tabs.splice(idx, 1)
      if (this.activeKey === key) {
        this.activeKey = this.tabs[Math.min(idx, this.tabs.length - 1)]?.key || '/dashboard'
      }
    },
    closeOthers(key: string) {
      this.tabs = this.tabs.filter((t) => !t.closable || t.key === key)
      this.activeKey = key
    },
    closeAll() {
      this.tabs = this.tabs.filter((t) => !t.closable)
      this.activeKey = this.tabs[0]?.key || '/dashboard'
    },
    closeRight(key: string) {
      const idx = this.tabs.findIndex((t) => t.key === key)
      if (idx === -1) return
      this.tabs = this.tabs.filter((t, i) => !t.closable || i <= idx)
      this.activeKey = key
    },
    setActiveKey(key: string) {
      this.activeKey = key
    },
    refresh(key: string) {
      const tab = this.tabs.find((t) => t.key === key)
      if (tab) {
        tab.keepAlive = false
        setTimeout(() => { tab.keepAlive = true }, 50)
      }
    },
  },
})
