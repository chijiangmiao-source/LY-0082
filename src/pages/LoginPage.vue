<template>
  <div class="login-page">
    <div class="login-card">
      <div class="login-header">
        <Heart :size="36" color="#E8A0BF" />
        <h1>月子中心探视管理系统</h1>
        <p>请登录以继续</p>
      </div>
      <div class="login-form">
        <div class="field">
          <label for="username">用户名</label>
          <InputText id="username" v-model="username" placeholder="请输入用户名" @keyup.enter="handleLogin" />
        </div>
        <div class="field">
          <label for="password">密码</label>
          <InputText id="password" v-model="password" type="password" placeholder="请输入密码" @keyup.enter="handleLogin" />
        </div>
        <Message v-if="errorMsg" severity="error" :closable="false">{{ errorMsg }}</Message>
        <Button label="登 录" @click="handleLogin" :loading="loading" class="login-btn" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { Heart } from 'lucide-vue-next'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Message from 'primevue/message'

const authStore = useAuthStore()
const router = useRouter()

const username = ref('')
const password = ref('')
const errorMsg = ref('')
const loading = ref(false)

async function handleLogin() {
  errorMsg.value = ''
  if (!username.value || !password.value) {
    errorMsg.value = '请输入用户名和密码'
    return
  }
  loading.value = true
  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch (e: any) {
    errorMsg.value = e.message || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #FFF8F0 0%, #F8D7E4 50%, #E8A0BF 100%);
}

.login-card {
  background: white;
  border-radius: 16px;
  padding: 48px 40px;
  width: 400px;
  box-shadow: 0 8px 32px rgba(232, 160, 191, 0.2);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin: 16px 0 8px;
  font-size: 22px;
  color: #2D3436;
  font-weight: 700;
}

.login-header p {
  color: #999;
  font-size: 14px;
  margin: 0;
}

.login-form .field {
  margin-bottom: 20px;
}

.login-form .field label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  color: #2D3436;
  font-weight: 500;
}

.login-form .field .p-inputtext {
  width: 100%;
}

.login-btn {
  width: 100%;
  margin-top: 8px;
}
</style>
