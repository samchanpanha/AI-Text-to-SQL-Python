import { defineStore } from 'pinia'
import type { ThemeConfig } from 'ant-design-vue/es/config-provider/context'

interface AppState {
  sidebarCollapsed: boolean
  theme: 'light' | 'dark'
}

export const useAppStore = defineStore('app', {
  state: (): AppState => ({
    sidebarCollapsed: false,
    theme: (localStorage.getItem('app_theme') as 'light' | 'dark') || 'light',
  }),
  getters: {
    themeConfig: (state): ThemeConfig => {
      if (state.theme === 'dark') {
        return { algorithm: 'dark' as any }
      }
      return { algorithm: 'default' as any }
    },
    isDark: (state) => state.theme === 'dark',
  },
  actions: {
    toggleSidebar() {
      this.sidebarCollapsed = !this.sidebarCollapsed
    },
    toggleTheme() {
      this.theme = this.theme === 'light' ? 'dark' : 'light'
      localStorage.setItem('app_theme', this.theme)
    },
  },
})
