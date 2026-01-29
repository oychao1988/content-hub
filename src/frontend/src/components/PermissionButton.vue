<template>
  <el-button
    v-if="hasPermission"
    v-bind="$attrs"
    @click="handleClick"
  >
    <slot></slot>
  </el-button>
</template>

<script setup>
import { computed } from 'vue'
import { useUserStore } from '../stores/modules/user'

const props = defineProps({
  /**
   * 权限标识，支持字符串或数组
   * 例如: 'account:create' 或 ['account:create', 'account:update']
   */
  permission: {
    type: [String, Array],
    required: true
  },
  /**
   * 当所有权限都满足时才显示（默认为 false，表示满足任意一个即可）
   */
  requireAll: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['click'])

const userStore = useUserStore()

const hasPermission = computed(() => {
  const permissions = Array.isArray(props.permission) ? props.permission : [props.permission]

  if (props.requireAll) {
    return userStore.hasAllPermissions(permissions)
  } else {
    return userStore.hasAnyPermission(permissions)
  }
})

const handleClick = (event) => {
  emit('click', event)
}
</script>

<script>
export default {
  name: 'PermissionButton',
  inheritAttrs: true
}
</script>
