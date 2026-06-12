import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { authApi } from '@/api'

function getUserFromStorage() {
  try {
    const data = localStorage.getItem('user')
    return data ? JSON.parse(data) : null
  } catch {
    return null
  }
}

function parseJwtPayload(token: string): { exp?: number } | null {
  try {
    const base64Url = token.split('.')[1]
    if (!base64Url) return null
    const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
    return JSON.parse(decodeURIComponent(escape(window.atob(base64))))
  } catch {
    return null
  }
}

function isTokenValid(token: string | null): boolean {
  if (!token) return false
  const payload = parseJwtPayload(token)
  if (!payload?.exp) return true
  return payload.exp * 1000 > Date.now()
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<{ id: number; username: string; role: string } | null>(getUserFromStorage())
  const initialized = ref(false)

  const isLoggedIn = computed(() => !!token.value && isTokenValid(token.value) && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  watch(token, (newVal) => {
    if (newVal) {
      localStorage.setItem('token', newVal)
    } else {
      localStorage.removeItem('token')
    }
  })

  watch(user, (newVal) => {
    if (newVal) {
      localStorage.setItem('user', JSON.stringify(newVal))
    } else {
      localStorage.removeItem('user')
    }
  }, { deep: true })

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
    localStorage.removeItem('user')
  }

  async function fetchMe() {
    try {
      if (!isTokenValid(token.value)) {
        logout()
        return
      }
      const userData = await authApi.getMe()
      user.value = userData
      localStorage.setItem('user', JSON.stringify(userData))
    } catch {
      logout()
    }
  }

  async function initAuth() {
    if (initialized.value) return
    initialized.value = true

    if (!isTokenValid(token.value)) {
      logout()
      return
    }

    if (token.value) {
      try {
        const userData = await authApi.getMe()
        user.value = userData
        localStorage.setItem('user', JSON.stringify(userData))
      } catch {
        logout()
      }
    } else {
      logout()
    }
  }

  return { token, user, isLoggedIn, isAdmin, login, logout, fetchMe, initAuth }
})
