<template>
  <div class="page-header">
    <div class="page-header-left">
      <el-icon v-if="icon" class="page-header-icon">
        <component :is="icon" />
      </el-icon>
      <h2 class="page-header-title">{{ title }}</h2>
    </div>
    <div class="page-header-right">
      <slot></slot>
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  icon: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 20px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.page-header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.page-header-icon {
  font-size: 24px;
  color: #409eff;
}

.page-header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
}

.page-header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
