<template>
  <el-form
    ref="formRef"
    :model="formData"
    :inline="inline"
    :label-width="labelWidth"
    class="search-form"
  >
    <el-row :gutter="20">
      <slot :formData="formData"></slot>
      <el-col :span="inline ? undefined : 24">
        <el-form-item>
          <el-button type="primary" @click="handleSearch" :icon="Search">
            查询
          </el-button>
          <el-button @click="handleReset" :icon="RefreshLeft">重置</el-button>
          <slot name="actions"></slot>
        </el-form-item>
      </el-col>
    </el-row>
  </el-form>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { Search, RefreshLeft } from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  },
  inline: {
    type: Boolean,
    default: true
  },
  labelWidth: {
    type: String,
    default: '80px'
  }
})

const emit = defineEmits(['update:modelValue', 'search', 'reset'])

const formRef = ref()
const formData = reactive({ ...props.modelValue })

const handleSearch = () => {
  emit('update:modelValue', { ...formData })
  emit('search', formData)
}

const handleReset = () => {
  Object.keys(formData).forEach(key => {
    formData[key] = ''
  })
  emit('update:modelValue', { ...formData })
  emit('reset', formData)
}

const resetForm = () => {
  formRef.value?.resetFields()
}

defineExpose({
  resetForm
})
</script>

<style scoped>
.search-form {
  margin-bottom: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}
</style>
