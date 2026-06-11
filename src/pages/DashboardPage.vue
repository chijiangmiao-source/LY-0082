<template>
  <AppLayout>
    <div class="dashboard">
      <h2 class="page-title">仪表盘</h2>
      <div class="stat-cards">
        <div class="stat-card" style="background: linear-gradient(135deg, #E8A0BF, #D4899F)">
          <div class="stat-icon">
            <Eye :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.today_visits }}</div>
            <div class="stat-label">今日探视数</div>
          </div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #27AE60, #219A52)">
          <div class="stat-icon">
            <Users :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.active_visitors }}</div>
            <div class="stat-label">在场访客数</div>
          </div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #E74C3C, #C0392B)">
          <div class="stat-icon">
            <ShieldAlert :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.interception_count }}</div>
            <div class="stat-label">拦截次数</div>
          </div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #3498DB, #2980B9)">
          <div class="stat-icon">
            <AlertTriangle :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.overcapacity_count }}</div>
            <div class="stat-label">超员预警数</div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { statisticsApi } from '@/api'
import { Eye, Users, ShieldAlert, AlertTriangle } from 'lucide-vue-next'

const stats = ref({
  today_visits: 0,
  active_visitors: 0,
  interception_count: 0,
  overcapacity_count: 0,
})

onMounted(async () => {
  try {
    stats.value = await statisticsApi.dashboard()
  } catch {}
})
</script>

<style scoped>
.dashboard {
  max-width: 1200px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
  margin: 0 0 24px;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
}

.stat-card {
  border-radius: 16px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 56px;
  height: 56px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-info {
  color: white;
}

.stat-number {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
  margin-top: 4px;
}
</style>
