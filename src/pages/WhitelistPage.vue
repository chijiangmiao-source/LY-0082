<template>
  <AppLayout>
    <div class="whitelist-page">
      <h2 class="page-title">访客白名单</h2>
      <div class="toolbar">
        <div class="filter-group">
          <Dropdown v-model="residentFilter" :options="residentOptions" optionLabel="name" optionValue="id" placeholder="按住户筛选" showClear filter @change="loadData" />
        </div>
        <Button label="添加白名单" icon="pi pi-plus" @click="showDialog()" />
      </div>
      <DataTable :value="whitelist" paginator :rows="10" stripedRows tableStyle="min-width: 1000px">
        <Column field="resident_name" header="住户姓名" />
        <Column field="room_number" header="房间号" />
        <Column field="visitor_name" header="访客姓名" />
        <Column field="visitor_relation" header="与住户关系" />
        <Column field="visitor_phone" header="访客手机">
          <template #body="{ data }">
            <span>{{ data.visitor_phone || '-' }}</span>
          </template>
        </Column>
        <Column field="visitor_id_card" header="身份证号">
          <template #body="{ data }">
            <span>{{ data.visitor_id_card || '-' }}</span>
          </template>
        </Column>
        <Column field="created_at" header="添加时间" />
        <Column header="操作" :style="{ width: '140px' }">
          <template #body="{ data }">
            <button class="icon-btn" @click="showDialog(data)"><Pencil :size="14" /></button>
            <button class="icon-btn danger" @click="handleRemove(data)"><Trash2 :size="14" /></button>
          </template>
        </Column>
      </DataTable>

      <Dialog v-model:visible="dialogVisible" :header="form.id ? '编辑白名单' : '添加白名单'" :modal="true" :style="{ width: '500px' }">
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
            <label>与住户关系</label>
            <Dropdown v-model="form.visitor_relation" :options="relationshipOptions" optionLabel="label" optionValue="value" placeholder="请选择关系" editable />
          </div>
          <div class="field">
            <label>访客手机号</label>
            <InputText v-model="form.visitor_phone" placeholder="请输入访客手机号" :class="{ 'p-invalid': errors.visitor_phone }" />
            <small v-if="errors.visitor_phone" class="p-error">{{ errors.visitor_phone }}</small>
          </div>
          <div class="field">
            <label>访客身份证号</label>
            <InputText v-model="form.visitor_id_card" placeholder="请输入访客身份证号" :class="{ 'p-invalid': errors.visitor_id_card }" />
            <small v-if="errors.visitor_id_card" class="p-error">{{ errors.visitor_id_card }}</small>
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
import { whitelistApi, residentApi } from '@/api'
import { Pencil, Trash2 } from 'lucide-vue-next'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'

const whitelist = ref<any[]>([])
const residentOptions = ref<any[]>([])
const dialogVisible = ref(false)
const residentFilter = ref<number | null>(null)

const form = ref<{
  id?: number
  resident_id: number | null
  visitor_name: string
  visitor_phone: string
  visitor_id_card: string
  visitor_relation: string
}>({
  resident_id: null, visitor_name: '', visitor_phone: '', visitor_id_card: '', visitor_relation: '',
})

const errors = reactive<Record<string, string>>({})

const relationshipOptions = [
  { label: '配偶', value: '配偶' },
  { label: '母亲', value: '母亲' },
  { label: '父亲', value: '父亲' },
  { label: '婆婆', value: '婆婆' },
  { label: '公公', value: '公公' },
  { label: '姐妹', value: '姐妹' },
  { label: '兄弟', value: '兄弟' },
  { label: '子女', value: '子女' },
  { label: '朋友', value: '朋友' },
  { label: '其他', value: '其他' },
]

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
  return Object.keys(errors).length === 0
}

async function loadData() {
  try {
    const params: any = {}
    if (residentFilter.value) params.resident_id = residentFilter.value
    whitelist.value = await whitelistApi.list(params)
  } catch {}
}

async function loadResidents() {
  try {
    residentOptions.value = await residentApi.list()
  } catch {}
}

function showDialog(item?: any) {
  if (item) {
    form.value = {
      id: item.id,
      resident_id: item.resident_id,
      visitor_name: item.visitor_name || '',
      visitor_phone: item.visitor_phone || '',
      visitor_id_card: item.visitor_id_card || '',
      visitor_relation: item.visitor_relation || '',
    }
  } else {
    form.value = { resident_id: null, visitor_name: '', visitor_phone: '', visitor_id_card: '', visitor_relation: '' }
  }
  clearErrors()
  dialogVisible.value = true
}

async function handleSave() {
  if (!validate()) return
  try {
    const data: any = {
      resident_id: form.value.resident_id!,
      visitor_name: form.value.visitor_name,
      visitor_phone: form.value.visitor_phone || undefined,
      visitor_id_card: form.value.visitor_id_card || undefined,
      visitor_relation: form.value.visitor_relation || undefined,
    }
    if (form.value.id) {
      await whitelistApi.update(form.value.id, data)
    } else {
      await whitelistApi.create(data)
    }
    dialogVisible.value = false
    await loadData()
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

async function handleRemove(item: any) {
  if (!confirm(`确定从白名单移除「${item.visitor_name}」？`)) return
  try {
    await whitelistApi.delete(item.id)
    await loadData()
  } catch (e: any) {
    alert(e.message || '移除失败')
  }
}

onMounted(() => {
  loadData()
  loadResidents()
})
</script>

<style scoped>
.whitelist-page {
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
.dialog-form .field .p-dropdown {
  width: 100%;
}
</style>
