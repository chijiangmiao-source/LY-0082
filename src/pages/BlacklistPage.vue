<template>
  <AppLayout>
    <div class="blacklist-page">
      <h2 class="page-title">黑名单管理</h2>
      <div class="toolbar">
        <div></div>
        <Button v-if="authStore.isAdmin" label="添加黑名单" icon="pi pi-plus" @click="showDialog()" />
      </div>
      <DataTable :value="blacklist" paginator :rows="10" stripedRows tableStyle="min-width: 800px">
        <Column field="visitor_name" header="访客姓名" />
        <Column field="visitor_id_card" header="身份证号" />
        <Column field="reason" header="原因" />
        <Column field="created_at" header="添加时间" />
        <Column v-if="authStore.isAdmin" header="操作" :style="{ width: '80px' }">
          <template #body="{ data }">
            <Button label="移除" severity="danger" size="small" @click="handleRemove(data)" />
          </template>
        </Column>
      </DataTable>

      <Dialog v-model:visible="dialogVisible" header="添加黑名单" :modal="true" :style="{ width: '450px' }">
        <div class="dialog-form">
          <div class="field">
            <label>访客姓名</label>
            <InputText v-model="form.visitor_name" placeholder="请输入访客姓名" />
          </div>
          <div class="field">
            <label>身份证号</label>
            <InputText v-model="form.visitor_id_card" placeholder="请输入身份证号" />
          </div>
          <div class="field">
            <label>原因</label>
            <InputText v-model="form.reason" placeholder="请输入加入黑名单原因" />
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
import { useAuthStore } from '@/stores/auth'
import { blacklistApi } from '@/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'

const authStore = useAuthStore()
const blacklist = ref<any[]>([])
const dialogVisible = ref(false)

const form = ref({
  visitor_name: '',
  visitor_id_card: '',
  reason: '',
})

async function loadData() {
  try {
    blacklist.value = await blacklistApi.list()
  } catch {}
}

function showDialog() {
  form.value = { visitor_name: '', visitor_id_card: '', reason: '' }
  dialogVisible.value = true
}

async function handleSave() {
  try {
    await blacklistApi.create(form.value)
    dialogVisible.value = false
    await loadData()
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

async function handleRemove(item: any) {
  if (!confirm(`确定移除「${item.visitor_name}」的黑名单记录？`)) return
  try {
    await blacklistApi.remove(item.id)
    await loadData()
  } catch (e: any) {
    alert(e.message || '移除失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.blacklist-page {
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

.dialog-form .field .p-inputtext {
  width: 100%;
}
</style>
