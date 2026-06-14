<template>
  <AppLayout>
    <div class="bills-page">
      <h2 class="page-title">访客账单管理</h2>

      <div class="summary-cards">
        <div class="summary-card" style="background: linear-gradient(135deg, #10B981, #059669)">
          <div class="s-icon"><FileCheck :size="24" color="white" /></div>
          <div class="s-info">
            <div class="s-number">{{ billStats.settlement_rate }}<span class="s-unit">%</span></div>
            <div class="s-label">账单已结清率</div>
            <div class="s-sub">{{ billStats.paid_bills }}/{{ billStats.total_bills }} 笔</div>
          </div>
        </div>
        <div class="summary-card" style="background: linear-gradient(135deg, #F59E0B, #D97706)">
          <div class="s-icon"><Calculator :size="24" color="white" /></div>
          <div class="s-info">
            <div class="s-number">¥{{ billStats.avg_deduct_amount.toFixed(2) }}</div>
            <div class="s-label">平均扣费金额</div>
            <div class="s-sub">共 {{ billStats.deduct_count }} 笔扣费</div>
          </div>
        </div>
        <div class="summary-card" style="background: linear-gradient(135deg, #8B5CF6, #7C3AED)">
          <div class="s-icon"><TrendingDown :size="24" color="white" /></div>
          <div class="s-info">
            <div class="s-number">¥{{ billStats.total_deduct_amount.toFixed(2) }}</div>
            <div class="s-label">累计扣费总额</div>
          </div>
        </div>
      </div>

      <div v-if="billStats.deduct_reason_distribution.length" class="distribution-card">
        <h3 class="dist-title">高频扣费原因分布（最近30天）</h3>
        <div class="dist-list">
          <div v-for="item in billStats.deduct_reason_distribution" :key="item.reason" class="dist-item">
            <div class="dist-name">{{ item.reason }}</div>
            <div class="dist-bar-wrap">
              <div class="dist-bar" :style="{ width: getDistWidth(item.count) + '%' }"></div>
            </div>
            <div class="dist-counts">
              <span>{{ item.count }} 次</span>
              <span class="amount">¥{{ item.total_amount.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="action-bar">
        <div class="search-row">
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="searchForm.visitor_name" placeholder="搜索访客姓名" @keyup.enter="loadBills" />
          </span>
          <span class="p-input-icon-left">
            <i class="pi pi-search" />
            <InputText v-model="searchForm.bill_no" placeholder="搜索账单编号" @keyup.enter="loadBills" />
          </span>
          <Select v-model="searchForm.payment_status" :options="paymentStatusOptions" optionLabel="label" optionValue="value" placeholder="支付状态" class="filter-select" @change="loadBills" />
          <Select v-model="searchForm.signature_status" :options="signatureStatusOptions" optionLabel="label" optionValue="value" placeholder="签收状态" class="filter-select" @change="loadBills" />
          <Calendar v-model="searchForm.start_date" dateFormat="yy-mm-dd" placeholder="开始日期" class="filter-date" />
          <Calendar v-model="searchForm.end_date" dateFormat="yy-mm-dd" placeholder="结束日期" class="filter-date" />
          <Button label="搜索" icon="pi pi-search" @click="loadBills" />
          <Button label="重置" icon="pi pi-refresh" severity="secondary" @click="resetSearch" />
        </div>
      </div>

      <DataTable :value="bills" paginator :rows="10" stripedRows tableStyle="min-width: 100%" :emptyMessage="'暂无账单记录'">
        <Column field="bill_no" header="账单编号" :style="{ width: '180px' }">
          <template #body="{ data }">
            <span class="bill-no">{{ data.bill_no }}</span>
          </template>
        </Column>
        <Column field="visitor_name" header="访客姓名" :style="{ width: '100px' }">
          <template #body="{ data }">
            <span class="strong">{{ data.visitor_name }}</span>
          </template>
        </Column>
        <Column field="room_number" header="房间号" :style="{ width: '80px' }" />
        <Column field="resident_name" header="探视住户" :style="{ width: '100px' }" />
        <Column field="total_amount" header="应付金额" :style="{ width: '110px' }">
          <template #body="{ data }">
            <span class="amount">¥{{ Number(data.total_amount).toFixed(2) }}</span>
          </template>
        </Column>
        <Column field="actual_paid" header="实付金额" :style="{ width: '110px' }">
          <template #body="{ data }">
            <span :class="{ 'zero': data.actual_paid === 0 }">¥{{ Number(data.actual_paid).toFixed(2) }}</span>
          </template>
        </Column>
        <Column header="支付状态" :style="{ width: '100px' }">
          <template #body="{ data }">
            <span class="payment-status" :class="data.payment_status">{{ paymentStatusLabel(data.payment_status) }}</span>
          </template>
        </Column>
        <Column header="签收状态" :style="{ width: '100px' }">
          <template #body="{ data }">
            <span class="signature-status" :class="data.signature_status">{{ signatureStatusLabel(data.signature_status) }}</span>
          </template>
        </Column>
        <Column field="generated_at" header="生成时间" :style="{ width: '160px' }">
          <template #body="{ data }">{{ formatTime(data.generated_at) }}</template>
        </Column>
        <Column header="操作" :style="{ width: '200px' }">
          <template #body="{ data }">
            <Button label="查看" size="small" severity="info" @click="viewBillDetail(data)" class="mr-2" />
            <template v-if="data.signature_status !== 'signed'">
              <Button label="签收" size="small" severity="primary" @click="openSignDialog(data)" />
            </template>
          </template>
        </Column>
      </DataTable>

      <Dialog v-model:visible="detailDialogVisible" :modal="true" :style="{ width: '720px' }">
        <template #header>
          <div class="dialog-header">
            <FileText :size="20" />
            <span v-if="currentBill">账单详情 · {{ currentBill.bill_no }}</span>
          </div>
        </template>
        <div v-if="currentBill" class="bill-content">
          <div class="bill-header">
            <div class="bill-info">
              <div class="info-row">
                <span class="label">访客姓名</span>
                <span class="value">{{ currentBill.visitor_name }}</span>
              </div>
              <div class="info-row">
                <span class="label">房间号</span>
                <span class="value">{{ currentBill.room_number }}</span>
              </div>
              <div class="info-row">
                <span class="label">探视住户</span>
                <span class="value">{{ currentBill.resident_name }}</span>
              </div>
            </div>
            <div class="bill-info">
              <div class="info-row">
                <span class="label">签到时间</span>
                <span class="value">{{ formatTime(currentBill.check_in_time) }}</span>
              </div>
              <div class="info-row">
                <span class="label">离开时间</span>
                <span class="value">{{ formatTime(currentBill.check_out_time) }}</span>
              </div>
              <div class="info-row">
                <span class="label">生成时间</span>
                <span class="value">{{ formatTime(currentBill.generated_at) }}</span>
              </div>
            </div>
          </div>

          <div class="bill-section">
            <h3 class="section-title">费用明细</h3>
            <div class="charge-table">
              <div class="charge-header">
                <span class="ch-item">项目</span>
                <span class="ch-desc">说明</span>
                <span class="ch-amount">金额</span>
              </div>
              <div v-for="item in currentBill.charge_items" :key="item.id" class="charge-row" :class="{ negative: item.amount < 0 }">
                <span class="ci-item">
                  <span class="ci-tag" :class="item.charge_type">{{ chargeTypeLabel(item.charge_type) }}</span>
                  {{ item.item_name }}
                </span>
                <span class="ci-desc">{{ item.description || '-' }}</span>
                <span class="ci-amount">{{ item.amount >= 0 ? '+' : '' }}¥{{ item.amount.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <div class="bill-summary">
            <div class="summary-row" v-if="currentBill.deposit_amount > 0">
              <span class="sl">押金收取</span>
              <span class="sv">¥{{ currentBill.deposit_amount.toFixed(2) }}</span>
            </div>
            <div class="summary-row" v-if="currentBill.deposit_refund_amount > 0">
              <span class="sl">押金退还</span>
              <span class="sv refund">-¥{{ currentBill.deposit_refund_amount.toFixed(2) }}</span>
            </div>
            <div class="summary-row" v-if="currentBill.item_damage_fee > 0">
              <span class="sl">物品损坏费</span>
              <span class="sv deduct">¥{{ currentBill.item_damage_fee.toFixed(2) }}</span>
            </div>
            <div class="summary-row" v-if="currentBill.item_lost_fee > 0">
              <span class="sl">物品丢失费</span>
              <span class="sv deduct">¥{{ currentBill.item_lost_fee.toFixed(2) }}</span>
            </div>
            <div class="summary-row" v-if="currentBill.overtime_fee > 0">
              <span class="sl">超时占用费</span>
              <span class="sv deduct">¥{{ currentBill.overtime_fee.toFixed(2) }}</span>
            </div>
            <div class="summary-row" v-if="currentBill.other_fee > 0">
              <span class="sl">其他费用</span>
              <span class="sv deduct">¥{{ currentBill.other_fee.toFixed(2) }}</span>
            </div>
            <div class="summary-row total">
              <span class="sl">应付金额</span>
              <span class="sv total-amount">¥{{ currentBill.total_amount.toFixed(2) }}</span>
            </div>
          </div>

          <div class="bill-status">
            <div class="status-item">
              <span class="st-label">支付状态</span>
              <span class="st-value" :class="currentBill.payment_status">{{ paymentStatusLabel(currentBill.payment_status) }}</span>
            </div>
            <div class="status-item">
              <span class="st-label">签收状态</span>
              <span class="st-value" :class="currentBill.signature_status">{{ signatureStatusLabel(currentBill.signature_status) }}</span>
            </div>
          </div>

          <div v-if="currentBill.signature" class="signature-preview">
            <div class="sp-title">
              <CheckCircle2 :size="16" color="#059669" />
              <span>已签名确认</span>
            </div>
            <div class="sp-info">
              <span>签收人：{{ currentBill.signature.signer_name }}</span>
              <span>签收时间：{{ formatTime(currentBill.signature.signed_at) }}</span>
            </div>
            <img :src="currentBill.signature.signature_data" class="sp-image" alt="签名" />
          </div>
        </div>
        <template #footer>
          <Button label="关闭" severity="secondary" @click="detailDialogVisible = false" />
          <template v-if="currentBill && currentBill.payment_status !== 'paid'">
            <Button label="确认支付" icon="pi pi-credit-card" severity="warning" @click="openPayDialog" />
          </template>
          <template v-if="currentBill && currentBill.signature_status !== 'signed'">
            <Button label="电子签收" icon="pi pi-pencil" severity="primary" @click="openSignDialog(currentBill)" />
          </template>
        </template>
      </Dialog>

      <Dialog v-model:visible="payDialogVisible" header="确认支付" :modal="true" :style="{ width: '480px' }">
        <div v-if="currentBill" class="pay-form">
          <div class="pay-info">
            <div class="info-row"><span class="k">账单编号</span><span class="v bill-no">{{ currentBill.bill_no }}</span></div>
            <div class="info-row"><span class="k">访客姓名</span><span class="v">{{ currentBill.visitor_name }}</span></div>
            <div class="info-row"><span class="k">应付金额</span><span class="v amount">¥{{ currentBill.total_amount.toFixed(2) }}</span></div>
          </div>
          <div class="field">
            <label>实际支付金额 (元) <span class="required">*</span></label>
            <InputNumber v-model="payForm.actual_paid" :min="0" :precision="2" prefix="¥" placeholder="0.00" />
            <small class="form-hint">如金额为 0 则表示免收</small>
          </div>
          <div class="field">
            <label>备注</label>
            <textarea v-model="payForm.remarks" class="form-textarea" rows="2" placeholder="可选，填写支付相关说明" />
          </div>
          <div v-if="payForm.actual_paid === 0" class="waive-notice">
            <AlertTriangle :size="16" />
            <span>金额为 0，账单将标记为「免收」</span>
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="payDialogVisible = false" />
          <Button label="确认支付" severity="primary" @click="submitPayment" :disabled="!canSubmitPay" />
        </template>
      </Dialog>

      <Dialog v-model:visible="signDialogVisible" header="电子签名确认" :modal="true" :style="{ width: '640px' }">
        <div class="sign-form">
          <div class="sign-info" v-if="currentBill">
            <div class="info-row"><span class="k">账单编号</span><span class="v bill-no">{{ currentBill.bill_no }}</span></div>
            <div class="info-row"><span class="k">应付金额</span><span class="v amount">¥{{ currentBill.total_amount.toFixed(2) }}</span></div>
          </div>
          <div class="field">
            <label>签收人姓名 <span class="required">*</span></label>
            <InputText v-model="signForm.signer_name" placeholder="请输入签收人姓名" />
          </div>
          <SignaturePad ref="signaturePadRef" @signature="onSignature" @change="onSignatureChange" />
          <div class="sign-terms">
            <Checkbox v-model="signForm.agree_terms" :binary="true" />
            <label class="terms-text">我已仔细阅读并确认以上费用明细无误，同意以此电子签名作为确认凭证</label>
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="signDialogVisible = false" />
          <Button label="确认签名" severity="primary" @click="submitSignature" :disabled="!canSubmitSign" />
        </template>
      </Dialog>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import SignaturePad from '@/components/SignaturePad.vue'
import { billApi, type VisitorBill } from '@/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import Calendar from 'primevue/calendar'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Checkbox from 'primevue/checkbox'
import { FileCheck, Calculator, TrendingDown, FileText, CheckCircle2, AlertTriangle } from 'lucide-vue-next'

const bills = ref<VisitorBill[]>([])
const currentBill = ref<VisitorBill | null>(null)
const signaturePadRef = ref<InstanceType<typeof SignaturePad> | null>(null)

const billStats = reactive({
  total_bills: 0,
  paid_bills: 0,
  settlement_rate: 0,
  deduct_count: 0,
  total_deduct_amount: 0,
  avg_deduct_amount: 0,
  deduct_reason_distribution: [] as Array<{ reason: string; count: number; total_amount: number }>,
})

const searchForm = reactive({
  visitor_name: '',
  bill_no: '',
  payment_status: null as string | null,
  signature_status: null as string | null,
  start_date: null as Date | null,
  end_date: null as Date | null,
})

const paymentStatusOptions = [
  { label: '全部状态', value: null },
  { label: '待支付', value: 'pending' },
  { label: '已支付', value: 'paid' },
  { label: '部分支付', value: 'partial_paid' },
  { label: '已免收', value: 'waived' },
]

const signatureStatusOptions = [
  { label: '全部状态', value: null },
  { label: '未签收', value: 'unsigned' },
  { label: '已签收', value: 'signed' },
]

const detailDialogVisible = ref(false)
const payDialogVisible = ref(false)
const signDialogVisible = ref(false)

const payForm = reactive({
  actual_paid: 0,
  remarks: '',
})

const signForm = reactive({
  signer_name: '',
  signature_data: '',
  has_signature: false,
  agree_terms: false,
})

const canSubmitPay = computed(() => {
  return payForm.actual_paid !== null && payForm.actual_paid >= 0
})

const canSubmitSign = computed(() => {
  return (
    signForm.signer_name.trim().length >= 2 &&
    signForm.has_signature &&
    signForm.agree_terms
  )
})

const maxDistCount = computed(() =>
  Math.max(1, ...billStats.deduct_reason_distribution.map((d: any) => d.count))
)

function getDistWidth(count: number) {
  return (count / maxDistCount.value) * 100
}

function formatTime(timeStr: string | null | undefined): string {
  if (!timeStr) return '-'
  try {
    const dt = new Date(timeStr)
    return dt.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return timeStr
  }
}

function chargeTypeLabel(type: string): string {
  const m: Record<string, string> = {
    deposit_collect: '押金',
    deposit_refund: '退还',
    item_damage: '损坏',
    item_lost: '丢失',
    overtime: '超时',
    other: '其他',
  }
  return m[type] || type
}

function paymentStatusLabel(status: string): string {
  const m: Record<string, string> = {
    pending: '待支付',
    paid: '已支付',
    partial_paid: '部分支付',
    waived: '已免收',
  }
  return m[status] || status
}

function signatureStatusLabel(status: string): string {
  const m: Record<string, string> = {
    unsigned: '未签收',
    signed: '已签收',
  }
  return m[status] || status
}

async function loadBillStats() {
  try {
    const data = await billApi.statistics({ days: 30 })
    Object.assign(billStats, data)
  } catch {}
}

async function loadBills() {
  try {
    const params: any = {}
    if (searchForm.visitor_name.trim()) params.visitor_name = searchForm.visitor_name.trim()
    if (searchForm.bill_no.trim()) params.bill_no = searchForm.bill_no.trim()
    if (searchForm.payment_status) params.payment_status = searchForm.payment_status
    if (searchForm.signature_status) params.signature_status = searchForm.signature_status
    if (searchForm.start_date) params.start_date = formatDate(searchForm.start_date)
    if (searchForm.end_date) params.end_date = formatDate(searchForm.end_date)
    bills.value = await billApi.list(params)
  } catch {
    bills.value = []
  }
}

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function resetSearch() {
  searchForm.visitor_name = ''
  searchForm.bill_no = ''
  searchForm.payment_status = null
  searchForm.signature_status = null
  searchForm.start_date = null
  searchForm.end_date = null
  loadBills()
}

async function viewBillDetail(bill: VisitorBill) {
  try {
    currentBill.value = await billApi.get(bill.id)
    detailDialogVisible.value = true
  } catch (e: any) {
    alert(e.message || '加载账单详情失败')
  }
}

function openPayDialog() {
  if (!currentBill.value) return
  payForm.actual_paid = currentBill.value.total_amount
  payForm.remarks = ''
  payDialogVisible.value = true
}

async function submitPayment() {
  if (!currentBill.value || !canSubmitPay.value) return
  try {
    const bill = await billApi.pay(currentBill.value.id, {
      actual_paid: payForm.actual_paid,
      remarks: payForm.remarks.trim() || undefined,
    })
    currentBill.value = bill
    payDialogVisible.value = false
    alert('支付确认成功')
    loadBills()
    loadBillStats()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

function openSignDialog(bill: VisitorBill) {
  currentBill.value = bill
  signForm.signer_name = bill.visitor_name
  signForm.signature_data = ''
  signForm.has_signature = false
  signForm.agree_terms = false
  setTimeout(() => {
    signaturePadRef.value?.clear()
  }, 100)
  signDialogVisible.value = true
}

function onSignature(data: string) {
  signForm.signature_data = data
}

function onSignatureChange(hasSignature: boolean) {
  signForm.has_signature = hasSignature
}

async function submitSignature() {
  if (!currentBill.value || !canSubmitSign.value) return
  try {
    const bill = await billApi.sign(currentBill.value.id, {
      signer_name: signForm.signer_name.trim(),
      signature_data: signForm.signature_data,
      sign_device: navigator.userAgent.substring(0, 50),
    })
    currentBill.value = bill
    signDialogVisible.value = false
    detailDialogVisible.value = false
    alert('签名确认成功')
    loadBills()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

onMounted(() => {
  loadBillStats()
  loadBills()
})
</script>

<style scoped>
.bills-page {
  max-width: 1400px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
  margin: 0 0 24px;
}

.summary-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.summary-card {
  border-radius: 14px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  color: white;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.1);
}

.s-icon {
  width: 52px;
  height: 52px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.s-number {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.1;
}

.s-unit {
  font-size: 14px;
  font-weight: 500;
  margin-left: 4px;
  opacity: 0.9;
}

.s-label {
  font-size: 13px;
  opacity: 0.9;
  margin-top: 2px;
}

.s-sub {
  font-size: 12px;
  opacity: 0.85;
  margin-top: 2px;
}

.distribution-card {
  background: white;
  border-radius: 12px;
  padding: 20px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  margin-bottom: 20px;
}

.dist-title {
  font-size: 15px;
  font-weight: 600;
  color: #2D3436;
  margin: 0 0 14px;
}

.dist-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 14px 24px;
}

.dist-item {
  display: grid;
  grid-template-columns: 120px 1fr auto;
  gap: 10px;
  align-items: center;
}

.dist-name {
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.dist-bar-wrap {
  height: 8px;
  background: #F3F4F6;
  border-radius: 4px;
  overflow: hidden;
}

.dist-bar {
  height: 100%;
  background: linear-gradient(90deg, #E8A0BF, #D4899F);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.dist-counts {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: #6B7280;
}

.dist-counts .amount {
  color: #D97706;
  font-weight: 600;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 18px;
  flex-wrap: wrap;
}

.search-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.search-row :deep(.p-input-icon-left) {
  position: relative;
}
.search-row :deep(.p-input-icon-left i) {
  position: absolute;
  left: 10px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1;
  color: #9CA3AF;
}
.search-row :deep(.p-input-icon-left .p-inputtext) {
  padding-left: 32px;
  width: 180px;
}

.filter-select {
  width: 140px;
}

.filter-date {
  width: 130px;
}

.strong {
  font-weight: 600;
  color: #2D3436;
}

.bill-no {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #4F46E5;
  font-size: 12.5px;
}

.amount {
  font-weight: 700;
  color: #D97706;
}

.zero {
  color: #9CA3AF;
}

.payment-status {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.payment-status.pending { background: #FEF3C7; color: #D97706; }
.payment-status.paid { background: #D1FAE5; color: #059669; }
.payment-status.partial_paid { background: #DBEAFE; color: #2563EB; }
.payment-status.waived { background: #E5E7EB; color: #4B5563; }

.signature-status {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.signature-status.unsigned { background: #FEE2E2; color: #DC2626; }
.signature-status.signed { background: #D1FAE5; color: #059669; }

.mr-2 {
  margin-right: 8px;
}

.dialog-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #2D3436;
}

.bill-content {
  padding: 4px;
}

.bill-header {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  background: #F9FAFB;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.bill-info .info-row {
  display: flex;
  justify-content: space-between;
  padding: 4px 0;
  font-size: 13px;
}

.bill-info .label {
  color: #6B7280;
}

.bill-info .value {
  font-weight: 500;
  color: #2D3436;
}

.bill-section {
  margin-bottom: 20px;
}

.section-title {
  font-size: 15px;
  font-weight: 600;
  color: #2D3436;
  margin: 0 0 12px;
  padding-left: 10px;
  border-left: 3px solid #E8A0BF;
}

.charge-table {
  border: 1px solid #E5E7EB;
  border-radius: 8px;
  overflow: hidden;
}

.charge-header {
  display: grid;
  grid-template-columns: 140px 1fr 100px;
  background: #F3F4F6;
  padding: 10px 14px;
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
}

.charge-row {
  display: grid;
  grid-template-columns: 140px 1fr 100px;
  padding: 10px 14px;
  border-top: 1px solid #E5E7EB;
  font-size: 13px;
  align-items: center;
}

.charge-row.negative {
  color: #059669;
}

.ci-item {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.ci-tag {
  display: inline-block;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.ci-tag.deposit_collect { background: #FEF3C7; color: #D97706; }
.ci-tag.deposit_refund { background: #D1FAE5; color: #059669; }
.ci-tag.item_damage { background: #FEE2E2; color: #DC2626; }
.ci-tag.item_lost { background: #1F2937; color: #F9FAFB; }
.ci-tag.overtime { background: #FEF3C7; color: #B45309; }
.ci-tag.other { background: #F3F4F6; color: #4B5563; }

.ci-desc {
  color: #6B7280;
  font-size: 12px;
}

.ci-amount {
  font-weight: 600;
  text-align: right;
}

.bill-summary {
  background: #FDF2F8;
  border-radius: 10px;
  padding: 16px 20px;
  margin-bottom: 20px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 13px;
}

.summary-row .sl {
  color: #6B7280;
}

.summary-row .sv {
  font-weight: 600;
}

.summary-row .sv.refund {
  color: #059669;
}

.summary-row .sv.deduct {
  color: #DC2626;
}

.summary-row.total {
  border-top: 1px dashed #E8A0BF;
  margin-top: 8px;
  padding-top: 12px;
  font-size: 16px;
}

.summary-row.total .sl {
  color: #2D3436;
  font-weight: 600;
}

.summary-row.total .total-amount {
  color: #D4899F;
  font-weight: 700;
  font-size: 20px;
}

.bill-status {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.status-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #F9FAFB;
  border-radius: 8px;
}

.st-label {
  color: #6B7280;
  font-size: 13px;
}

.st-value {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.signature-preview {
  background: #ECFDF5;
  border: 1px solid #A7F3D0;
  border-radius: 10px;
  padding: 16px;
}

.sp-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #065F46;
  margin-bottom: 8px;
}

.sp-info {
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #065F46;
  margin-bottom: 12px;
}

.sp-image {
  max-width: 200px;
  max-height: 80px;
  background: white;
  border-radius: 6px;
  border: 1px solid #D1FAE5;
}

.pay-form,
.sign-form {
  padding: 4px;
}

.pay-info {
  background: #F9FAFB;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 16px;
}

.pay-info .info-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;
}

.pay-info .k {
  color: #6B7280;
}

.pay-info .v {
  font-weight: 500;
  color: #2D3436;
}

.field {
  margin-bottom: 14px;
}

.field label {
  display: block;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.field :deep(.p-inputtext),
.field :deep(.p-inputnumber) {
  width: 100%;
}

.required {
  color: #E74C3C;
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  min-height: 60px;
  box-sizing: border-box;
}

.form-textarea:focus {
  outline: none;
  border-color: #E8A0BF;
  box-shadow: 0 0 0 2px rgba(232, 160, 191, 0.2);
}

.form-hint {
  display: block;
  margin-top: 4px;
  font-size: 11.5px;
  color: #6B7280;
}

.waive-notice {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 14px;
  background: #FEF3C7;
  border-radius: 8px;
  color: #92400E;
  font-size: 13px;
}

.sign-info {
  background: #F9FAFB;
  border-radius: 10px;
  padding: 14px 18px;
  margin-bottom: 16px;
}

.sign-info .info-row {
  display: flex;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;
}

.sign-info .k {
  color: #6B7280;
}

.sign-info .v {
  font-weight: 500;
  color: #2D3436;
}

.sign-terms {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-top: 16px;
  padding: 12px;
  background: #F9FAFB;
  border-radius: 8px;
}

.terms-text {
  font-size: 12px;
  color: #4B5563;
  line-height: 1.5;
  margin: 0;
}
</style>
