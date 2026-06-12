<template>
  <AppLayout>
    <div class="dashboard">
      <h2 class="page-title">探视统计总览</h2>
      <div class="filter-bar">
        <label>时间范围：</label>
        <SelectButton v-model="daysRange" :options="rangeOptions" optionLabel="label" optionValue="value" @change="loadCharts" />
      </div>

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
            <div class="stat-label">今日拦截次数</div>
          </div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #3498DB, #2980B9)">
          <div class="stat-icon">
            <AlertTriangle :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.overcapacity_count }}</div>
            <div class="stat-label">超员预警房间</div>
          </div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #F59E0B, #D97706)">
          <div class="stat-icon">
            <Star :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.whitelist_ratio }}%</div>
            <div class="stat-label">白名单访客占比（{{ stats.whitelist_visit_count }}人）</div>
          </div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #8B5CF6, #7C3AED)">
          <div class="stat-icon">
            <QrCode :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.visit_code_released_count }}</div>
            <div class="stat-label">探视码放行次数</div>
          </div>
        </div>
        <div class="stat-card" style="background: linear-gradient(135deg, #64748B, #475569)">
          <div class="stat-icon">
            <XCircle :size="28" color="white" />
          </div>
          <div class="stat-info">
            <div class="stat-number">{{ stats.visit_code_rejected_count }}</div>
            <div class="stat-label">异常码拦截次数</div>
          </div>
        </div>
      </div>

      <div class="charts-grid">
        <div class="chart-card">
          <h3>房间探视热度</h3>
          <Bar :data="roomHeatData" :options="barOptions" v-if="roomHeatData.labels.length" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>拦截原因分布</h3>
          <Doughnut :data="interceptionData" :options="doughnutOptions" v-if="interceptionData.labels.length" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>
        <div class="chart-card full-width">
          <h3>超员预警分布</h3>
          <Bar :data="overcapacityData" :options="barOptions" v-if="overcapacityData.labels.length" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { statisticsApi } from '@/api'
import { Eye, Users, ShieldAlert, AlertTriangle, Star, QrCode, XCircle } from 'lucide-vue-next'
import { Bar, Doughnut } from 'vue-chartjs'
import SelectButton from 'primevue/selectbutton'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

const daysRange = ref(7)
const rangeOptions = [
  { label: '最近7天', value: 7 },
  { label: '最近30天', value: 30 },
]

const stats = ref({
  today_visits: 0,
  active_visitors: 0,
  interception_count: 0,
  overcapacity_count: 0,
  whitelist_visit_count: 0,
  whitelist_ratio: 0,
  visit_code_released_count: 0,
  visit_code_rejected_count: 0,
})

const roomHeatData = reactive<{ labels: string[]; datasets: any[] }>({ labels: [], datasets: [] })
const interceptionData = reactive<{ labels: string[]; datasets: any[] }>({ labels: [], datasets: [] })
const overcapacityData = reactive<{ labels: string[]; datasets: any[] }>({ labels: [], datasets: [] })

const barOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { display: false },
  },
  scales: {
    y: { beginAtZero: true },
  },
}

const doughnutOptions = {
  responsive: true,
  maintainAspectRatio: true,
  plugins: {
    legend: { position: 'bottom' as const },
  },
}

async function loadDashboard() {
  try {
    stats.value = await statisticsApi.dashboard()
  } catch {}
}

async function loadRoomHeat() {
  try {
    const data = await statisticsApi.roomHeat({ days: daysRange.value })
    roomHeatData.labels = data.map((d: any) => d.room_number)
    roomHeatData.datasets = [{
      label: '探视次数',
      data: data.map((d: any) => d.visit_count),
      backgroundColor: 'rgba(232, 160, 191, 0.7)',
      borderColor: '#E8A0BF',
      borderWidth: 1,
    }]
  } catch {}
}

async function loadInterception() {
  try {
    const data = await statisticsApi.interception({ days: daysRange.value })
    const colors = ['#E74C3C', '#E8A0BF', '#3498DB', '#F59E0B', '#27AE60', '#8B5CF6']
    interceptionData.labels = data.map((d: any) => d.reason)
    interceptionData.datasets = [{
      data: data.map((d: any) => d.count),
      backgroundColor: colors.slice(0, data.length),
    }]
  } catch {}
}

async function loadOvercapacity() {
  try {
    const data = await statisticsApi.overcapacity({ days: daysRange.value })
    overcapacityData.labels = data.map((d: any) => d.room_number)
    overcapacityData.datasets = [{
      label: '超员次数',
      data: data.map((d: any) => d.overcapacity_count),
      backgroundColor: data.map((d: any) =>
        d.overcapacity_count > 5 ? 'rgba(231, 76, 60, 0.7)' : 'rgba(52, 152, 219, 0.7)'
      ),
      borderWidth: 1,
    }]
  } catch {}
}

function loadCharts() {
  loadRoomHeat()
  loadInterception()
  loadOvercapacity()
}

onMounted(() => {
  loadDashboard()
  loadCharts()
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
  margin: 0 0 16px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.filter-bar label {
  font-size: 14px;
  font-weight: 500;
  color: #2D3436;
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 20px;
  margin-bottom: 32px;
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
  font-size: 13px;
  opacity: 0.9;
  margin-top: 4px;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.chart-card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.chart-card.full-width {
  grid-column: 1 / -1;
}

.chart-card h3 {
  margin: 0 0 16px;
  font-size: 16px;
  color: #2D3436;
}

.empty-chart {
  text-align: center;
  padding: 40px;
  color: #999;
}
</style>
