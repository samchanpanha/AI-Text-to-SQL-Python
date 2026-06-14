import { defineStore } from 'pinia'
import type { User } from '~/types/auth'

interface AuthState {
  token: string | null
  user: User | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    token: null,
    user: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.token,
    isAdmin: (state) => state.user?.role === 'admin',
    username: (state) => state.user?.username ?? '',
  },
  actions: {
    setToken(token: string) {
      this.token = token
      localStorage.setItem('auth_token', token)
    },
    setUser(user: User) {
      this.user = user
      localStorage.setItem('auth_user', JSON.stringify(user))
    },
    loadFromStorage() {
      const token = localStorage.getItem('auth_token')
      const user = localStorage.getItem('auth_user')
      if (token) this.token = token
      if (user) {
        try {
          this.user = JSON.parse(user)
        } catch {
          localStorage.removeItem('auth_user')
        }
      }
    },
    logout() {
      this.token = null
      this.user = null
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user')
    },
  },
})
