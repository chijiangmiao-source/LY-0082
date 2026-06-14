<template>
  <div class="app-layout">
    <div class="sidebar" :class="{ collapsed: collapsed }">
      <div class="sidebar-header">
        <div class="logo" v-if="!collapsed">
          <Heart class="logo-icon" :size="24" />
          <span class="logo-text">月子中心</span>
        </div>
        <button class="collapse-btn" @click="collapsed = !collapsed">
          <ChevronLeft v-if="!collapsed" :size="18" />
          <ChevronRight v-else :size="18" />
        </button>
      </div>
      <nav class="sidebar-nav">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: $route.path === item.path }"
        >
          <component :is="item.icon" :size="20" />
          <span v-if="!collapsed" class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>
      <div class="sidebar-footer" v-if="!collapsed">
        <div class="user-info">
          <User :size="16" />
          <span>{{ authStore.user?.username || '用户' }}</span>
        </div>
        <button class="logout-btn" @click="handleLogout">
          <LogOut :size="16" />
          <span>退出登录</span>
        </button>
      </div>
    </div>
    <div class="main-content">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
  LayoutDashboard,
  Building2,
  Users,
  CalendarCheck,
  ShieldCheck,
  DoorOpen,
  Ban,
  Heart,
  User,
  LogOut,
  ChevronLeft,
  ChevronRight,
  BookmarkCheck,
  Wallet,
} from 'lucide-vue-next'

const authStore = useAuthStore()
const router = useRouter()
const collapsed = ref(false)

const navItems = [
  { path: '/', label: '统计总览', icon: LayoutDashboard },
  { path: '/rooms', label: '楼层房间', icon: Building2 },
  { path: '/residents', label: '住户档案', icon: Users },
  { path: '/whitelist', label: '访客白名单', icon: BookmarkCheck },
  { path: '/appointments', label: '探视预约', icon: CalendarCheck },
  { path: '/checkin', label: '前台核验', icon: ShieldCheck },
  { path: '/deposit-items', label: '押金与物品', icon: Wallet },
  { path: '/checkout', label: '离开登记', icon: DoorOpen },
  { path: '/blacklist', label: '黑名单', icon: Ban },
]

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-layout {
  display: flex;
  min-height: 100vh;
}

.sidebar {
  width: 260px;
  background: linear-gradient(180deg, #E8A0BF 0%, #D4899F 100%);
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
  flex-shrink: 0;
}

.sidebar.collapsed {
  width: 64px;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
}

.logo-icon {
  flex-shrink: 0;
}

.logo-text {
  font-size: 18px;
  font-weight: 700;
  white-space: nowrap;
}

.collapse-btn {
  background: rgba(255, 255, 255, 0.2);
  border: none;
  color: white;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.collapse-btn:hover {
  background: rgba(255, 255, 255, 0.3);
}

.sidebar-nav {
  flex: 1;
  padding: 12px 8px;
  overflow-y: auto;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  color: rgba(255, 255, 255, 0.8);
  text-decoration: none;
  border-radius: 8px;
  margin-bottom: 4px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.15);
  color: white;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.25);
  color: white;
  font-weight: 600;
}

.nav-label {
  white-space: nowrap;
  font-size: 14px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: rgba(255, 255, 255, 0.8);
  font-size: 13px;
  margin-bottom: 8px;
}

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.15);
  border: none;
  color: rgba(255, 255, 255, 0.8);
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 6px;
  width: 100%;
  font-size: 13px;
  transition: all 0.2s;
}

.logout-btn:hover {
  background: rgba(255, 255, 255, 0.25);
  color: white;
}

.main-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background-color: var(--bg-color);
}
</style>
