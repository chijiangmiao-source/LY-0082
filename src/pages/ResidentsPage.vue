<template>
  <AppLayout>
    <div class="residents-page">
      <h2 class="page-title">住户档案</h2>
      <div class="toolbar">
        <span class="p-input-icon-left search-box">
          <i class="pi pi-search" />
          <InputText v-model="searchQuery" placeholder="搜索住户姓名/手机号" @input="handleSearch" />
        </span>
        <Button label="新增住户" icon="pi pi-plus" @click="showDialog()" />
      </div>
      <DataTable :value="residents" paginator :rows="10" stripedRows tableStyle="min-width: 800px">
        <Column field="name" header="姓名" />
        <Column field="phone" header="手机号" />
        <Column field="room_number" header="房间号" />
        <Column field="check_in_date" header="入住日期" />
        <Column field="expected_check_out_date" header="预计离店日期" />
        <Column header="操作" :style="{ width: '120px' }">
          <template #body="{ data }">
            <button class="icon-btn" @click="showDialog(data)"><Pencil :size="14" /></button>
            <button class="icon-btn danger" @click="handleDelete(data)"><Trash2 :size="14" /></button>
          </template>
        </Column>
      </DataTable>

      <Dialog v-model:visible="dialogVisible" :header="form.id ? '编辑住户' : '新增住户'" :modal="true" :style="{ width: '500px' }">
        <div class="dialog-form">
          <div class="field">
            <label>姓名</label>
            <InputText v-model="form.name" placeholder="请输入姓名" />
          </div>
          <div class="field">
            <label>手机号</label>
            <InputText v-model="form.phone" placeholder="请输入手机号" />
          </div>
          <div class="field">
            <label>房间</label>
            <Dropdown v-model="form.room_id" :options="roomOptions" optionLabel="room_number" optionValue="id" placeholder="请选择房间" />
          </div>
          <div class="field">
            <label>入住日期</label>
            <Calendar v-model="form.check_in_date" dateFormat="yy-mm-dd" showIcon />
          </div>
          <div class="field">
            <label>预计离店日期</label>
            <Calendar v-model="form.expected_check_out_date" dateFormat="yy-mm-dd" showIcon />
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
import { residentApi, roomApi } from '@/api'
import { Pencil, Trash2 } from 'lucide-vue-next'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'
import Calendar from 'primevue/calendar'

const residents = ref<any[]>([])
const roomOptions = ref<any[]>([])
const dialogVisible = ref(false)
const searchQuery = ref('')

const form = ref<{ id?: number; name: string; phone: string; room_id: number | null; check_in_date: Date | null; expected_check_out_date: Date | null }>({
  name: '', phone: '', room_id: null, check_in_date: null, expected_check_out_date: null,
})

async function loadData() {
  try {
    residents.value = await residentApi.list(searchQuery.value ? { search: searchQuery.value } : undefined)
  } catch {}
}

async function loadRooms() {
  try {
    roomOptions.value = await roomApi.list()
  } catch {}
}

function handleSearch() {
  loadData()
}

function showDialog(resident?: any) {
  if (resident) {
    form.value = {
      id: resident.id,
      name: resident.name,
      phone: resident.phone || '',
      room_id: resident.room_id,
      check_in_date: resident.check_in_date ? new Date(resident.check_in_date) : null,
      expected_check_out_date: resident.expected_check_out_date ? new Date(resident.expected_check_out_date) : null,
    }
  } else {
    form.value = { name: '', phone: '', room_id: null, check_in_date: null, expected_check_out_date: null }
  }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    const data: any = {
      name: form.value.name,
      phone: form.value.phone || undefined,
      room_id: form.value.room_id!,
      check_in_date: form.value.check_in_date ? formatDate(form.value.check_in_date) : '',
      expected_check_out_date: form.value.expected_check_out_date ? formatDate(form.value.expected_check_out_date) : undefined,
    }
    if (form.value.id) {
      await residentApi.update(form.value.id, data)
    } else {
      await residentApi.create(data)
    }
    dialogVisible.value = false
    await loadData()
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

function formatDate(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

async function handleDelete(resident: any) {
  if (!confirm(`确定删除住户「${resident.name}」？`)) return
  try {
    await residentApi.delete(resident.id)
    await loadData()
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}

onMounted(() => {
  loadData()
  loadRooms()
})
</script>

<style scoped>
.residents-page {
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

.search-box {
  position: relative;
}

.search-box :deep(.p-inputtext) {
  padding-left: 32px;
}

.search-box i {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
  z-index: 1;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  display: inline-flex;
  align-items: center;
  color: #666;
}

.icon-btn:hover {
  background: #f0f0f0;
}

.icon-btn.danger:hover {
  color: #E74C3C;
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
