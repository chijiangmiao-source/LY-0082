<template>
  <div class="signature-pad">
    <div class="pad-header">
      <span class="pad-title">请在下方签名区域手写签名</span>
      <div class="pad-actions">
        <Button label="清除" icon="pi pi-eraser" severity="secondary" size="small" @click="clear" />
      </div>
    </div>
    <div class="canvas-container" :class="{ 'has-signature': hasSignature }">
      <canvas
        ref="canvasRef"
        :width="canvasWidth"
        :height="canvasHeight"
        @mousedown="startDrawing"
        @mousemove="draw"
        @mouseup="stopDrawing"
        @mouseleave="stopDrawing"
        @touchstart.prevent="handleTouchStart"
        @touchmove.prevent="handleTouchMove"
        @touchend.prevent="stopDrawing"
      ></canvas>
      <div v-if="!hasSignature" class="placeholder-text">
        <PenLine :size="32" class="placeholder-icon" />
        <span>请在此处签名</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import Button from 'primevue/button'
import { PenLine } from 'lucide-vue-next'

const props = defineProps<{
  width?: number
  height?: number
  lineColor?: string
  lineWidth?: number
}>()

const emit = defineEmits<{
  (e: 'change', hasSignature: boolean): void
  (e: 'signature', data: string): void
}>()

const canvasRef = ref<HTMLCanvasElement | null>(null)
const ctx = ref<CanvasRenderingContext2D | null>(null)
const isDrawing = ref(false)
const hasSignature = ref(false)
const lastX = ref(0)
const lastY = ref(0)

const canvasWidth = computed(() => props.width || 500)
const canvasHeight = computed(() => props.height || 200)
const lineColor = computed(() => props.lineColor || '#1F2937')
const lineWidth = computed(() => props.lineWidth || 3)

onMounted(() => {
  initCanvas()
  window.addEventListener('resize', handleResize)
})

watch(hasSignature, (val) => {
  emit('change', val)
})

function initCanvas() {
  if (!canvasRef.value) return

  const canvas = canvasRef.value
  const container = canvas.parentElement
  if (container) {
    const rect = container.getBoundingClientRect()
    canvas.width = rect.width
    canvas.height = canvasHeight.value
  }

  ctx.value = canvas.getContext('2d')
  if (ctx.value) {
    ctx.value.strokeStyle = lineColor.value
    ctx.value.lineWidth = lineWidth.value
    ctx.value.lineCap = 'round'
    ctx.value.lineJoin = 'round'
    ctx.value.fillStyle = '#FFFFFF'
    ctx.value.fillRect(0, 0, canvas.width, canvas.height)
  }
}

function handleResize() {
  const oldData = hasSignature.value ? getSignatureData() : null
  initCanvas()
  if (oldData && ctx.value) {
    const img = new Image()
    img.onload = () => {
      ctx.value?.drawImage(img, 0, 0)
    }
    img.src = oldData
  }
}

function getPosition(e: MouseEvent | Touch) {
  if (!canvasRef.value) return { x: 0, y: 0 }
  const rect = canvasRef.value.getBoundingClientRect()
  const scaleX = canvasRef.value.width / rect.width
  const scaleY = canvasRef.value.height / rect.height
  return {
    x: (e.clientX - rect.left) * scaleX,
    y: (e.clientY - rect.top) * scaleY,
  }
}

function startDrawing(e: MouseEvent) {
  isDrawing.value = true
  const pos = getPosition(e)
  lastX.value = pos.x
  lastY.value = pos.y
  if (ctx.value) {
    ctx.value.beginPath()
    ctx.value.moveTo(pos.x, pos.y)
  }
}

function draw(e: MouseEvent) {
  if (!isDrawing.value || !ctx.value) return
  const pos = getPosition(e)
  ctx.value.lineTo(pos.x, pos.y)
  ctx.value.stroke()
  hasSignature.value = true
}

function stopDrawing() {
  isDrawing.value = false
  if (hasSignature.value) {
    emit('signature', getSignatureData())
  }
}

function handleTouchStart(e: TouchEvent) {
  if (e.touches.length === 0) return
  isDrawing.value = true
  const pos = getPosition(e.touches[0])
  lastX.value = pos.x
  lastY.value = pos.y
  if (ctx.value) {
    ctx.value.beginPath()
    ctx.value.moveTo(pos.x, pos.y)
  }
}

function handleTouchMove(e: TouchEvent) {
  if (!isDrawing.value || !ctx.value || e.touches.length === 0) return
  const pos = getPosition(e.touches[0])
  ctx.value.lineTo(pos.x, pos.y)
  ctx.value.stroke()
  hasSignature.value = true
}

function clear() {
  if (!ctx.value || !canvasRef.value) return
  ctx.value.fillStyle = '#FFFFFF'
  ctx.value.fillRect(0, 0, canvasRef.value.width, canvasRef.value.height)
  ctx.value.strokeStyle = lineColor.value
  ctx.value.lineWidth = lineWidth.value
  hasSignature.value = false
  emit('signature', '')
}

function getSignatureData(): string {
  if (!canvasRef.value) return ''
  return canvasRef.value.toDataURL('image/png')
}

function isEmpty(): boolean {
  return !hasSignature.value
}

defineExpose({
  clear,
  getSignatureData,
  isEmpty,
})
</script>

<style scoped>
.signature-pad {
  width: 100%;
}

.pad-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.pad-title {
  font-size: 14px;
  font-weight: 500;
  color: #374151;
}

.canvas-container {
  position: relative;
  border: 2px dashed #D1D5DB;
  border-radius: 12px;
  background: white;
  overflow: hidden;
  transition: border-color 0.2s;
  min-height: 200px;
}

.canvas-container.has-signature {
  border-color: #10B981;
  border-style: solid;
}

canvas {
  display: block;
  width: 100%;
  height: 200px;
  cursor: crosshair;
  touch-action: none;
}

.placeholder-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  color: #9CA3AF;
  font-size: 14px;
  pointer-events: none;
}

.placeholder-icon {
  opacity: 0.5;
}
</style>
