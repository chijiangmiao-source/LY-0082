<template>
  <AppLayout>
    <div class="deposit-items-page">
      <h2 class="page-title">访客押金与物品领用管理</h2>

      <div class="summary-cards">
        <div class="summary-card" style="background: linear-gradient(135deg, #F59E0B, #D97706)">
          <div class="s-icon"><Wallet :size="24" color="white" /></div>
          <div class="s-info">
            <div class="s-number">{{ summary.pending_deposit_count }}<span class="s-unit">笔</span></div>
            <div class="s-label">押金未退</div>
            <div class="s-sub">¥{{ summary.pending_deposit_amount.toFixed(2) }}</div>
          </div>
        </div>
        <div class="summary-card" style="background: linear-gradient(135deg, #EF4444, #DC2626)">
          <div class="s-icon"><Clock :size="24" color="white" /></div>
          <div class="s-info">
            <div class="s-number">{{ summary.overdue_item_count }}<span class="s-unit">次</span></div>
            <div class="s-label">物品逾期未还</div>
          </div>
        </div>
        <div class="summary-card" style="background: linear-gradient(135deg, #8B5CF6, #7C3AED)">
          <div class="s-icon"><AlertOctagon :size="24" color="white" /></div>
          <div class="s-info">
            <div class="s-number">{{ summary.abnormal_item_count }}<span class="s-unit">次</span></div>
            <div class="s-label">异常物品（丢失/损坏）</div>
          </div>
        </div>
        <div class="summary-card" style="background: linear-gradient(135deg, #10B981, #059669)">
          <div class="s-icon"><TrendingUp :size="24" color="white" /></div>
          <div class="s-info">
            <div class="s-number">{{ summary.today_collected_count }}<span class="s-unit">笔</span></div>
            <div class="s-label">今日押金收取</div>
            <div class="s-sub">¥{{ summary.today_collected_amount.toFixed(2) }}</div>
          </div>
        </div>
      </div>

      <div v-if="summary.item_distribution.length" class="distribution-card">
        <h3 class="dist-title">高频异常物品分布</h3>
        <div class="dist-list">
          <div v-for="item in summary.item_distribution" :key="item.item_type" class="dist-item">
            <div class="dist-name">{{ item.item_name }}</div>
            <div class="dist-bar-wrap">
              <div class="dist-bar" :style="{ width: getDistWidth(item.total_count) + '%' }"></div>
            </div>
            <div class="dist-counts">
              <span>总数 {{ item.total_count }}</span>
              <span v-if="item.abnormal_count > 0" class="abnormal-tag">异常 {{ item.abnormal_count }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="main-tabs">
        <div class="tab" :class="{ active: activeTab === 'deposit' }" @click="activeTab = 'deposit'">
          <Wallet :size="18" />
          <span>押金管理</span>
        </div>
        <div class="tab" :class="{ active: activeTab === 'items' }" @click="activeTab = 'items'">
          <Package :size="18" />
          <span>物品领用</span>
        </div>
      </div>

      <div v-show="activeTab === 'deposit'" class="tab-content">
        <div class="action-bar">
          <div class="search-row">
            <span class="p-input-icon-left">
              <i class="pi pi-search" />
              <InputText v-model="depositSearch" placeholder="搜索访客姓名" @keyup.enter="loadDeposits" />
            </span>
            <Select v-model="depositStatusFilter" :options="depositStatusOptions" optionLabel="label" optionValue="value" placeholder="状态筛选" class="filter-select" @change="loadDeposits" />
            <Button label="搜索" icon="pi pi-search" @click="loadDeposits" />
          </div>
          <Button label="登记押金" icon="pi pi-plus" severity="primary" @click="openDepositDialog" />
        </div>

        <DataTable :value="deposits" paginator :rows="10" stripedRows tableStyle="min-width: 100%" :emptyMessage="'暂无押金记录'">
          <Column field="visitor_name" header="访客姓名" :style="{ width: '100px' }">
            <template #body="{ data }">
              <span class="strong">{{ data.visitor_name }}</span>
            </template>
          </Column>
          <Column field="appointment_no" header="关联预约" :style="{ width: '130px' }">
            <template #body="{ data }">
              <span class="apt-no">{{ data.appointment_no || '-' }}</span>
            </template>
          </Column>
          <Column field="room_number" header="房间号" :style="{ width: '80px' }">
            <template #body="{ data }">{{ data.room_number || '-' }}</template>
          </Column>
          <Column field="resident_name" header="探视住户" :style="{ width: '100px' }">
            <template #body="{ data }">{{ data.resident_name || '-' }}</template>
          </Column>
          <Column field="amount" header="押金金额" :style="{ width: '110px' }">
            <template #body="{ data }">
              <span class="amount">¥{{ Number(data.amount).toFixed(2) }}</span>
            </template>
          </Column>
          <Column header="状态" :style="{ width: '110px' }">
            <template #body="{ data }">
              <span class="deposit-status" :class="data.status">{{ depositStatusLabel(data.status) }}</span>
            </template>
          </Column>
          <Column field="collected_at" header="收取时间" :style="{ width: '150px' }" />
          <Column field="refunded_at" header="结算时间" :style="{ width: '150px' }">
            <template #body="{ data }">{{ data.refunded_at || '-' }}</template>
          </Column>
          <Column field="deduct_reason" header="扣费/备注" :style="{ minWidth: '140px' }">
            <template #body="{ data }">
              <span v-if="data.status === 'deducted' || data.status === 'partial_refunded'" class="deduct-text">
                ¥{{ Number(data.deduct_amount || 0).toFixed(2) }}：{{ data.deduct_reason }}
              </span>
              <span v-else-if="data.status === 'refunded'" class="refund-text">全额退还 ¥{{ Number(data.refund_amount || data.amount).toFixed(2) }}</span>
              <span v-else>-</span>
            </template>
          </Column>
          <Column header="操作" :style="{ width: '180px' }">
            <template #body="{ data }">
              <template v-if="data.status === 'collected'">
                <Button label="全额退还" size="small" severity="success" @click="openSettleDialog(data, 'refund')" class="mr-2" />
                <Button label="结算" size="small" severity="warning" @click="openSettleDialog(data, 'settle')" />
              </template>
              <template v-else>
                <span class="muted-text">已结算</span>
              </template>
            </template>
          </Column>
        </DataTable>
      </div>

      <div v-show="activeTab === 'items'" class="tab-content">
        <div class="action-bar">
          <div class="search-row">
            <span class="p-input-icon-left">
              <i class="pi pi-search" />
              <InputText v-model="itemSearch" placeholder="搜索访客姓名" @keyup.enter="loadItems" />
            </span>
            <Select v-model="itemStatusFilter" :options="itemStatusOptions" optionLabel="label" optionValue="value" placeholder="状态筛选" class="filter-select" @change="loadItems" />
            <Select v-model="itemTypeFilter" :options="itemTypeOptions" optionLabel="label" optionValue="value" placeholder="物品类型" class="filter-select" @change="loadItems" />
            <Button label="搜索" icon="pi pi-search" @click="loadItems" />
          </div>
          <Button label="登记领用" icon="pi pi-plus" severity="primary" @click="openItemDialog" />
        </div>

        <DataTable :value="items" paginator :rows="10" stripedRows tableStyle="min-width: 100%" :emptyMessage="'暂无领用记录'">
          <Column field="visitor_name" header="访客姓名" :style="{ width: '100px' }">
            <template #body="{ data }">
              <span class="strong">{{ data.visitor_name }}</span>
            </template>
          </Column>
          <Column field="appointment_no" header="关联预约" :style="{ width: '130px' }">
            <template #body="{ data }">
              <span class="apt-no">{{ data.appointment_no || '-' }}</span>
            </template>
          </Column>
          <Column field="room_number" header="房间号" :style="{ width: '80px' }">
            <template #body="{ data }">{{ data.room_number || '-' }}</template>
          </Column>
          <Column header="物品类型" :style="{ width: '100px' }">
            <template #body="{ data }">
              <span class="item-type" :class="data.item_type">{{ itemTypeLabel(data.item_type) }}</span>
            </template>
          </Column>
          <Column field="item_name" header="物品名称" :style="{ width: '130px' }">
            <template #body="{ data }">{{ data.item_name }}</template>
          </Column>
          <Column field="item_identifier" header="编号/标识" :style="{ width: '110px' }">
            <template #body="{ data }">{{ data.item_identifier || '-' }}</template>
          </Column>
          <Column header="归还状态" :style="{ width: '100px' }">
            <template #body="{ data }">
              <span class="item-status" :class="data.status">{{ itemStatusLabel(data.status) }}</span>
            </template>
          </Column>
          <Column field="loaned_at" header="发放时间" :style="{ width: '150px' }" />
          <Column field="due_return_at" header="应归还时间" :style="{ width: '150px' }">
            <template #body="{ data }">
              <span :class="{ overdue: data.due_return_at && isOverdue(data) && !['returned','lost','damaged'].includes(data.status) }">
                {{ data.due_return_at || '-' }}
              </span>
            </template>
          </Column>
          <Column field="returned_at" header="实际归还" :style="{ width: '150px' }">
            <template #body="{ data }">{{ data.returned_at || '-' }}</template>
          </Column>
          <Column field="abnormal_reason" header="异常说明" :style="{ minWidth: '140px' }">
            <template #body="{ data }">
              <span v-if="data.abnormal_reason" class="abnormal-text">{{ data.abnormal_reason }}</span>
              <span v-else>-</span>
            </template>
          </Column>
          <Column header="操作" :style="{ width: '200px' }">
            <template #body="{ data }">
              <template v-if="!['returned', 'lost', 'damaged'].includes(data.status)">
                <Button label="确认归还" size="small" severity="success" @click="openReturnDialog(data, 'return')" class="mr-2" />
                <Button label="异常" size="small" severity="danger" @click="openReturnDialog(data, 'abnormal')" />
              </template>
              <template v-else>
                <span class="muted-text">已处理</span>
              </template>
            </template>
          </Column>
        </DataTable>
      </div>

      <Dialog v-model:visible="depositDialogVisible" header="登记押金收取" :modal="true" :style="{ width: '520px' }" @hide="resetDepositForm">
        <div class="dialog-form">
          <div class="section-title">关联预约信息</div>
          <div class="search-apt-box">
            <div class="search-row2">
              <InputText v-model="aptSearchKeyword" placeholder="输入预约编号/访客姓名搜索" class="flex-1" @keyup.enter="searchAptForDeposit" />
              <Button label="搜索" icon="pi pi-search" @click="searchAptForDeposit" />
            </div>
            <div v-if="aptSearchResults.length" class="apt-result-list">
              <div v-for="apt in aptSearchResults" :key="apt.id"
                   class="apt-result-item"
                   :class="{ selected: selectedApt?.id === apt.id }"
                   @click="selectAptForDeposit(apt)">
                <div class="apt-item-top">
                  <span class="apt-no">{{ apt.appointment_no }}</span>
                  <span class="apt-status" :class="apt.status">{{ aptStatusLabel(apt.status) }}</span>
                </div>
                <div class="apt-item-body">
                  <span>访客：{{ apt.visitor_name }}</span>
                  <span>住户：{{ apt.resident_name }}（{{ apt.room_number }}）</span>
                  <span>时段：{{ apt.scheduled_start }} ~ {{ apt.scheduled_end }}</span>
                </div>
              </div>
            </div>
            <div v-else-if="aptSearched" class="empty-text">未找到相关预约</div>
            <div v-else class="empty-text hint">请先搜索并选择关联预约（必填）</div>
          </div>

          <div class="field-row">
            <div class="field">
              <label>访客姓名 <span class="required">*</span></label>
              <InputText v-model="depositForm.visitor_name" placeholder="请输入访客姓名" />
            </div>
            <div class="field">
              <label>押金金额 (元) <span class="required">*</span></label>
              <InputNumber v-model="depositForm.amount" :min="0" :step="50" :precision="2" prefix="¥" placeholder="0.00" />
            </div>
          </div>
          <div class="quick-amounts">
            <span class="quick-label">快捷金额：</span>
            <button v-for="amt in [50, 100, 200, 500]" :key="amt" class="quick-btn" @click="depositForm.amount = amt">¥{{ amt }}</button>
          </div>
          <div class="selected-info" v-if="selectedApt">
            <Check :size="16" color="#059669" />
            <span>已关联预约：{{ selectedApt.appointment_no }} · {{ selectedApt.visitor_name }} → {{ selectedApt.resident_name }}</span>
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="depositDialogVisible = false" />
          <Button label="确认收取" severity="primary" @click="submitDeposit" :disabled="!canSubmitDeposit" />
        </template>
      </Dialog>

      <Dialog v-model:visible="settleDialogVisible" header="押金结算" :modal="true" :style="{ width: '460px' }" @hide="resetSettleForm">
        <div v-if="currentDeposit" class="dialog-form">
          <div class="settle-info">
            <div class="info-row"><span class="k">访客姓名</span><span class="v">{{ currentDeposit.visitor_name }}</span></div>
            <div class="info-row"><span class="k">关联预约</span><span class="v apt-no">{{ currentDeposit.appointment_no }}</span></div>
            <div class="info-row"><span class="k">押金总额</span><span class="v amount">¥{{ Number(currentDeposit.amount).toFixed(2) }}</span></div>
          </div>

          <div class="field">
            <label>结算方式 <span class="required">*</span></label>
            <SelectButton v-model="settleForm.action" :options="settleActionOptions" optionLabel="label" optionValue="value" />
          </div>

          <div v-if="settleForm.action === 'partial_refund'" class="field">
            <label>实际退还金额 (元) <span class="required">*</span></label>
            <InputNumber v-model="settleForm.refund_amount" :min="0" :max="Number(currentDeposit.amount)" :precision="2" prefix="¥" />
            <small class="form-hint">扣费金额 = ¥{{ Number(currentDeposit.amount).toFixed(2) }} - 退还金额</small>
            <small v-if="settleFormError" class="form-error">{{ settleFormError }}</small>
          </div>

          <div v-if="settleForm.action === 'partial_refund' || settleForm.action === 'deduct'" class="field">
            <label>扣费/异常原因 <span class="required">*</span></label>
            <textarea v-model="settleForm.deduct_reason" class="form-textarea" rows="3" maxlength="200" placeholder="请说明扣费原因（如物品损坏、逾期未还等，2-200字）" />
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="settleDialogVisible = false" />
          <Button label="确认结算" severity="primary" @click="submitSettle" :disabled="!canSubmitSettle" />
        </template>
      </Dialog>

      <Dialog v-model:visible="itemDialogVisible" header="登记物品领用" :modal="true" :style="{ width: '560px' }" @hide="resetItemForm">
        <div class="dialog-form">
          <div class="section-title">关联预约信息</div>
          <div class="search-apt-box">
            <div class="search-row2">
              <InputText v-model="itemAptSearchKeyword" placeholder="输入预约编号/访客姓名搜索" class="flex-1" @keyup.enter="searchAptForItem" />
              <Button label="搜索" icon="pi pi-search" @click="searchAptForItem" />
            </div>
            <div v-if="itemAptSearchResults.length" class="apt-result-list">
              <div v-for="apt in itemAptSearchResults" :key="apt.id"
                   class="apt-result-item"
                   :class="{ selected: itemSelectedApt?.id === apt.id }"
                   @click="selectAptForItem(apt)">
                <div class="apt-item-top">
                  <span class="apt-no">{{ apt.appointment_no }}</span>
                  <span class="apt-status" :class="apt.status">{{ aptStatusLabel(apt.status) }}</span>
                </div>
                <div class="apt-item-body">
                  <span>访客：{{ apt.visitor_name }}</span>
                  <span>住户：{{ apt.resident_name }}（{{ apt.room_number }}）</span>
                </div>
              </div>
            </div>
            <div v-else-if="itemAptSearched" class="empty-text">未找到相关预约</div>
            <div v-else class="empty-text hint">请先搜索并选择关联预约（必填）</div>
          </div>

          <div class="field-row">
            <div class="field">
              <label>访客姓名 <span class="required">*</span></label>
              <InputText v-model="itemForm.visitor_name" placeholder="请输入访客姓名" />
            </div>
            <div class="field">
              <label>物品类型 <span class="required">*</span></label>
              <Select v-model="itemForm.item_type" :options="itemTypeOptions" optionLabel="label" optionValue="value" placeholder="选择类型" @change="handleItemTypeChange" />
            </div>
          </div>

          <div class="field-row">
            <div class="field">
              <label>物品名称 <span class="required">*</span></label>
              <Select v-model="itemForm.item_name" :options="itemNameOptions" optionLabel="label" optionValue="value" placeholder="选择/填写物品" :editable="true" />
            </div>
            <div class="field">
              <label>编号/标识</label>
              <InputText v-model="itemForm.item_identifier" placeholder="如：钥匙编号A-01、证件号等" />
            </div>
          </div>

          <div class="field">
            <label>应归还时间</label>
            <Calendar v-model="itemForm.due_return_at" showTime :stepHour="1" :stepMinute="15" dateFormat="yy-mm-dd" timeFormat="HH:mm" placeholder="如不填写则按预约结束时间" style="width: 100%" />
          </div>

          <div class="selected-info" v-if="itemSelectedApt">
            <Check :size="16" color="#059669" />
            <span>已关联预约：{{ itemSelectedApt.appointment_no }} · {{ itemSelectedApt.visitor_name }}</span>
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="itemDialogVisible = false" />
          <Button label="确认发放" severity="primary" @click="submitItem" :disabled="!canSubmitItem" />
        </template>
      </Dialog>

      <Dialog v-model:visible="returnDialogVisible" header="物品归还处理" :modal="true" :style="{ width: '460px' }" @hide="resetReturnForm">
        <div v-if="currentItem" class="dialog-form">
          <div class="settle-info">
            <div class="info-row"><span class="k">访客姓名</span><span class="v">{{ currentItem.visitor_name }}</span></div>
            <div class="info-row"><span class="k">物品类型</span><span class="v"><span class="item-type" :class="currentItem.item_type">{{ itemTypeLabel(currentItem.item_type) }}</span></span></div>
            <div class="info-row"><span class="k">物品名称</span><span class="v">{{ currentItem.item_name }} <span v-if="currentItem.item_identifier" class="muted-text">#{{ currentItem.item_identifier }}</span></span></div>
            <div class="info-row"><span class="k">发放时间</span><span class="v">{{ currentItem.loaned_at }}</span></div>
          </div>

          <div class="field">
            <label>处理方式 <span class="required">*</span></label>
            <SelectButton v-model="returnForm.action" :options="returnActionOptions" optionLabel="label" optionValue="value" />
          </div>

          <div v-if="returnForm.action !== 'return'" class="field">
            <label>异常原因 <span class="required">*</span></label>
            <textarea v-model="returnForm.abnormal_reason" class="form-textarea" rows="3" maxlength="200" :placeholder="returnForm.action === 'lost' ? '请说明物品丢失情况...' : '请说明物品损坏情况...'" />
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="returnDialogVisible = false" />
          <Button label="确认处理" severity="primary" @click="submitReturn" :disabled="!canSubmitReturn" />
        </template>
      </Dialog>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { depositApi, itemLoanApi, depositItemSummaryApi, appointmentApi } from '@/api'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'
import Button from 'primevue/button'
import InputText from 'primevue/inputtext'
import Select from 'primevue/select'
import SelectButton from 'primevue/selectbutton'
import Dialog from 'primevue/dialog'
import InputNumber from 'primevue/inputnumber'
import Calendar from 'primevue/calendar'
import { Wallet, Clock, AlertOctagon, TrendingUp, Package, Check } from 'lucide-vue-next'

const activeTab = ref<'deposit' | 'items'>('deposit')

const summary = reactive({
  pending_deposit_count: 0,
  pending_deposit_amount: 0,
  overdue_item_count: 0,
  abnormal_item_count: 0,
  today_collected_count: 0,
  today_collected_amount: 0,
  item_distribution: [] as any[],
})

const maxDistCount = computed(() =>
  Math.max(1, ...summary.item_distribution.map((d: any) => d.total_count))
)
function getDistWidth(count: number) {
  return (count / maxDistCount.value) * 100
}

const deposits = ref<any[]>([])
const depositSearch = ref('')
const depositStatusFilter = ref<string | null>(null)
const depositStatusOptions = [
  { label: '全部状态', value: null },
  { label: '待结算（已收取）', value: 'collected' },
  { label: '全额退还', value: 'refunded' },
  { label: '部分退还', value: 'partial_refunded' },
  { label: '全额扣费', value: 'deducted' },
]

const items = ref<any[]>([])
const itemSearch = ref('')
const itemStatusFilter = ref<string | null>(null)
const itemTypeFilter = ref<string | null>(null)
const itemStatusOptions = [
  { label: '全部状态', value: null },
  { label: '使用中', value: 'loaned' },
  { label: '已归还', value: 'returned' },
  { label: '逾期未还', value: 'overdue' },
  { label: '已丢失', value: 'lost' },
  { label: '已损坏', value: 'damaged' },
]
const itemTypeOptions = [
  { label: '全部类型', value: null },
  { label: '临时证件', value: 'temporary_id' },
  { label: '陪护服', value: 'escort_clothes' },
  { label: '储物柜钥匙', value: 'locker_key' },
  { label: '陪护床用品', value: 'escort_bed' },
  { label: '其他物品', value: 'other' },
]
const itemNameMap: Record<string, { label: string; value: string }[]> = {
  temporary_id: [
    { label: '临时出入证', value: '临时出入证' },
    { label: '访客门禁卡', value: '访客门禁卡' },
  ],
  escort_clothes: [
    { label: '陪护服（M号）', value: '陪护服（M号）' },
    { label: '陪护服（L号）', value: '陪护服（L号）' },
    { label: '陪护服（XL号）', value: '陪护服（XL号）' },
    { label: '一次性鞋套', value: '一次性鞋套' },
  ],
  locker_key: [
    { label: '储物柜钥匙', value: '储物柜钥匙' },
  ],
  escort_bed: [
    { label: '陪护折叠床', value: '陪护折叠床' },
    { label: '枕头被褥套装', value: '枕头被褥套装' },
  ],
  other: [],
}
const itemNameOptions = ref<{ label: string; value: string }[]>([])

function depositStatusLabel(s: string) {
  const m: Record<string, string> = {
    collected: '待结算',
    refunded: '全额退还',
    partial_refunded: '部分退还',
    deducted: '全额扣费',
  }
  return m[s] || s
}

function itemStatusLabel(s: string) {
  const m: Record<string, string> = {
    loaned: '使用中',
    returned: '已归还',
    overdue: '逾期',
    lost: '已丢失',
    damaged: '已损坏',
  }
  return m[s] || s
}

function itemTypeLabel(t: string) {
  const m: Record<string, string> = {
    temporary_id: '临时证件',
    escort_clothes: '陪护服',
    locker_key: '储物柜钥匙',
    escort_bed: '陪护床用品',
    other: '其他',
  }
  return m[t] || t
}

function aptStatusLabel(s: string) {
  const m: Record<string, string> = { pending: '待审核', approved: '已通过', checked_in: '已签到', checked_out: '已签退', cancelled: '已取消', rejected: '已拒绝' }
  return m[s] || s
}

function isOverdue(item: any) {
  if (!item.due_return_at) return false
  return new Date(item.due_return_at.replace(' ', 'T')) < new Date()
}

async function loadSummary() {
  try {
    const data = await depositItemSummaryApi.get()
    Object.assign(summary, data)
  } catch {}
}

async function loadDeposits() {
  try {
    const params: any = {}
    if (depositSearch.value.trim()) params.visitor_name = depositSearch.value.trim()
    if (depositStatusFilter.value) params.status = depositStatusFilter.value
    deposits.value = await depositApi.list(params)
  } catch {
    deposits.value = []
  }
}

async function loadItems() {
  try {
    const params: any = {}
    if (itemSearch.value.trim()) params.visitor_name = itemSearch.value.trim()
    if (itemStatusFilter.value) params.status = itemStatusFilter.value
    if (itemTypeFilter.value) params.item_type = itemTypeFilter.value
    items.value = await itemLoanApi.list(params)
  } catch {
    items.value = []
  }
}

function refreshAll() {
  loadSummary()
  loadDeposits()
  loadItems()
}

const depositDialogVisible = ref(false)
const aptSearchKeyword = ref('')
const aptSearchResults = ref<any[]>([])
const aptSearched = ref(false)
const selectedApt = ref<any>(null)

const depositForm = reactive({
  visitor_name: '',
  amount: 0,
})

const canSubmitDeposit = computed(() => {
  return (
    !!selectedApt.value &&
    depositForm.visitor_name.trim().length >= 2 &&
    depositForm.amount > 0
  )
})

function openDepositDialog() {
  resetDepositForm()
  depositDialogVisible.value = true
}

function resetDepositForm() {
  depositForm.visitor_name = ''
  depositForm.amount = 0
  aptSearchKeyword.value = ''
  aptSearchResults.value = []
  aptSearched.value = false
  selectedApt.value = null
}

async function searchAptForDeposit() {
  const q = aptSearchKeyword.value.trim()
  if (!q) return
  aptSearched.value = true
  try {
    const params: any = {}
    if (q.startsWith('VT') || q.startsWith('vt')) params.appointment_no = q
    else params.visitor_name = q
    aptSearchResults.value = await appointmentApi.search(params)
  } catch {
    aptSearchResults.value = []
  }
}

function selectAptForDeposit(apt: any) {
  selectedApt.value = apt
  if (!depositForm.visitor_name.trim()) depositForm.visitor_name = apt.visitor_name
}

async function submitDeposit() {
  if (!canSubmitDeposit.value) return
  if (!selectedApt.value) {
    alert('请先搜索并选择关联的预约')
    return
  }
  try {
    await depositApi.create({
      appointment_id: selectedApt.value.id,
      visit_id: selectedApt.value.visit_id,
      visitor_name: depositForm.visitor_name.trim(),
      amount: Number(depositForm.amount),
    })
    alert('押金登记成功')
    depositDialogVisible.value = false
    refreshAll()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

const settleDialogVisible = ref(false)
const currentDeposit = ref<any>(null)
const settleForm = reactive({
  action: 'refund' as 'refund' | 'partial_refund' | 'deduct',
  refund_amount: 0,
  deduct_reason: '',
})
const settleActionOptions = [
  { label: '全额退还', value: 'refund' },
  { label: '部分退还', value: 'partial_refund' },
  { label: '全额扣费', value: 'deduct' },
]

const canSubmitSettle = computed(() => {
  if (settleForm.action === 'refund') return true
  if (settleForm.action === 'partial_refund') {
    const refAmt = Number(settleForm.refund_amount)
    const total = Number(currentDeposit.value?.amount || 0)
    return (
      !isNaN(refAmt) &&
      refAmt > 0 &&
      refAmt < total &&
      settleForm.deduct_reason.trim().length >= 2
    )
  }
  if (settleForm.action === 'deduct') {
    return settleForm.deduct_reason.trim().length >= 2
  }
  return false
})

const settleFormError = computed(() => {
  if (settleForm.action !== 'partial_refund' || !currentDeposit.value) return ''
  const refAmt = Number(settleForm.refund_amount)
  const total = Number(currentDeposit.value.amount)
  if (isNaN(refAmt)) return '请输入有效的退款金额'
  if (refAmt < 0) return '退款金额不能为负数'
  if (refAmt === 0) return '退款金额必须大于 0，否则请选择「全额扣费」'
  if (refAmt >= total) return '部分退款金额必须小于押金总额，否则请选择「全额退还」'
  return ''
})

function openSettleDialog(deposit: any, mode: string) {
  currentDeposit.value = deposit
  settleForm.action = mode === 'refund' ? 'refund' : 'partial_refund'
  settleForm.refund_amount = Number(deposit.amount)
  settleForm.deduct_reason = ''
  settleDialogVisible.value = true
}

function resetSettleForm() {
  currentDeposit.value = null
  settleForm.action = 'refund'
  settleForm.refund_amount = 0
  settleForm.deduct_reason = ''
}

async function submitSettle() {
  if (!canSubmitSettle.value || !currentDeposit.value) return
  if (settleForm.action === 'partial_refund' && settleFormError.value) {
    alert(settleFormError.value)
    return
  }
  try {
    await depositApi.settle(currentDeposit.value.id, {
      action: settleForm.action,
      refund_amount: settleForm.action === 'partial_refund' ? Number(settleForm.refund_amount) : undefined,
      deduct_reason: settleForm.deduct_reason.trim() || undefined,
    })
    alert('结算成功')
    settleDialogVisible.value = false
    refreshAll()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

const itemDialogVisible = ref(false)
const itemAptSearchKeyword = ref('')
const itemAptSearchResults = ref<any[]>([])
const itemAptSearched = ref(false)
const itemSelectedApt = ref<any>(null)

const itemForm = reactive({
  visitor_name: '',
  item_type: '',
  item_name: '',
  item_identifier: '',
  due_return_at: null as Date | null,
})

const canSubmitItem = computed(() => {
  return (
    !!itemSelectedApt.value &&
    itemForm.visitor_name.trim().length >= 2 &&
    itemForm.item_type &&
    itemForm.item_name.trim()
  )
})

function openItemDialog() {
  resetItemForm()
  itemDialogVisible.value = true
}

function resetItemForm() {
  itemForm.visitor_name = ''
  itemForm.item_type = ''
  itemForm.item_name = ''
  itemForm.item_identifier = ''
  itemForm.due_return_at = null
  itemAptSearchKeyword.value = ''
  itemAptSearchResults.value = []
  itemAptSearched.value = false
  itemSelectedApt.value = null
  itemNameOptions.value = []
}

function handleItemTypeChange() {
  itemNameOptions.value = itemNameMap[itemForm.item_type] || []
  if (itemNameOptions.value.length && !itemForm.item_name) {
    itemForm.item_name = itemNameOptions.value[0].value
  } else if (!itemNameOptions.value.length) {
    //
  }
}

async function searchAptForItem() {
  const q = itemAptSearchKeyword.value.trim()
  if (!q) return
  itemAptSearched.value = true
  try {
    const params: any = {}
    if (q.startsWith('VT') || q.startsWith('vt')) params.appointment_no = q
    else params.visitor_name = q
    itemAptSearchResults.value = await appointmentApi.search(params)
  } catch {
    itemAptSearchResults.value = []
  }
}

function selectAptForItem(apt: any) {
  itemSelectedApt.value = apt
  if (!itemForm.visitor_name.trim()) itemForm.visitor_name = apt.visitor_name
  if (!itemForm.due_return_at && apt.scheduled_end) {
    try {
      itemForm.due_return_at = new Date(apt.scheduled_end.replace(' ', 'T'))
    } catch {}
  }
}

async function submitItem() {
  if (!canSubmitItem.value) return
  if (!itemSelectedApt.value) {
    alert('请先搜索并选择关联的预约')
    return
  }
  try {
    let dueStr: string | undefined
    if (itemForm.due_return_at) {
      dueStr = itemForm.due_return_at.toISOString()
    }
    await itemLoanApi.create({
      appointment_id: itemSelectedApt.value.id,
      visit_id: itemSelectedApt.value?.visit_id,
      visitor_name: itemForm.visitor_name.trim(),
      item_type: itemForm.item_type,
      item_name: itemForm.item_name.trim(),
      item_identifier: itemForm.item_identifier.trim() || undefined,
      due_return_at: dueStr,
    })
    alert('物品领用登记成功')
    itemDialogVisible.value = false
    refreshAll()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

const returnDialogVisible = ref(false)
const currentItem = ref<any>(null)
const returnForm = reactive({
  action: 'return' as 'return' | 'lost' | 'damaged',
  abnormal_reason: '',
})
const returnActionOptions = [
  { label: '正常归还', value: 'return' },
  { label: '物品丢失', value: 'lost' },
  { label: '物品损坏', value: 'damaged' },
]

const canSubmitReturn = computed(() => {
  if (returnForm.action === 'return') return true
  return returnForm.abnormal_reason.trim().length >= 2
})

function openReturnDialog(item: any, mode: string) {
  currentItem.value = item
  returnForm.action = mode === 'abnormal' ? 'damaged' : 'return'
  returnForm.abnormal_reason = ''
  returnDialogVisible.value = true
}

function resetReturnForm() {
  currentItem.value = null
  returnForm.action = 'return'
  returnForm.abnormal_reason = ''
}

async function submitReturn() {
  if (!canSubmitReturn.value || !currentItem.value) return
  try {
    await itemLoanApi.returnItem(currentItem.value.id, {
      action: returnForm.action,
      abnormal_reason: returnForm.abnormal_reason.trim() || undefined,
    })
    alert('归还处理成功')
    returnDialogVisible.value = false
    refreshAll()
  } catch (e: any) {
    alert(e.message || '操作失败')
  }
}

onMounted(refreshAll)
</script>

<style scoped>
.deposit-items-page {
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
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px 24px;
}

.dist-item {
  display: grid;
  grid-template-columns: 90px 1fr auto;
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
  gap: 8px;
  font-size: 12px;
  color: #6B7280;
}

.abnormal-tag {
  color: #DC2626;
  font-weight: 600;
}

.main-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #E5E7EB;
  margin-bottom: 20px;
}

.main-tabs .tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  cursor: pointer;
  color: #6B7280;
  font-weight: 500;
  font-size: 14px;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: all 0.2s;
}

.main-tabs .tab:hover {
  color: #D4899F;
}

.main-tabs .tab.active {
  color: #D4899F;
  border-bottom-color: #D4899F;
}

.tab-content {
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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
  width: 220px;
}

.filter-select {
  width: 160px;
}

.strong {
  font-weight: 600;
  color: #2D3436;
}

.apt-no {
  font-family: 'Courier New', monospace;
  font-weight: 600;
  color: #4F46E5;
  font-size: 12.5px;
}

.amount {
  font-weight: 700;
  color: #D97706;
}

.deposit-status {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.deposit-status.collected { background: #FEF3C7; color: #D97706; }
.deposit-status.refunded { background: #D1FAE5; color: #059669; }
.deposit-status.partial_refunded { background: #DBEAFE; color: #2563EB; }
.deposit-status.deducted { background: #FEE2E2; color: #DC2626; }

.item-type {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.item-type.temporary_id { background: #DBEAFE; color: #2563EB; }
.item-type.escort_clothes { background: #FCE7F3; color: #BE185D; }
.item-type.locker_key { background: #FEF3C7; color: #B45309; }
.item-type.escort_bed { background: #D1FAE5; color: #047857; }
.item-type.other { background: #F3F4F6; color: #4B5563; }

.item-status {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}
.item-status.loaned { background: #DBEAFE; color: #2563EB; }
.item-status.returned { background: #D1FAE5; color: #059669; }
.item-status.overdue { background: #FEE2E2; color: #DC2626; }
.item-status.lost { background: #1F2937; color: #F9FAFB; }
.item-status.damaged { background: #FEF3C7; color: #B45309; }

.overdue {
  color: #DC2626;
  font-weight: 600;
}

.deduct-text {
  color: #DC2626;
  font-size: 12.5px;
}
.refund-text {
  color: #059669;
  font-size: 12.5px;
}
.abnormal-text {
  color: #B45309;
  font-size: 12.5px;
}
.muted-text {
  color: #9CA3AF;
  font-size: 12.5px;
}
.mr-2 {
  margin-right: 8px;
}

.dialog-form .section-title {
  font-size: 13px;
  font-weight: 600;
  color: #6B7280;
  margin: 4px 0 10px;
  padding-left: 8px;
  border-left: 3px solid #E8A0BF;
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
.field :deep(.p-select),
.field :deep(.p-inputnumber) {
  width: 100%;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.field-row .field {
  margin-bottom: 14px;
}

.required {
  color: #E74C3C;
}

.quick-amounts {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: -4px 0 14px;
  flex-wrap: wrap;
}
.quick-label {
  font-size: 12px;
  color: #6B7280;
}
.quick-btn {
  padding: 5px 12px;
  border-radius: 16px;
  border: 1px solid #E5E7EB;
  background: #F9FAFB;
  font-size: 12px;
  color: #4B5563;
  cursor: pointer;
  transition: all 0.15s;
}
.quick-btn:hover {
  background: #FEF2F7;
  border-color: #E8A0BF;
  color: #D4899F;
}

.search-apt-box {
  background: #F9FAFB;
  border-radius: 10px;
  padding: 14px;
  margin-bottom: 18px;
}

.search-row2 {
  display: flex;
  gap: 8px;
  align-items: center;
  margin-bottom: 10px;
}
.flex-1 { flex: 1; }

.apt-result-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 180px;
  overflow-y: auto;
}

.apt-result-item {
  background: white;
  border: 1.5px solid #E5E7EB;
  border-radius: 8px;
  padding: 10px 12px;
  cursor: pointer;
  transition: all 0.15s;
}
.apt-result-item:hover {
  border-color: #E8A0BF;
  background: #FEF7FA;
}
.apt-result-item.selected {
  border-color: #D4899F;
  background: #FEF2F7;
  box-shadow: 0 0 0 2px rgba(232, 160, 191, 0.2);
}

.apt-item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.apt-status {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 500;
}
.apt-status.pending { background: #FEF3C7; color: #D97706; }
.apt-status.approved { background: #DBEAFE; color: #2563EB; }
.apt-status.checked_in { background: #D1FAE5; color: #059669; }
.apt-status.checked_out { background: #E0E7FF; color: #4F46E5; }
.apt-status.rejected { background: #FEE2E2; color: #DC2626; }
.apt-status.cancelled { background: #F3F4F6; color: #6B7280; }

.apt-item-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  font-size: 12px;
  color: #6B7280;
}

.empty-text {
  text-align: center;
  padding: 16px;
  color: #9CA3AF;
  font-size: 13px;
}

.selected-info {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #ECFDF5;
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;
  color: #065F46;
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #D1D5DB;
  border-radius: 6px;
  font-size: 13px;
  font-family: inherit;
  resize: vertical;
  min-height: 72px;
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

.form-error {
  display: block;
  margin-top: 4px;
  font-size: 11.5px;
  color: #DC2626;
  font-weight: 500;
}

.empty-text.hint {
  color: #9CA3AF;
  font-style: italic;
  background: #FFFBEB;
  border-radius: 6px;
  border: 1px dashed #FCD34D;
  padding: 10px;
}

.settle-info {
  background: #F9FAFB;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 16px;
}
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  font-size: 13px;
}
.info-row .k {
  color: #6B7280;
}
.info-row .v {
  font-weight: 500;
  color: #2D3436;
}
</style>
