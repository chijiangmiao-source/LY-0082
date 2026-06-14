<template>
  <div class="signature-page">
    <div v-if="loading" class="loading-box">
      <i class="pi pi-spin pi-spinner" style="font-size: 48px; color: #E8A0BF"></i>
      <p>正在加载账单...</p>
    </div>

    <div v-else-if="bill" class="bill-container">
      <div class="bill-header">
        <div class="logo-area">
          <FileText :size="32" color="#D4899F" />
          <h1>访客离场账单</h1>
        </div>
        <div class="bill-no">账单编号：{{ bill.bill_no }}</div>
      </div>

      <div class="bill-info-card">
        <div class="info-grid">
          <div class="info-item">
            <span class="label">访客姓名</span>
            <span class="value">{{ bill.visitor_name }}</span>
          </div>
          <div class="info-item">
            <span class="label">房间号</span>
            <span class="value">{{ bill.room_number }}</span>
          </div>
          <div class="info-item">
            <span class="label">探视住户</span>
            <span class="value">{{ bill.resident_name }}</span>
          </div>
          <div class="info-item">
            <span class="label">签到时间</span>
            <span class="value">{{ formatTime(bill.check_in_time) }}</span>
          </div>
          <div class="info-item">
            <span class="label">离开时间</span>
            <span class="value">{{ formatTime(bill.check_out_time) }}</span>
          </div>
          <div class="info-item">
            <span class="label">生成时间</span>
            <span class="value">{{ formatTime(bill.generated_at) }}</span>
          </div>
        </div>
      </div>

      <div class="bill-section">
        <h2 class="section-title">费用明细</h2>
        <div class="charge-table">
          <div class="charge-header">
            <span>项目</span>
            <span>说明</span>
            <span class="amount-col">金额</span>
          </div>
          <div v-for="item in bill.charge_items" :key="item.id" class="charge-row" :class="{ negative: item.amount < 0 }">
            <span class="ci-item">
              <span class="ci-tag" :class="item.charge_type">{{ chargeTypeLabel(item.charge_type) }}</span>
              {{ item.item_name }}
            </span>
            <span class="ci-desc">{{ item.description || '-' }}</span>
            <span class="ci-amount">{{ item.amount >= 0 ? '+' : '' }}¥{{ item.amount.toFixed(2) }}</span>
          </div>
        </div>
      </div>

      <div class="bill-summary-card">
        <div class="summary-row" v-if="bill.deposit_amount > 0">
          <span>押金收取</span>
          <span>¥{{ bill.deposit_amount.toFixed(2) }}</span>
        </div>
        <div class="summary-row" v-if="bill.deposit_refund_amount > 0">
          <span>押金退还</span>
          <span class="refund">-¥{{ bill.deposit_refund_amount.toFixed(2) }}</span>
        </div>
        <div class="summary-row" v-if="bill.item_damage_fee > 0">
          <span>物品损坏费</span>
          <span class="deduct">¥{{ bill.item_damage_fee.toFixed(2) }}</span>
        </div>
        <div class="summary-row" v-if="bill.item_lost_fee > 0">
          <span>物品丢失费</span>
          <span class="deduct">¥{{ bill.item_lost_fee.toFixed(2) }}</span>
        </div>
        <div class="summary-row" v-if="bill.overtime_fee > 0">
          <span>超时占用费</span>
          <span class="deduct">¥{{ bill.overtime_fee.toFixed(2) }}</span>
        </div>
        <div class="summary-row" v-if="bill.other_fee > 0">
          <span>其他费用</span>
          <span class="deduct">¥{{ bill.other_fee.toFixed(2) }}</span>
        </div>
        <div class="summary-row total">
          <span>应付金额</span>
          <span class="total-amount">¥{{ bill.total_amount.toFixed(2) }}</span>
        </div>
      </div>

      <div class="status-card">
        <div class="status-item">
          <span class="label">支付状态</span>
          <span class="status-badge" :class="bill.payment_status">{{ paymentStatusLabel(bill.payment_status) }}</span>
        </div>
        <div class="status-item">
          <span class="label">签收状态</span>
          <span class="status-badge" :class="bill.signature_status">{{ signatureStatusLabel(bill.signature_status) }}</span>
        </div>
      </div>

      <div v-if="bill.signature" class="signed-card">
        <div class="signed-title">
          <CheckCircle2 :size="20" color="#059669" />
          <span>已完成电子签名确认</span>
        </div>
        <div class="signed-info">
          <div><span class="label">签收人：</span>{{ bill.signature.signer_name }}</div>
          <div><span class="label">签收时间：</span>{{ formatTime(bill.signature.signed_at) }}</div>
          <div v-if="bill.signature.sign_device"><span class="label">设备：</span>{{ bill.signature.sign_device }}</div>
        </div>
        <img :src="bill.signature.signature_data" class="signature-image" alt="电子签名" />
      </div>

      <div v-else class="signature-section">
        <h2 class="section-title">电子签名确认</h2>
        
        <div class="sign-form">
          <div class="form-group">
            <label>签收人姓名 <span class="required">*</span></label>
            <InputText v-model="signerName" :placeholder="'请输入您的姓名，如：' + bill.visitor_name" />
          </div>

          <SignaturePad ref="signaturePadRef" @signature="onSignature" @change="onSignatureChange" />

          <div class="terms-box">
            <Checkbox v-model="agreeTerms" :binary="true" />
            <p class="terms-text">
              我已仔细阅读并确认以上费用明细无误，包括押金收取/退还、物品丢失或损坏扣费、超时占用附加费等所有记录。
              我同意以此电子签名作为确认凭证，确认本次探视相关费用已结清。
            </p>
          </div>

          <Button 
            label="确认签名" 
            :icon="submitting ? 'pi pi-spin pi-spinner' : 'pi pi-check'" 
            class="submit-btn" 
            :disabled="!canSubmit || submitting"
            @click="submitSignature"
          />
        </div>
      </div>

      <div class="footer-note">
        <p>如有疑问，请联系前台工作人员</p>
        <p class="timestamp">页面生成于 {{ currentTime }}</p>
      </div>
    </div>

    <div v-else class="error-box">
      <XCircle :size="48" color="#EF4444" />
      <h2>账单不存在</h2>
      <p>请检查链接是否正确，或联系前台工作人员</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import SignaturePad from '@/components/SignaturePad.vue'
import { billApi, type VisitorBill } from '@/api'
import InputText from 'primevue/inputtext'
import Button from 'primevue/button'
import Checkbox from 'primevue/checkbox'
import { FileText, CheckCircle2, XCircle } from 'lucide-vue-next'

const route = useRoute()
const bill = ref<VisitorBill | null>(null)
const loading = ref(true)
const submitting = ref(false)
const signaturePadRef = ref<InstanceType<typeof SignaturePad> | null>(null)

const signerName = ref('')
const signatureData = ref('')
const hasSignature = ref(false)
const agreeTerms = ref(false)

const currentTime = computed(() => {
  return new Date().toLocaleString('zh-CN')
})

const canSubmit = computed(() => {
  return (
    signerName.value.trim().length >= 2 &&
    hasSignature.value &&
    agreeTerms.value
  )
})

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

function onSignature(data: string) {
  signatureData.value = data
}

function onSignatureChange(val: boolean) {
  hasSignature.value = val
}

async function submitSignature() {
  if (!bill.value || !canSubmit.value || submitting.value) return

  submitting.value = true
  try {
    const updatedBill = await billApi.sign(bill.value.id, {
      signer_name: signerName.value.trim(),
      signature_data: signatureData.value,
      sign_device: navigator.userAgent.substring(0, 50),
    })
    bill.value = updatedBill
    alert('签名确认成功！感谢您的配合。')
  } catch (e: any) {
    alert(e.message || '签名失败，请重试')
  } finally {
    submitting.value = false
  }
}

async function loadBill() {
  const billId = route.params.id as string
  if (!billId) {
    loading.value = false
    return
  }

  try {
    bill.value = await billApi.get(parseInt(billId))
    signerName.value = bill.value.visitor_name
  } catch {
    bill.value = null
  } finally {
    loading.value = false
  }
}

onMounted(loadBill)
</script>

<style scoped>
.signature-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #FDF2F8 0%, #FCE7F3 100%);
  padding: 20px;
}

.loading-box,
.error-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  gap: 16px;
  text-align: center;
}

.loading-box p,
.error-box p {
  color: #6B7280;
  font-size: 14px;
}

.error-box h2 {
  color: #1F2937;
  font-size: 20px;
  margin: 0;
}

.bill-container {
  max-width: 600px;
  margin: 0 auto;
}

.bill-header {
  text-align: center;
  margin-bottom: 20px;
}

.logo-area {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
}

.logo-area h1 {
  font-size: 24px;
  font-weight: 700;
  color: #1F2937;
  margin: 0;
}

.bill-no {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #6B7280;
  background: white;
  padding: 4px 12px;
  border-radius: 12px;
  display: inline-block;
}

.bill-info-card {
  background: white;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 20px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item .label {
  font-size: 12px;
  color: #9CA3AF;
}

.info-item .value {
  font-size: 14px;
  font-weight: 500;
  color: #1F2937;
}

.bill-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #1F2937;
  margin: 0 0 12px 0;
  padding-left: 12px;
  border-left: 4px solid #E8A0BF;
}

.charge-table {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.charge-header {
  display: grid;
  grid-template-columns: 120px 1fr 80px;
  background: #F9FAFB;
  padding: 12px 16px;
  font-size: 12px;
  font-weight: 600;
  color: #6B7280;
}

.charge-header .amount-col {
  text-align: right;
}

.charge-row {
  display: grid;
  grid-template-columns: 120px 1fr 80px;
  padding: 12px 16px;
  border-top: 1px solid #F3F4F6;
  font-size: 13px;
  align-items: center;
}

.charge-row.negative {
  color: #059669;
}

.ci-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ci-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
  width: fit-content;
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

.bill-summary-card {
  background: linear-gradient(135deg, #FDF2F8 0%, #FCE7F3 100%);
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  font-size: 14px;
}

.summary-row .refund {
  color: #059669;
  font-weight: 600;
}

.summary-row .deduct {
  color: #DC2626;
  font-weight: 600;
}

.summary-row.total {
  border-top: 1px dashed #E8A0BF;
  margin-top: 8px;
  padding-top: 12px;
  font-size: 18px;
}

.summary-row.total .total-amount {
  color: #D4899F;
  font-weight: 700;
  font-size: 22px;
}

.status-card {
  background: white;
  border-radius: 12px;
  padding: 16px 20px;
  margin-bottom: 16px;
  display: flex;
  justify-content: space-between;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.status-item .label {
  font-size: 12px;
  color: #9CA3AF;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.status-badge.pending { background: #FEF3C7; color: #D97706; }
.status-badge.paid { background: #D1FAE5; color: #059669; }
.status-badge.partial_paid { background: #DBEAFE; color: #2563EB; }
.status-badge.waived { background: #E5E7EB; color: #4B5563; }
.status-badge.unsigned { background: #FEE2E2; color: #DC2626; }
.status-badge.signed { background: #D1FAE5; color: #059669; }

.signed-card {
  background: #ECFDF5;
  border: 2px solid #A7F3D0;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  text-align: center;
}

.signed-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #065F46;
  margin-bottom: 12px;
}

.signed-info {
  font-size: 13px;
  color: #065F46;
  margin-bottom: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.signed-info .label {
  font-weight: 500;
}

.signature-image {
  max-width: 240px;
  max-height: 100px;
  background: white;
  border-radius: 8px;
  border: 1px solid #D1FAE5;
  margin: 0 auto;
  display: block;
}

.signature-section {
  background: white;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.sign-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.form-group :deep(.p-inputtext) {
  width: 100%;
  padding: 12px 14px;
  font-size: 14px;
}

.required {
  color: #E74C3C;
}

.terms-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 14px;
  background: #F9FAFB;
  border-radius: 8px;
}

.terms-text {
  font-size: 12px;
  color: #4B5563;
  line-height: 1.6;
  margin: 0;
}

.submit-btn {
  width: 100%;
  padding: 14px;
  font-size: 16px;
  font-weight: 600;
  background: linear-gradient(135deg, #E8A0BF 0%, #D4899F 100%);
  border: none;
  border-radius: 10px;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(212, 137, 159, 0.4);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.footer-note {
  text-align: center;
  color: #9CA3AF;
  font-size: 12px;
  padding: 20px 0;
}

.footer-note p {
  margin: 4px 0;
}

.footer-note .timestamp {
  font-family: 'Courier New', monospace;
}
</style>
