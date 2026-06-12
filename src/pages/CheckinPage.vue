<template>
  <AppLayout>
    <div class="checkin-page">
      <h2 class="page-title">前台核验</h2>
      <div class="search-section">
        <div class="search-bar">
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="searchQuery" placeholder="输入预约编号或访客姓名搜索" style="width: 400px" @keyup.enter="handleSearch" />
          </span>
          <Button label="搜索" icon="pi pi-search" @click="handleSearch" />
        </div>
      </div>

      <div v-if="searchResults.length" class="results-section">
        <div v-for="apt in searchResults" :key="apt.id" class="appointment-card" :class="getCardClass(apt)">
          <div class="card-header">
            <div class="apt-no">预约编号：{{ apt.appointment_no }}</div>
            <span class="status-badge" :class="apt.status">{{ statusLabel(apt.status) }}</span>
          </div>
          <div class="card-body">
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">住户姓名</span>
                <span class="info-value">{{ apt.resident_name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">访客姓名</span>
                <span class="info-value">{{ apt.visitor_name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">关系</span>
                <span class="info-value">{{ apt.visitor_relation }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">访客手机</span>
                <span class="info-value">{{ apt.visitor_phone || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">预约开始</span>
                <span class="info-value">{{ apt.scheduled_start }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">预约结束</span>
                <span class="info-value">{{ apt.scheduled_end }}</span>
              </div>
            </div>
            <div v-if="apt.warnings && apt.warnings.length" class="warnings">
              <div v-for="(w, i) in apt.warnings" :key="i" class="warning-item">
                <AlertTriangle :size="16" color="#E74C3C" />
                <span>{{ w }}</span>
              </div>
            </div>
          </div>
          <div class="card-actions" v-if="apt.status === 'pending'">
            <Button label="放行" icon="pi pi-check" severity="success" @click="handleCheckin(apt)" />
            <Button label="拒绝" icon="pi pi-times" severity="danger" @click="showRejectDialog(apt)" />
          </div>
        </div>
      </div>
      <div v-else-if="searched" class="empty-state">未找到相关预约</div>

      <Dialog v-model:visible="rejectDialogVisible" header="拒绝原因" :modal="true" :style="{ width: '400px' }">
        <div class="dialog-form">
          <div class="field">
            <label>请输入拒绝原因 <span class="required">*</span></label>
            <textarea v-model="rejectReason" class="reject-textarea" :class="{ 'textarea-invalid': rejectError }" placeholder="请输入拒绝原因（2-200字）" rows="3" maxlength="200" @input="rejectError = ''" />
            <div class="field-footer">
              <small v-if="rejectError" class="p-error">{{ rejectError }}</small>
              <small class="char-count" :class="{ 'count-warning': rejectReason.length > 180 }">{{ rejectReason.length }}/200</small>
            </div>
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="rejectDialogVisible = false" />
          <Button label="确认拒绝" severity="danger" @click="handleReject" :disabled="rejectReason.trim().length < 2 || rejectReason.trim().length > 200" />
        </template>
      </Dialog>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { appointmentApi, visitApi } from '@/api'
import { AlertTriangle } from 'lucide-vue-next'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'

const searchQuery = ref('')
const searchResults = ref<any[]>([])
const searched = ref(false)
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const rejectError = ref('')
const currentApt = ref<any>(null)

function statusLabel(status: string) {
  const map: Record<string, string> = { pending: '待处理', checked_in: '已签到', checked_out: '已签退', cancelled: '已取消', rejected: '已拒绝' }
  return map[status] || status
}

function getCardClass(apt: any) {
  if (apt.status !== 'pending') return 'card-disabled'
  if (apt.warnings && apt.warnings.length) return 'card-warning'
  return 'card-ok'
}

async function handleSearch() {
  if (!searchQuery.value.trim()) return
  searched.value = true
  try {
    const params: any = {}
    const q = searchQuery.value.trim()
    if (q.startsWith('VT') || q.startsWith('vt')) {
      params.appointment_no = q
    } else {
      params.visitor_name = q
    }
    searchResults.value = await appointmentApi.search(params)
  } catch {
    searchResults.value = []
  }
}

function showRejectDialog(apt: any) {
  currentApt.value = apt
  rejectReason.value = ''
  rejectError.value = ''
  rejectDialogVisible.value = true
}

async function handleCheckin(apt: any) {
  try {
    await visitApi.checkin({ appointment_id: apt.id })
    alert('放行成功')
    await handleSearch()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

function validateReject(): boolean {
  const reason = rejectReason.value.trim()
  if (reason.length < 2) {
    rejectError.value = '拒绝原因至少2个字符'
    return false
  }
  if (reason.length > 200) {
    rejectError.value = '拒绝原因不能超过200字'
    return false
  }
  rejectError.value = ''
  return true
}

async function handleReject() {
  if (!validateReject()) return
  try {
    await visitApi.checkin({ appointment_id: currentApt.value.id, reject_reason: rejectReason.value.trim() })
    rejectDialogVisible.value = false
    alert('已拒绝')
    await handleSearch()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}
</script>

<style scoped>
.checkin-page {
  max-width: 900px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
  margin: 0 0 24px;
}

.search-section {
  margin-bottom: 24px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-bar :deep(.p-input-icon-left) {
  position: relative;
}

.search-bar :deep(.p-input-icon-left i) {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
}

.search-bar :deep(.p-input-icon-left .p-inputtext) {
  padding-left: 32px;
}

.results-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.appointment-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #27AE60;
}

.appointment-card.card-warning {
  border-left-color: #E74C3C;
}

.appointment-card.card-disabled {
  border-left-color: #999;
  opacity: 0.7;
}

.appointment-card.card-ok {
  border-left-color: #27AE60;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.apt-no {
  font-weight: 600;
  color: #2D3436;
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

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.info-label {
  font-size: 12px;
  color: #999;
}

.info-value {
  font-size: 14px;
  color: #2D3436;
}

.warnings {
  background: #FEF2F2;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 12px;
}

.warning-item {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #E74C3C;
  font-size: 13px;
  margin-bottom: 4px;
}

.warning-item:last-child {
  margin-bottom: 0;
}

.card-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.dialog-form .field {
  margin-bottom: 16px;
}

.dialog-form .field label {
  display: block;
  margin-bottom: 6px;
  font-size: 14px;
  font-weight: 500;
}

.dialog-form .field .p-inputtext {
  width: 100%;
}

.required {
  color: #E74C3C;
}

.reject-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 80px;
  box-sizing: border-box;
}

.reject-textarea:focus {
  outline: none;
  border-color: #E8A0BF;
  box-shadow: 0 0 0 2px rgba(232, 160, 191, 0.2);
}

.reject-textarea.textarea-invalid {
  border-color: #E74C3C;
}

.field-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.char-count {
  color: #999;
  font-size: 12px;
}

.char-count.count-warning {
  color: #E74C3C;
  font-weight: 500;
}
</style>
