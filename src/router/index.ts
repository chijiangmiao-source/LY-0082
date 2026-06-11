import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/pages/LoginPage.vue'),
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    name: 'dashboard',
    component: () => import('@/pages/DashboardPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/rooms',
    name: 'rooms',
    component: () => import('@/pages/RoomsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/residents',
    name: 'residents',
    component: () => import('@/pages/ResidentsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/appointments',
    name: 'appointments',
    component: () => import('@/pages/AppointmentsPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/checkin',
    name: 'checkin',
    component: () => import('@/pages/CheckinPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/checkout',
    name: 'checkout',
    component: () => import('@/pages/CheckoutPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/blacklist',
    name: 'blacklist',
    component: () => import('@/pages/BlacklistPage.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/statistics',
    name: 'statistics',
    component: () => import('@/pages/StatisticsPage.vue'),
    meta: { requiresAuth: true },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth !== false && !authStore.isLoggedIn) {
    next('/login')
  } else if (to.path === '/login' && authStore.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
