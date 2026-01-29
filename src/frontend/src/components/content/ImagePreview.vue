<template>
  <el-dialog
    v-model="visible"
    title="图片预览"
    width="80%"
    :before-close="handleBeforeClose"
    class="image-preview-dialog"
  >
    <div class="image-preview-container">
      <!-- 图片容器 -->
      <div class="image-container">
        <img
          ref="imageRef"
          :src="imageSrc"
          :style="{ transform: imageTransform }"
          class="preview-image"
          @load="handleImageLoad"
          @wheel.prevent="handleWheel"
        />
      </div>

      <!-- 控制工具栏 -->
      <div class="control-toolbar">
        <el-button-group>
          <el-button
            size="small"
            @click="zoomOut"
            :disabled="scale <= 0.5"
            title="缩小"
          >
            <el-icon><ZoomOut /></el-icon>
          </el-button>
          <span class="zoom-level">{{ Math.round(scale * 100) }}%</span>
          <el-button
            size="small"
            @click="zoomIn"
            :disabled="scale >= 3"
            title="放大"
          >
            <el-icon><ZoomIn /></el-icon>
          </el-button>
          <el-button size="small" @click="reset" title="重置">
            <el-icon><Refresh /></el-icon>
          </el-button>
        </el-button-group>

        <el-button-group>
          <el-button size="small" @click="rotateLeft" title="逆时针旋转">
            <el-icon><DArrowLeft /></el-icon>
          </el-button>
          <el-button size="small" @click="rotateRight" title="顺时针旋转">
            <el-icon><DArrowRight /></el-icon>
          </el-button>
        </el-button-group>

        <el-button-group>
          <el-button size="small" @click="flipHorizontal" title="水平翻转">
            <el-icon><SwitchButton /></el-icon>
          </el-button>
          <el-button size="small" @click="flipVertical" title="垂直翻转">
            <el-icon><Top /></el-icon>
          </el-button>
        </el-button-group>

        <el-button-group>
          <el-button size="small" @click="downloadImage" title="下载图片">
            <el-icon><Download /></el-icon>
          </el-button>
          <el-button size="small" @click="copyImage" title="复制图片">
            <el-icon><CopyDocument /></el-icon>
          </el-button>
        </el-button-group>
      </div>

      <!-- 尺寸信息 -->
      <div class="image-info">
        <span>尺寸: {{ naturalWidth }} × {{ naturalHeight }}</span>
        <span v-if="fileSize">大小: {{ formatFileSize(fileSize) }}</span>
      </div>
    </div>
  </el-dialog>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import {
  ZoomOut,
  ZoomIn,
  Refresh,
  DArrowLeft,
  DArrowRight,
  SwitchButton,
  Top,
  Download,
  CopyDocument
} from '@element-plus/icons-vue'

const props = defineProps({
  imageSrc: {
    type: String,
    required: true
  },
  modelValue: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue', 'close'])

const visible = computed({
  get() {
    return props.modelValue
  },
  set(val) {
    emit('update:modelValue', val)
    if (!val) {
      emit('close')
    }
  }
})

// 图片引用
const imageRef = ref(null)

// 变换属性
const scale = ref(1)
const rotation = ref(0)
const flipH = ref(1)
const flipV = ref(1)

// 图片原始尺寸
const naturalWidth = ref(0)
const naturalHeight = ref(0)
const fileSize = ref(null)

// 计算变换样式
const imageTransform = computed(() => {
  return `scale(${scale.value}) rotate(${rotation.value}deg) scaleX(${flipH.value}) scaleY(${flipV.value})`
})

// 处理图片加载
const handleImageLoad = () => {
  if (imageRef.value) {
    naturalWidth.value = imageRef.value.naturalWidth
    naturalHeight.value = imageRef.value.naturalHeight
  }
}

// 缩小
const zoomOut = () => {
  scale.value = Math.max(0.5, scale.value - 0.1)
}

// 放大
const zoomIn = () => {
  scale.value = Math.min(3, scale.value + 0.1)
}

// 重置
const reset = () => {
  scale.value = 1
  rotation.value = 0
  flipH.value = 1
  flipV.value = 1
}

// 逆时针旋转
const rotateLeft = () => {
  rotation.value = (rotation.value - 90 + 360) % 360
}

// 顺时针旋转
const rotateRight = () => {
  rotation.value = (rotation.value + 90) % 360
}

// 水平翻转
const flipHorizontal = () => {
  flipH.value = flipH.value * -1
}

// 垂直翻转
const flipVertical = () => {
  flipV.value = flipV.value * -1
}

// 处理滚轮缩放
const handleWheel = (event) => {
  const delta = event.deltaY > 0 ? -0.1 : 0.1
  const newScale = Math.max(0.5, Math.min(3, scale.value + delta))
  scale.value = newScale
}

// 下载图片
const downloadImage = () => {
  const link = document.createElement('a')
  link.href = props.imageSrc
  link.download = `image_${Date.now()}.${getImageExtension()}`
  link.click()
}

// 复制图片
const copyImage = async () => {
  try {
    const response = await fetch(props.imageSrc)
    const blob = await response.blob()
    await navigator.clipboard.write([
      new ClipboardItem({
        [blob.type]: blob
      })
    ])
    ElMessage.success('图片已复制到剪贴板')
  } catch (error) {
    ElMessage.error('复制图片失败')
  }
}

// 获取图片扩展名
const getImageExtension = () => {
  const extension = props.imageSrc.split('.').pop().split('?')[0]
  return ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(extension.toLowerCase())
    ? extension.toLowerCase()
    : 'png'
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (!bytes) return ''
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 获取图片尺寸和大小
const loadImageInfo = async () => {
  try {
    const response = await fetch(props.imageSrc)
    fileSize.value = response.headers.get('content-length')
    const blob = await response.blob()

    return new Promise((resolve) => {
      const img = new Image()
      img.onload = () => {
        naturalWidth.value = img.naturalWidth
        naturalHeight.value = img.naturalHeight
        resolve()
      }
      img.src = URL.createObjectURL(blob)
    })
  } catch (error) {
    console.error('获取图片信息失败:', error)
  }
}

// 对话框关闭前处理
const handleBeforeClose = () => {
  visible.value = false
}

// 监听图片源变化
const watchImageSrc = () => {
  reset()
  loadImageInfo()
}

onMounted(() => {
  if (visible.value) {
    loadImageInfo()
  }
})

// 监听可见性变化
const unwatchVisible = watch(visible, (newVal) => {
  if (newVal) {
    watchImageSrc()
  }
})

onUnmounted(() => {
  unwatchVisible()
})
</script>

<style scoped>
.image-preview-dialog :deep(.el-dialog__body) {
  padding: 0;
}

.image-preview-container {
  padding: 20px;
  min-height: 400px;
}

.image-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 4px;
  overflow: hidden;
}

.preview-image {
  max-width: 100%;
  max-height: 400px;
  cursor: grab;
  transition: transform 0.2s ease;
}

.preview-image:active {
  cursor: grabbing;
}

.control-toolbar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
  flex-wrap: wrap;
}

.zoom-level {
  min-width: 60px;
  text-align: center;
  font-weight: 600;
  color: #606266;
}

.image-info {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  margin-top: 12px;
  color: #909399;
  font-size: 14px;
}

.image-info span {
  padding: 4px 8px;
  background-color: #f5f7fa;
  border-radius: 3px;
}
</style>
