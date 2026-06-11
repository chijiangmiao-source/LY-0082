<template>
  <AppLayout>
    <div class="rooms-page">
      <h2 class="page-title">楼层房间管理</h2>
      <div class="rooms-layout">
        <div class="floor-panel">
          <div class="panel-header">
            <h3>楼层</h3>
            <Button v-if="authStore.isAdmin" label="添加楼层" icon="pi pi-plus" size="small" @click="showFloorDialog()" />
          </div>
          <div class="floor-list">
            <div
              v-for="floor in floors"
              :key="floor.id"
              class="floor-item"
              :class="{ active: selectedFloor?.id === floor.id }"
              @click="selectFloor(floor)"
            >
              <span>{{ floor.name }}</span>
              <div v-if="authStore.isAdmin" class="floor-actions">
                <button class="icon-btn" @click.stop="showFloorDialog(floor)">
                  <Pencil :size="14" />
                </button>
                <button class="icon-btn danger" @click.stop="handleDeleteFloor(floor)">
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="room-panel">
          <div class="panel-header">
            <h3>{{ selectedFloor?.name || '请选择楼层' }} - 房间</h3>
            <Button v-if="authStore.isAdmin && selectedFloor" label="添加房间" icon="pi pi-plus" size="small" @click="showRoomDialog()" />
          </div>
          <div class="room-grid" v-if="filteredRooms.length">
            <div v-for="room in filteredRooms" :key="room.id" class="room-card">
              <div class="room-number">{{ room.room_number }}</div>
              <div class="room-type">{{ roomTypeLabel(room.room_type) }}</div>
              <div class="room-status">
                <span class="status-badge" :class="room.occupancy_status">
                  {{ statusLabel(room.occupancy_status) }}
                </span>
              </div>
              <div class="room-visitors">
                <Users :size="14" />
                <span>{{ room.current_visitors || 0 }} / {{ room.max_visitors }}</span>
              </div>
              <div v-if="authStore.isAdmin" class="room-actions">
                <button class="icon-btn" @click="showRoomDialog(room)">
                  <Pencil :size="14" />
                </button>
                <button class="icon-btn danger" @click="handleDeleteRoom(room)">
                  <Trash2 :size="14" />
                </button>
              </div>
            </div>
          </div>
          <div v-else class="empty-state">暂无房间</div>
        </div>
      </div>

      <Dialog v-model:visible="floorDialogVisible" :header="floorForm.id ? '编辑楼层' : '添加楼层'" :modal="true" :style="{ width: '400px' }">
        <div class="dialog-form">
          <div class="field">
            <label>楼层名称</label>
            <InputText v-model="floorForm.name" placeholder="请输入楼层名称" />
          </div>
          <div class="field">
            <label>排序</label>
            <InputText v-model="floorForm.sort_order" type="number" placeholder="排序号" />
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="floorDialogVisible = false" />
          <Button label="保存" @click="handleSaveFloor" />
        </template>
      </Dialog>

      <Dialog v-model:visible="roomDialogVisible" :header="roomForm.id ? '编辑房间' : '添加房间'" :modal="true" :style="{ width: '450px' }">
        <div class="dialog-form">
          <div class="field">
            <label>房间号</label>
            <InputText v-model="roomForm.room_number" placeholder="请输入房间号" />
          </div>
          <div class="field">
            <label>房间类型</label>
            <Dropdown v-model="roomForm.room_type" :options="roomTypes" optionLabel="label" optionValue="value" placeholder="请选择房间类型" />
          </div>
          <div class="field">
            <label>入住状态</label>
            <Dropdown v-model="roomForm.occupancy_status" :options="occupancyStatuses" optionLabel="label" optionValue="value" placeholder="请选择入住状态" />
          </div>
          <div class="field">
            <label>最大访客数</label>
            <InputText v-model="roomForm.max_visitors" type="number" placeholder="最大访客数" />
          </div>
        </div>
        <template #footer>
          <Button label="取消" severity="secondary" @click="roomDialogVisible = false" />
          <Button label="保存" @click="handleSaveRoom" />
        </template>
      </Dialog>
    </div>
  </AppLayout>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import AppLayout from '@/components/AppLayout.vue'
import { useAuthStore } from '@/stores/auth'
import { floorApi, roomApi } from '@/api'
import { Users, Pencil, Trash2 } from 'lucide-vue-next'
import Button from 'primevue/button'
import Dialog from 'primevue/dialog'
import InputText from 'primevue/inputtext'
import Dropdown from 'primevue/dropdown'

const authStore = useAuthStore()

const floors = ref<any[]>([])
const rooms = ref<any[]>([])
const selectedFloor = ref<any>(null)

const floorDialogVisible = ref(false)
const roomDialogVisible = ref(false)

const floorForm = ref<{ id?: number; name: string; sort_order: string }>({ name: '', sort_order: '0' })
const roomForm = ref<{ id?: number; room_number: string; floor_id: number; room_type: string; occupancy_status: string; max_visitors: string }>({
  room_number: '', floor_id: 0, room_type: 'single', occupancy_status: 'vacant', max_visitors: '2',
})

const roomTypes = [
  { label: '单人间', value: 'single' },
  { label: '双人间', value: 'double' },
  { label: '套房', value: 'suite' },
  { label: 'VIP房', value: 'vip' },
]

const occupancyStatuses = [
  { label: '空闲', value: 'vacant' },
  { label: '已入住', value: 'occupied' },
  { label: '维护中', value: 'maintenance' },
]

const filteredRooms = computed(() => {
  if (!selectedFloor.value) return []
  return rooms.value.filter((r: any) => r.floor_id === selectedFloor.value.id)
})

function roomTypeLabel(type: string) {
  const map: Record<string, string> = { single: '单人间', double: '双人间', suite: '套房', vip: 'VIP房' }
  return map[type] || type
}

function statusLabel(status: string) {
  const map: Record<string, string> = { vacant: '空闲', occupied: '已入住', maintenance: '维护中' }
  return map[status] || status
}

async function loadData() {
  try {
    floors.value = await floorApi.list()
    rooms.value = await roomApi.list()
    if (floors.value.length && !selectedFloor.value) {
      selectedFloor.value = floors.value[0]
    }
  } catch {}
}

function selectFloor(floor: any) {
  selectedFloor.value = floor
}

function showFloorDialog(floor?: any) {
  if (floor) {
    floorForm.value = { id: floor.id, name: floor.name, sort_order: String(floor.sort_order) }
  } else {
    floorForm.value = { name: '', sort_order: '0' }
  }
  floorDialogVisible.value = true
}

function showRoomDialog(room?: any) {
  if (room) {
    roomForm.value = { id: room.id, room_number: room.room_number, floor_id: room.floor_id, room_type: room.room_type, occupancy_status: room.occupancy_status, max_visitors: String(room.max_visitors) }
  } else {
    roomForm.value = { room_number: '', floor_id: selectedFloor.value?.id || 0, room_type: 'single', occupancy_status: 'vacant', max_visitors: '2' }
  }
  roomDialogVisible.value = true
}

async function handleSaveFloor() {
  try {
    if (floorForm.value.id) {
      await floorApi.update(floorForm.value.id, { name: floorForm.value.name, sort_order: Number(floorForm.value.sort_order) })
    } else {
      await floorApi.create({ name: floorForm.value.name, sort_order: Number(floorForm.value.sort_order) })
    }
    floorDialogVisible.value = false
    await loadData()
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

async function handleDeleteFloor(floor: any) {
  if (!confirm(`确定删除楼层「${floor.name}」？`)) return
  try {
    await floorApi.delete(floor.id)
    if (selectedFloor.value?.id === floor.id) selectedFloor.value = null
    await loadData()
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}

async function handleSaveRoom() {
  try {
    const data = { ...roomForm.value, max_visitors: Number(roomForm.value.max_visitors) }
    if (roomForm.value.id) {
      await roomApi.update(roomForm.value.id, data)
    } else {
      await roomApi.create(data)
    }
    roomDialogVisible.value = false
    await loadData()
  } catch (e: any) {
    alert(e.message || '保存失败')
  }
}

async function handleDeleteRoom(room: any) {
  if (!confirm(`确定删除房间「${room.room_number}」？`)) return
  try {
    await roomApi.delete(room.id)
    await loadData()
  } catch (e: any) {
    alert(e.message || '删除失败')
  }
}

onMounted(loadData)
</script>

<style scoped>
.rooms-page {
  max-width: 1400px;
}

.page-title {
  font-size: 24px;
  font-weight: 700;
  color: #2D3436;
  margin: 0 0 24px;
}

.rooms-layout {
  display: flex;
  gap: 24px;
}

.floor-panel {
  width: 280px;
  flex-shrink: 0;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #2D3436;
}

.floor-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.floor-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.floor-item:hover {
  background: #F8D7E4;
}

.floor-item.active {
  background: #E8A0BF;
  color: white;
}

.floor-actions {
  display: flex;
  gap: 4px;
}

.icon-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  color: #666;
}

.icon-btn:hover {
  background: rgba(0, 0, 0, 0.1);
}

.icon-btn.danger:hover {
  color: #E74C3C;
}

.room-panel {
  flex: 1;
  background: white;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.room-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 16px;
}

.room-card {
  background: #F8D7E4;
  border-radius: 12px;
  padding: 16px;
  text-align: center;
  transition: transform 0.2s;
}

.room-card:hover {
  transform: translateY(-2px);
}

.room-number {
  font-size: 20px;
  font-weight: 700;
  color: #2D3436;
  margin-bottom: 8px;
}

.room-type {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.status-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.vacant {
  background: #D5F5E3;
  color: #27AE60;
}

.status-badge.occupied {
  background: #FADBD8;
  color: #E74C3C;
}

.status-badge.maintenance {
  background: #FEF3C7;
  color: #F59E0B;
}

.room-visitors {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 8px;
  font-size: 13px;
  color: #666;
}

.room-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
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
  color: #2D3436;
}

.dialog-form .field .p-inputtext,
.dialog-form .field .p-dropdown {
  width: 100%;
}
</style>
