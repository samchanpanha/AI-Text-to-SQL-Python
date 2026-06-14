import { useAuthStore } from '~/stores/auth'

export function useAuth() {
  const authStore = useAuthStore()
  const router = useRouter()
  const config = useRuntimeConfig()

  async function login(username: string, password: string) {
    const { data, error } = await useFetch('/api/auth/login', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: { username, password },
    })
    if (error.value) {
      throw new Error(error.value.statusMessage || 'Login failed')
    }
    const result = data.value as any
    authStore.setToken(result.access_token)
    authStore.setUser(result.user)
    return result.user
  }

  async function fetchMe() {
    const { data, error } = await useFetch('/api/auth/me', {
      baseURL: config.public.apiBaseUrl,
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (error.value) return null
    authStore.setUser(data.value as any)
    return data.value
  }

  async function regenerateApiKey() {
    const { data, error } = await useFetch('/api/auth/api-key', {
      baseURL: config.public.apiBaseUrl,
      method: 'POST',
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (error.value) throw new Error('Failed to regenerate API key')
    const result = data.value as any
    await fetchMe()
    return result.api_key as string
  }

  function logout() {
    authStore.logout()
    router.push('/login')
  }

  return { login, fetchMe, regenerateApiKey, logout }
}
