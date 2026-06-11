<template>
  <AppLayout>
    <div class="statistics-page">
      <h2 class="page-title">探视统计</h2>
      <div class="filter-bar">
        <label>时间范围：</label>
        <SelectButton v-model="daysRange" :options="rangeOptions" optionLabel="label" optionValue="value" @change="loadAllData" />
      </div>

      <div class="charts-grid">
        <div class="chart-card">
          <h3>房间探视热度</h3>
          <Bar :data="roomHeatData" :options="barOptions" v-if="roomHeatData.labels.length" />
          <div v-else class="empty-chart">暂无数据</div>
        </div>
        <div class="chart-card">
          <h3>拦截次数统计</h3>
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
import { Bar, Doughnut } from 'vue-chartjs'
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

function loadAllData() {
  loadRoomHeat()
  loadInterception()
  loadOvercapacity()
}

onMounted(loadAllData)
</script>

<style scoped>
.statistics-page {
  max-width: 1200px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
  margin: 0 0 24px;
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
