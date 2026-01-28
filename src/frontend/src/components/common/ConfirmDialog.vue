<template>
  <el-dialog
    v-model="visible"
    :title="title"
    :width="width"
    :before-close="handleClose"
    destroy-on-close
  >
    <div class="confirm-content">
      <el-icon v-if="type === 'warning'" class="confirm-icon warning">
        <WarningFilled />
      </el-icon>
      <el-icon v-else-if="type === 'success'" class="confirm-icon success">
        <CircleCheckFilled />
      </el-icon>
      <el-icon v-else-if="type === 'info'" class="confirm-icon info">
        <InfoFilled />
      </el-icon>
      <el-icon v-else class="confirm-icon danger">
        <CircleCloseFilled />
      </el-icon>
      <p class="confirm-message">{{ message }}</p>
      <p v-if="content" class="confirm-detail">{{ content }}</p>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleClose">{{ cancelText }}</el-button>
        <el-button :type="confirmType" @click="handleConfirm">
          {{ confirmText }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'
import {
  WarningFilled,
  CircleCheckFilled,
  InfoFilled,
  CircleCloseFilled
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  title: {
    type: String,
    default: '确认'
  },
  message: {
    type: String,
    required: true
  },
  content: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'warning',
    validator: (value) => ['warning', 'success', 'info', 'danger'].includes(value)
  },
  confirmText: {
    type: String,
    default: '确认'
  },
  cancelText: {
    type: String,
    default: '取消'
  },
  width: {
    type: String,
    default: '420px'
  }
})

const emit = defineEmits(['update:modelValue', 'confirm', 'cancel'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const confirmType = computed(() => {
  const typeMap = {
    warning: 'warning',
    success: 'success',
    info: 'info',
    danger: 'danger'
  }
  return typeMap[props.type]
})

const handleConfirm = () => {
  emit('confirm')
  visible.value = false
}

const handleClose = () => {
  emit('cancel')
  visible.value = false
}
</script>

<style scoped>
.confirm-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.confirm-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.confirm-icon.warning {
  color: #e6a23c;
}

.confirm-icon.success {
  color: #67c23a;
}

.confirm-icon.info {
  color: #909399;
}

.confirm-icon.danger {
  color: #f56c6c;
}

.confirm-message {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin: 0 0 8px 0;
}

.confirm-detail {
  font-size: 14px;
  color: #606266;
  margin: 0;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}
</style>
