<template>
  <AppLayout>
    <div class="checkout-page">
      <h2 class="page-title">离开登记</h2>
      <DataTable :value="activeVisits" paginator :rows="10" stripedRows tableStyle="min-width: 900px">
        <Column field="visitor_name" header="访客姓名" />
        <Column field="room_number" header="房间号" />
        <Column field="resident_name" header="探视住户" />
        <Column field="check_in_time" header="签到时间" />
        <Column header="操作" :style="{ width: '120px' }">
          <template #body="{ data }">
            <Button label="确认离开" severity="success" size="small" @click="handleCheckout(data)" />
          </template>
        </Column>
      </DataTable>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { visitApi } from '@/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'

const activeVisits = ref<any[]>([])

async function loadData() {
  try {
    activeVisits.value = await visitApi.listActive()
  } catch {}
}

async function handleCheckout(visit: any) {
  if (!confirm(`确认访客「${visit.visitor_name}」已离开？`)) return
  try {
    await visitApi.checkout({ visit_id: visit.id })
    await loadData()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.checkout-page {
  max-width: 1200px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
  margin: 0 0 24px;
}
</style>
