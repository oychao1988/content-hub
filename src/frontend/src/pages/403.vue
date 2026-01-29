<template>
  <div class="forbidden-page">
    <div class="forbidden-container">
      <div class="error-code">403</div>
      <div class="error-title">访问被拒绝</div>
      <div class="error-desc">
        抱歉，您没有权限访问此页面。如果您认为这是一个错误，请联系系统管理员。
      </div>
      <div class="error-actions">
        <el-button type="primary" @click="goBack">返回上一页</el-button>
        <el-button @click="goHome">回到首页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

const goBack = () => {
  router.back()
}

const goHome = () => {
  router.push({ name: 'Dashboard' })
}
</script>

<style scoped>
.forbidden-page {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.forbidden-container {
  text-align: center;
  padding: 40px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 500px;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: #f56c6c;
  line-height: 1;
  margin-bottom: 20px;
}

.error-title {
  font-size: 28px;
  font-weight: 600;
  color: #303133;
  margin-bottom: 16px;
}

.error-desc {
  font-size: 16px;
  color: #606266;
  margin-bottom: 32px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
}
</style>
