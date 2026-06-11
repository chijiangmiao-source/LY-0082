<template>
  <AppLayout>
    <div class="appointments-page">
      <h2 class="page-title">探视预约</h2>
      <div class="toolbar">
        <div class="filter-group">
          <Dropdown v-model="statusFilter" :options="statusOptions" optionLabel="label" optionValue="value" placeholder="状态筛选" showClear @change="loadData" />
        </div>
        <Button label="新增预约" icon="pi pi-plus" @click="showDialog()" />
      </div>
      <DataTable :value="appointments" paginator :rows="10" stripedRows tableStyle="min-width: 1000px">
        <Column field="appointment_no" header="预约编号" />
        <Column field="resident_name" header="住户姓名" />
        <Column field="visitor_name" header="访客姓名" />
        <Column field="visitor_relation" header="关系" />
        <Column field="scheduled_start" header="预约开始" />
        <Column field="scheduled_end" header="预约结束" />
        <Column field="status" header="状态">
          <template #body="{ data }">
            <span class="status-badge" :class="data.status">{{ statusLabel(data.status) }}</span>
          </template>
        </Column>
        <Column header="操作" :style="{ width: '100px' }">
          <template #body="{ data }">
            <Button v-if="data.status === 'pending'" label="取消" severity="danger" size="small" @click="handleCancel(data)" />
          </template>
        </Column>
      </DataTable>

      <Dialog v-model:visible="dialogVisible" header="新增预约" :modal="true" :style="{ width: '550px' }">
        <div class="dialog-form">
          <div class="field">
            <label>住户</label>
            <Dropdown v-model="form.resident_id" :options="residentOptions" optionLabel="name" optionValue="id" placeholder="请选择住户" filter />
          </div>
          <div class="field">
            <label>访客姓名</label>
            <InputText v-model="form.visitor_name" placeholder="请输入访客姓名" />
          </div>
          <div class="field">
            <label>访客手机号</label>
            <InputText v-model="form.visitor_phone" placeholder="请输入访客手机号" />
          </div>
          <div class="field">
            <label>访客身份证</label>
            <InputText v-model="form.visitor_id_card" placeholder="请输入访客身份证号" />
          </div>
          <div class="field">
            <label>关系</label>
            <Dropdown v-model="form.visitor_relation" :options="relationshipOptions" optionLabel="label" optionValue="value" placeholder="请选择关系" editable />
          </div>
          <div class="field">
            <label>预约开始时间</label>
            <Calendar v-model="form.scheduled_start" showTime hourFormat="24" dateFormat="yy-mm-dd" showIcon />
          </div>
          <div class="field">
            <label>预约结束时间</label>
            <Calendar v-model="form.scheduled_end" showTime hourFormat="24" dateFormat="yy-mm-dd" showIcon />
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="dialogVisible = false" />
          <Button label="保存" @click="handleSave" />
        </template>
      </Dialog>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { appointmentApi, residentApi } from '@/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'

const appointments = ref<any[]>([])
const residentOptions = ref<any[]>([])
const dialogVisible = ref(false)
const statusFilter = ref<string | null>(null)

const form = ref<{
  resident_id: number | null
  visitor_name: string
  visitor_phone: string
  visitor_id_card: string
  visitor_relation: string
  scheduled_start: Date | null
  scheduled_end: Date | null
}>({
  resident_id: null, visitor_name: '', visitor_phone: '', visitor_id_card: '', visitor_relation: '', scheduled_start: null, scheduled_end: null,
})

const statusOptions = [
  { label: '待处理', value: 'pending' },
  { label: '已签到', value: 'checked_in' },
  { label: '已签退', value: 'checked_out' },
  { label: '已取消', value: 'cancelled' },
  { label: '已拒绝', value: 'rejected' },
]

const relationshipOptions = [
  { label: '配偶', value: '配偶' },
  { label: '母亲', value: '母亲' },
  { label: '父亲', value: '父亲' },
  { label: '婆婆', value: '婆婆' },
  { label: '公公', value: '公公' },
  { label: '姐妹', value: '姐妹' },
  { label: '兄弟', value: '兄弟' },
  { label: '朋友', value: '朋友' },
  { label: '其他', value: '其他' },
]

function statusLabel(status: string) {
  const map: Record<string, string> = { pending: '待处理', checked_in: '已签到', checked_out: '已签退', cancelled: '已取消', rejected: '已拒绝' }
  return map[status] || status
}

async function loadData() {
  try {
    const params: any = {}
    if (statusFilter.value) params.status = statusFilter.value
    appointments.value = await appointmentApi.list(params)
  } catch {}
}

async function loadResidents() {
  try {
    residentOptions.value = await residentApi.list()
  } catch {}
}

function showDialog() {
  form.value = { resident_id: null, visitor_name: '', visitor_phone: '', visitor_id_card: '', visitor_relation: '', scheduled_start: null, scheduled_end: null }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    const data = {
      resident_id: form.value.resident_id!,
      visitor_name: form.value.visitor_name,
      visitor_phone: form.value.visitor_phone || undefined,
      visitor_id_card: form.value.visitor_id_card || undefined,
      visitor_relation: form.value.visitor_relation,
      scheduled_start: form.value.scheduled_start ? formatDate(form.value.scheduled_start) : '',
      scheduled_end: form.value.scheduled_end ? formatDate(form.value.scheduled_end) : '',
    }
    await appointmentApi.create(data)
    dialogVisible.value = false
    await loadData()
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

async function handleCancel(apt: any) {
  if (!confirm(`确定取消预约「${apt.appointment_no}」？`)) return
  try {
    await appointmentApi.delete(apt.id)
    await loadData()
  } catch (e: any) {
    alert(e.message || '取消失败')
  }
}

function formatDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:00`
}

onMounted(() => {
  loadData()
  loadResidents()
})
</script>

<style scoped>
.appointments-page {
  max-width: 1200px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
  margin: 0 0 24px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.filter-group {
  display: flex;
  gap: 12px;
}

.status-badge {
  display: inline-block;
  padding: 2px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.pending {
  background: #FEF3C7;
  color: #D97706;
}

.status-badge.checked_in {
  background: #D1FAE5;
  color: #059669;
}

.status-badge.checked_out {
  background: #E0E7FF;
  color: #4F46E5;
}

.status-badge.cancelled {
  background: #F3F4F6;
  color: #6B7280;
}

.status-badge.rejected {
  background: #FEE2E2;
  color: #DC2626;
}

.dialog-form .field {
  margin-bottom: 16px;
}

.dialog-form .field label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
  color: #2D3436;
}

.dialog-form .field .p-inputtext,
.dialog-form .field .p-dropdown,
.dialog-form .field .p-calendar {
  width: 100%;
}
</style>
