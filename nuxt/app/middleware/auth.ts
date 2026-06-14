import { useAuthStore } from '~/stores/auth'

export default defineNuxtRouteMiddleware((to) => {
  const authStore = useAuthStore()
  authStore.loadFromStorage()

  if (to.path === '/login') {
    if (authStore.isAuthenticated) {
      return navigateTo('/dashboard')
    }
    return
  }

  if (!authStore.isAuthenticated) {
    return navigateTo('/login')
  }
})
