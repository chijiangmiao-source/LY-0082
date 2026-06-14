<template>
  <AppLayout>
    <div class="checkin-page">
      <h2 class="page-title">前台核验</h2>

      <div class="search-tabs">
        <div class="tab" :class="{ active: activeTab === 'code' }" @click="activeTab = 'code'">
          <QrCode :size="18" />
          <span>探视码核验</span>
        </div>
        <div class="tab" :class="{ active: activeTab === 'search' }" @click="activeTab = 'search'">
          <Search :size="18" />
          <span>预约搜索</span>
        </div>
      </div>

      <div v-show="activeTab === 'code'" class="code-verify-section">
        <div class="code-input-box">
          <div class="code-input-title">请输入或扫描探视码</div>
          <div class="code-input-row">
            <InputText
              v-model="codeInput"
              placeholder="请输入8位探视码（如：A1B2C3D4）"
              class="code-input"
              @keyup.enter="handleCodeQuery"
              maxlength="8"
            />
            <Button label="扫码" icon="pi pi-camera" @click="openScanner" class="scan-btn" :disabled="scannerActive" />
            <Button label="查询" icon="pi pi-search" @click="handleCodeQuery" />
          </div>
          <div class="code-input-hint">探视码为8位大写字母数字组合，审核通过后由系统生成</div>
        </div>

        <div v-if="codeResult" class="code-result-card" :class="getCodeCardClass(codeResult)">
          <div class="card-header">
            <div class="apt-no">预约编号：{{ codeResult.appointment_no }}</div>
            <div class="code-badge" :class="{ used: codeResult.visit_code_used }">
              码：{{ codeResult.visit_code }}
            </div>
            <span class="status-badge" :class="codeResult.status">{{ statusLabel(codeResult.status) }}</span>
          </div>
          <div class="card-body">
            <div class="info-grid">
              <div class="info-item">
                <span class="info-label">住户姓名</span>
                <span class="info-value">{{ codeResult.resident_name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">房间号</span>
                <span class="info-value">{{ codeResult.room_number }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">访客姓名</span>
                <span class="info-value">{{ codeResult.visitor_name }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">关系</span>
                <span class="info-value">{{ codeResult.visitor_relation }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">访客手机</span>
                <span class="info-value">{{ codeResult.visitor_phone || '-' }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">白名单访客</span>
                <span class="info-value">
                  <span v-if="codeResult.is_whitelist_visitor" class="whitelist-yes">是</span>
                  <span v-else>否</span>
                </span>
              </div>
              <div class="info-item full">
                <span class="info-label">预约开始</span>
                <span class="info-value">{{ codeResult.scheduled_start }}</span>
              </div>
              <div class="info-item full">
                <span class="info-label">预约结束</span>
                <span class="info-value">{{ codeResult.scheduled_end }}</span>
              </div>
            </div>
            <div v-if="codeResult.warnings && codeResult.warnings.length" class="warnings">
              <div v-for="(w, i) in codeResult.warnings" :key="i" class="warning-item">
                <AlertTriangle :size="16" color="#E74C3C" />
                <span>{{ w }}</span>
              </div>
            </div>
          </div>
          <div class="card-actions" v-if="canCheckinByCode(codeResult)">
            <Button label="快速放行" icon="pi pi-check" severity="success" @click="handleCodeCheckin" />
            <Button label="拒绝" icon="pi pi-times" severity="danger" @click="showCodeRejectDialog" />
          </div>
        </div>

        <div v-else-if="codeSearched && !codeError" class="empty-state">未找到相关预约</div>
        <div v-else-if="codeError" class="empty-state error">{{ codeError }}</div>
      </div>

      <div v-show="activeTab === 'search'" class="search-section">
        <div class="search-bar">
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="searchQuery" placeholder="输入预约编号或访客姓名搜索" style="width: 400px" @keyup.enter="handleSearch" />
          </span>
          <Button label="搜索" icon="pi pi-search" @click="handleSearch" />
        </div>

        <div v-if="searchResults.length" class="results-section">
          <div v-for="apt in searchResults" :key="apt.id" class="appointment-card" :class="getCardClass(apt)">
            <div class="card-header">
              <div class="apt-no">预约编号：{{ apt.appointment_no }}</div>
              <div v-if="apt.visit_code" class="code-badge" :class="{ used: apt.visit_code_used }">
                码：{{ apt.visit_code }}
              </div>
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
            <div class="card-actions" v-if="apt.status === 'pending' || apt.status === 'approved'">
              <Button label="放行" icon="pi pi-check" severity="success" @click="handleCheckin(apt)" />
              <Button label="拒绝" icon="pi pi-times" severity="danger" @click="showRejectDialog(apt)" />
            </div>
          </div>
        </div>
        <div v-else-if="searched" class="empty-state">未找到相关预约</div>
      </div>

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

      <Dialog v-model:visible="scannerDialogVisible" header="扫描探视码" :modal="true" :style="{ width: '500px' }" @hide="stopScanner">
        <div class="scanner-container">
          <div v-if="scannerError" class="scanner-error">
            <Camera :size="28" color="#E74C3C" />
            <span>{{ scannerError }}</span>
          </div>
          <div v-else id="qr-reader" class="qr-reader"></div>
          <div v-if="scannerActive && !scannerError" class="scanner-hint">
            <ScanLine :size="16" />
            <span>将二维码放入扫描框内，保持光线充足</span>
          </div>
        </div>
        <template #footer>
          <div class="scanner-footer">
            <Button label="切换摄像头" icon="pi pi-sync" @click="switchCamera" :disabled="!scannerActive" />
            <Button label="关闭" severity="secondary" @click="stopScanner" />
          </div>
        </template>
      </Dialog>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { appointmentApi, visitApi } from '@/api'
import { AlertTriangle, Search, QrCode, Camera, ScanLine } from 'lucide-vue-next'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import { Html5Qrcode } from 'html5-qrcode'

const activeTab = ref<'code' | 'search'>('code')
const codeInput = ref('')
const codeResult = ref<any>(null)
const codeSearched = ref(false)
const codeError = ref('')

const searchQuery = ref('')
const searchResults = ref<any[]>([])
const searched = ref(false)
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const rejectError = ref('')
const currentApt = ref<any>(null)
const rejectMode = ref<'code' | 'normal'>('normal')

const scannerDialogVisible = ref(false)
const scannerActive = ref(false)
const scannerError = ref('')
let html5QrCode: Html5Qrcode | null = null
let currentCameraId: string | null = null
let camerasList: string[] = []

function statusLabel(status: string) {
  const map: Record<string, string> = { pending: '待审核', approved: '已通过', checked_in: '已签到', checked_out: '已签退', cancelled: '已取消', rejected: '已拒绝' }
  return map[status] || status
}

function getCardClass(apt: any) {
  if (!(apt.status === 'pending' || apt.status === 'approved')) return 'card-disabled'
  if (apt.warnings && apt.warnings.length) return 'card-warning'
  return 'card-ok'
}

function getCodeCardClass(result: any) {
  if (!canCheckinByCode(result)) return 'card-disabled'
  if (result.warnings && result.warnings.length) return 'card-warning'
  return 'card-ok'
}

function canCheckinByCode(result: any) {
  return result.status === 'approved' && !result.visit_code_used
}

async function handleCodeQuery() {
  const code = codeInput.value.trim().toUpperCase()
  if (!code) return
  codeSearched.value = true
  codeError.value = ''
  codeResult.value = null
  try {
    codeResult.value = await visitApi.getByCode(code)
  } catch (e: any) {
    codeError.value = e.message || '查询失败'
  }
}

async function handleCodeCheckin() {
  if (!codeResult.value) return
  try {
    await visitApi.checkinByCode({ code: codeResult.value.visit_code })
    alert('放行成功')
    codeSearched.value = false
    codeInput.value = ''
    codeResult.value = null
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

function showCodeRejectDialog() {
  rejectMode.value = 'code'
  rejectReason.value = ''
  rejectError.value = ''
  rejectDialogVisible.value = true
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
  rejectMode.value = 'normal'
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
    if (rejectMode.value === 'code' && codeResult.value) {
      await visitApi.checkinByCode({ code: codeResult.value.visit_code, reject_reason: rejectReason.value.trim() })
      rejectDialogVisible.value = false
      alert('已拒绝')
      codeSearched.value = false
      codeInput.value = ''
      codeResult.value = null
    } else if (currentApt.value) {
      await visitApi.checkin({ appointment_id: currentApt.value.id, reject_reason: rejectReason.value.trim() })
      rejectDialogVisible.value = false
      alert('已拒绝')
      await handleSearch()
    }
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

async function openScanner() {
  scannerDialogVisible.value = true
  scannerError.value = ''
  try {
    if (!html5QrCode) {
      html5QrCode = new Html5Qrcode('qr-reader')
    }
    const devices = await Html5Qrcode.getCameras()
    if (!devices || devices.length === 0) {
      scannerError.value = '未检测到摄像头设备，请检查权限设置'
      return
    }
    camerasList = devices.map((d: any) => d.id)
    currentCameraId = camerasList[0]
    await startScanner()
  } catch (e: any) {
    console.error('Camera init error:', e)
    scannerError.value = '无法访问摄像头，请检查浏览器权限设置'
  }
}

async function startScanner() {
  if (!html5QrCode || !currentCameraId) return
  scannerActive.value = true
  try {
    await html5QrCode.start(
      { deviceId: { exact: currentCameraId } },
      {
        fps: 10,
        qrbox: { width: 250, height: 250 },
        aspectRatio: 1.0,
      },
      (decodedText: string) => {
        handleScanSuccess(decodedText)
      },
      (errorMessage: string) => {
        console.log('Scan error:', errorMessage)
      }
    )
  } catch (e: any) {
    console.error('Scanner start error:', e)
    scannerError.value = '摄像头启动失败，请重试'
    scannerActive.value = false
  }
}

async function stopScanner() {
  if (html5QrCode && scannerActive.value) {
    try {
      await html5QrCode.stop()
    } catch (e) {
      console.error('Scanner stop error:', e)
    }
  }
  scannerActive.value = false
  scannerDialogVisible.value = false
  scannerError.value = ''
}

async function switchCamera() {
  if (!html5QrCode || camerasList.length < 2) {
    alert('只有一个摄像头可用')
    return
  }
  try {
    await html5QrCode.stop()
    const currentIndex = camerasList.indexOf(currentCameraId!)
    const nextIndex = (currentIndex + 1) % camerasList.length
    currentCameraId = camerasList[nextIndex]
    await startScanner()
  } catch (e: any) {
    console.error('Switch camera error:', e)
    scannerError.value = '切换摄像头失败'
  }
}

function handleScanSuccess(decodedText: string) {
  const code = decodedText.trim().toUpperCase()
  if (/^[A-Z0-9]{8}$/.test(code)) {
    codeInput.value = code
    stopScanner()
    setTimeout(() => {
      handleCodeQuery()
    }, 300)
  } else {
    alert(`扫描成功，但内容不是有效的探视码格式：\n\n${decodedText}`)
  }
}

onUnmounted(() => {
  stopScanner()
})
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

.search-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  border-bottom: 2px solid #E5E7EB;
}

.tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  cursor: pointer;
  color: #6B7280;
  font-weight: 500;
  font-size: 14px;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.tab:hover {
  color: #D4899F;
}

.tab.active {
  color: #D4899F;
  border-bottom-color: #D4899F;
}

.code-verify-section {
  margin-bottom: 24px;
}

.code-input-box {
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 20px;
  text-align: center;
}

.code-input-title {
  font-size: 16px;
  font-weight: 600;
  color: #2D3436;
  margin-bottom: 16px;
}

.code-input-row {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.code-input {
  width: 360px;
  font-family: 'Courier New', monospace;
  font-size: 16px;
  letter-spacing: 2px;
  text-transform: uppercase;
}

.scan-btn {
  background: linear-gradient(135deg, #8B5CF6, #7C3AED) !important;
  border: none !important;
}

.code-input-hint {
  font-size: 12px;
  color: #999;
}

.code-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-family: 'Courier New', monospace;
  font-weight: 700;
  letter-spacing: 1px;
  color: #4F46E5;
  background: #EEF2FF;
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 12px;
}

.code-badge.used {
  color: #6B7280;
  background: #F3F4F6;
  text-decoration: line-through;
}

.whitelist-yes {
  color: #D97706;
  font-weight: 500;
}

.search-section {
  margin-bottom: 24px;
}

.search-bar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-bottom: 24px;
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

.appointment-card,
.code-result-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border-left: 4px solid #27AE60;
}

.appointment-card.card-warning,
.code-result-card.card-warning {
  border-left-color: #E74C3C;
}

.appointment-card.card-disabled,
.code-result-card.card-disabled {
  border-left-color: #999;
  opacity: 0.7;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
  gap: 12px;
  flex-wrap: wrap;
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

.status-badge.approved {
  background: #DBEAFE;
  color: #2563EB;
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

.info-item.full {
  grid-column: span 3;
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

.empty-state.error {
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

.scanner-container {
  padding: 16px 0;
}

.qr-reader {
  width: 100%;
  min-height: 300px;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}

.qr-reader :deep(video) {
  border-radius: 8px;
}

.scanner-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px;
  color: #E74C3C;
  text-align: center;
  background: #FEF2F2;
  border-radius: 8px;
  min-height: 300px;
}

.scanner-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin-top: 16px;
  color: #666;
  font-size: 13px;
}

.scanner-footer {
  display: flex;
  gap: 12px;
  justify-content: space-between;
}
</style>
