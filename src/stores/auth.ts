import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<{ id: number; username: string; role: string } | null>(null)

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    token.value = res.access_token
    localStorage.setItem('token', res.access_token)
    await fetchMe()
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
  }

  async function fetchMe() {
    try {
      user.value = await authApi.getMe()
    } catch {
      logout()
    }
  }

  return { token, user, isLoggedIn, isAdmin, login, logout, fetchMe }
})
