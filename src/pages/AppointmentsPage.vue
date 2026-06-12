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
      <DataTable :value="appointments" paginator :rows="10" stripedRows tableStyle="min-width: 1200px">
        <Column field="appointment_no" header="预约编号" />
        <Column field="resident_name" header="住户姓名" />
        <Column field="visitor_name" header="访客姓名" />
        <Column field="visitor_relation" header="关系" />
        <Column field="scheduled_start" header="预约开始" />
        <Column field="scheduled_end" header="预约结束" />
        <Column field="status" header="预约状态">
          <template #body="{ data }">
            <span class="status-badge" :class="data.status">{{ statusLabel(data.status) }}</span>
          </template>
        </Column>
        <Column field="release_status" header="放行状态">
          <template #body="{ data }">
            <span v-if="data.release_status" class="status-badge" :class="data.release_status">{{ releaseLabel(data.release_status) }}</span>
            <span v-else style="color: #999">-</span>
          </template>
        </Column>
        <Column field="reject_reason" header="拒绝原因">
          <template #body="{ data }">
            <span v-if="data.reject_reason" class="reject-reason" :title="data.reject_reason">{{ data.reject_reason }}</span>
            <span v-else style="color: #999">-</span>
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
            <label>住户 <span class="required">*</span></label>
            <Dropdown v-model="form.resident_id" :options="residentOptions" optionLabel="name" optionValue="id" placeholder="请选择住户" filter :class="{ 'p-invalid': errors.resident_id }" />
            <small v-if="errors.resident_id" class="p-error">{{ errors.resident_id }}</small>
          </div>
          <div class="field">
            <label>访客姓名 <span class="required">*</span></label>
            <InputText v-model="form.visitor_name" placeholder="请输入访客姓名" :class="{ 'p-invalid': errors.visitor_name }" />
            <small v-if="errors.visitor_name" class="p-error">{{ errors.visitor_name }}</small>
          </div>
          <div class="field">
            <label>访客手机号</label>
            <InputText v-model="form.visitor_phone" placeholder="请输入访客手机号" :class="{ 'p-invalid': errors.visitor_phone }" />
            <small v-if="errors.visitor_phone" class="p-error">{{ errors.visitor_phone }}</small>
          </div>
          <div class="field">
            <label>访客身份证</label>
            <InputText v-model="form.visitor_id_card" placeholder="请输入访客身份证号" :class="{ 'p-invalid': errors.visitor_id_card }" />
            <small v-if="errors.visitor_id_card" class="p-error">{{ errors.visitor_id_card }}</small>
          </div>
          <div class="field">
            <label>关系 <span class="required">*</span></label>
            <Dropdown v-model="form.visitor_relation" :options="relationshipOptions" optionLabel="label" optionValue="value" placeholder="请选择关系" editable :class="{ 'p-invalid': errors.visitor_relation }" />
            <small v-if="errors.visitor_relation" class="p-error">{{ errors.visitor_relation }}</small>
          </div>
          <div class="field">
            <label>预约开始时间 <span class="required">*</span></label>
            <Calendar v-model="form.scheduled_start" showTime hourFormat="24" dateFormat="yy-mm-dd" showIcon :class="{ 'p-invalid': errors.scheduled_start }" />
            <small v-if="errors.scheduled_start" class="p-error">{{ errors.scheduled_start }}</small>
          </div>
          <div class="field">
            <label>预约结束时间 <span class="required">*</span></label>
            <Calendar v-model="form.scheduled_end" showTime hourFormat="24" dateFormat="yy-mm-dd" showIcon :class="{ 'p-invalid': errors.scheduled_end }" />
            <small v-if="errors.scheduled_end" class="p-error">{{ errors.scheduled_end }}</small>
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
import { ref, reactive, onMounted } from 'vue'
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

const errors = reactive<Record<string, string>>({})

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

function releaseLabel(status: string) {
  const map: Record<string, string> = { released: '已放行', rejected: '已拒绝' }
  return map[status] || status
}

function clearErrors() {
  for (const k of Object.keys(errors)) delete errors[k]
}

function validate(): boolean {
  clearErrors()
  const f = form.value
  if (!f.resident_id) errors.resident_id = '请选择住户'
  if (!f.visitor_name.trim()) errors.visitor_name = '请输入访客姓名'
  if (f.visitor_name.trim().length < 2) errors.visitor_name = '访客姓名至少2个字符'
  if (f.visitor_phone && !/^1[3-9]\d{9}$/.test(f.visitor_phone.trim())) errors.visitor_phone = '手机号格式不正确'
  if (f.visitor_id_card && !/(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/.test(f.visitor_id_card.trim())) errors.visitor_id_card = '身份证号格式不正确'
  if (!f.visitor_relation) errors.visitor_relation = '请选择与住户的关系'
  if (!f.scheduled_start) errors.scheduled_start = '请选择预约开始时间'
  if (!f.scheduled_end) errors.scheduled_end = '请选择预约结束时间'
  if (f.scheduled_start && f.scheduled_end && f.scheduled_end <= f.scheduled_start) {
    errors.scheduled_end = '结束时间必须晚于开始时间'
  }
  if (f.scheduled_start && f.scheduled_end) {
    const duration = (f.scheduled_end.getTime() - f.scheduled_start.getTime()) / (1000 * 60)
    if (duration < 5) errors.scheduled_end = '预约时长至少5分钟'
    if (duration > 480) errors.scheduled_end = '单次预约不超过8小时'
  }
  return Object.keys(errors).length === 0
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
  clearErrors()
  dialogVisible.value = true
}

async function handleSave() {
  if (!validate()) return
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

.required {
  color: #E74C3C;
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

.status-badge.released {
  background: #D1FAE5;
  color: #059669;
}

.reject-reason {
  font-size: 12px;
  color: #6B7280;
  max-width: 180px;
  display: inline-block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
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
