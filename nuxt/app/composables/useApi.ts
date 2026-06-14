import { useAuthStore } from '~/stores/auth'

export function useApi() {
  const authStore = useAuthStore()
  const config = useRuntimeConfig()
  const router = useRouter()

  const api = $fetch.create({
    baseURL: config.public.apiBaseUrl,
    headers: {
      'Content-Type': 'application/json',
    },
    onRequest({ options }) {
      if (authStore.token) {
        options.headers = {
          ...options.headers,
          Authorization: `Bearer ${authStore.token}`,
        }
      }
    },
    onResponseError({ response }) {
      if (response.status === 401) {
        authStore.logout()
        router.push('/login')
      }
    },
  })

  return api
}
