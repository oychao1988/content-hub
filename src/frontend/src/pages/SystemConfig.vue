<template>
  <div class="system-config">
    <page-header title="系统配置" icon="Setting">
      <el-button type="primary" :icon="Check" @click="handleSave" :loading="loading">
        保存配置
      </el-button>
    </page-header>

    <!-- 快速导航 -->
    <el-card class="nav-card" shadow="hover" style="margin-bottom: 20px">
      <div class="quick-nav">
        <div class="nav-item" @click="goToWritingStyles">
          <el-icon :size="30" color="#409EFF"><EditPen /></el-icon>
          <div class="nav-text">
            <div class="nav-title">写作风格管理</div>
            <div class="nav-desc">管理系统写作风格配置</div>
          </div>
          <el-icon class="nav-arrow"><ArrowRight /></el-icon>
        </div>
        <div class="nav-item" @click="goToContentThemes">
          <el-icon :size="30" color="#67C23A"><CollectionTag /></el-icon>
          <div class="nav-text">
            <div class="nav-title">内容主题管理</div>
            <div class="nav-desc">管理系统内容主题配置</div>
          </div>
          <el-icon class="nav-arrow"><ArrowRight /></el-icon>
        </div>
      </div>
    </el-card>

    <el-card class="config-card" shadow="hover">
      <el-tabs v-model="activeTab" type="border-card">
        <!-- 基本配置 -->
        <el-tab-pane label="基本配置" name="basic">
          <el-form ref="basicFormRef" :model="basicConfig" label-width="150px">
            <el-form-item label="系统名称">
              <el-input v-model="basicConfig.system_name" placeholder="请输入系统名称" />
            </el-form-item>
            <el-form-item label="系统描述">
              <el-input
                v-model="basicConfig.system_description"
                type="textarea"
                :rows="3"
                placeholder="请输入系统描述"
              />
            </el-form-item>
            <el-form-item label="管理员邮箱">
              <el-input v-model="basicConfig.admin_email" placeholder="请输入管理员邮箱" />
            </el-form-item>
            <el-form-item label="默认语言">
              <el-select v-model="basicConfig.default_language" placeholder="请选择默认语言">
                <el-option label="简体中文" value="zh-CN" />
                <el-option label="English" value="en-US" />
              </el-select>
            </el-form-item>
            <el-form-item label="时区">
              <el-select v-model="basicConfig.timezone" placeholder="请选择时区">
                <el-option label="Asia/Shanghai" value="Asia/Shanghai" />
                <el-option label="Asia/Hong_Kong" value="Asia/Hong_Kong" />
                <el-option label="UTC" value="UTC" />
              </el-select>
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 内容生成配置 -->
        <el-tab-pane label="内容生成" name="content">
          <el-form ref="contentFormRef" :model="contentConfig" label-width="150px">
            <el-form-item label="默认文章长度">
              <el-input-number
                v-model="contentConfig.default_article_length"
                :min="100"
                :max="10000"
                :step="100"
              />
            </el-form-item>
            <el-form-item label="生成超时时间(秒)">
              <el-input-number
                v-model="contentConfig.generation_timeout"
                :min="10"
                :max="600"
                :step="10"
              />
            </el-form-item>
            <el-form-item label="启用自动保存">
              <el-switch v-model="contentConfig.auto_save" />
            </el-form-item>
            <el-form-item label="自动保存间隔(秒)">
              <el-input-number
                v-model="contentConfig.auto_save_interval"
                :min="10"
                :max="300"
                :step="10"
                :disabled="!contentConfig.auto_save"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 发布配置 -->
        <el-tab-pane label="发布配置" name="publish">
          <el-form ref="publishFormRef" :model="publishConfig" label-width="150px">
            <el-form-item label="默认发布策略">
              <el-radio-group v-model="publishConfig.default_strategy">
                <el-radio label="immediate">立即发布</el-radio>
                <el-radio label="scheduled">定时发布</el-radio>
                <el-radio label="manual">手动发布</el-radio>
              </el-radio-group>
            </el-form-item>
            <el-form-item label="发布重试次数">
              <el-input-number
                v-model="publishConfig.retry_count"
                :min="0"
                :max="10"
                :step="1"
              />
            </el-form-item>
            <el-form-item label="重试间隔(秒)">
              <el-input-number
                v-model="publishConfig.retry_interval"
                :min="5"
                :max="300"
                :step="5"
              />
            </el-form-item>
            <el-form-item label="启用发布审核">
              <el-switch v-model="publishConfig.enable_review" />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- 定时任务配置 -->
        <el-tab-pane label="定时任务" name="scheduler">
          <el-form ref="schedulerFormRef" :model="schedulerConfig" label-width="150px">
            <el-form-item label="最大并发任务数">
              <el-input-number
                v-model="schedulerConfig.max_concurrent_jobs"
                :min="1"
                :max="20"
                :step="1"
              />
            </el-form-item>
            <el-form-item label="任务超时时间(秒)">
              <el-input-number
                v-model="schedulerConfig.job_timeout"
                :min="60"
                :max="3600"
                :step="60"
              />
            </el-form-item>
            <el-form-item label="启用任务日志">
              <el-switch v-model="schedulerConfig.enable_job_log" />
            </el-form-item>
            <el-form-item label="日志保留天数">
              <el-input-number
                v-model="schedulerConfig.log_retention_days"
                :min="1"
                :max="365"
                :step="1"
                :disabled="!schedulerConfig.enable_job_log"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>

        <!-- API 配置 -->
        <el-tab-pane label="API 配置" name="api">
          <el-form ref="apiFormRef" :model="apiConfig" label-width="150px">
            <el-form-item label="API 速率限制">
              <el-input-number
                v-model="apiConfig.rate_limit"
                :min="10"
                :max="10000"
                :step="10"
              />
              <span style="margin-left: 10px">次/分钟</span>
            </el-form-item>
            <el-form-item label="Token 过期时间(小时)">
              <el-input-number
                v-model="apiConfig.token_expiration"
                :min="1"
                :max="168"
                :step="1"
              />
            </el-form-item>
            <el-form-item label="启用 CORS">
              <el-switch v-model="apiConfig.enable_cors" />
            </el-form-item>
            <el-form-item label="允许的来源">
              <el-input
                v-model="apiConfig.allowed_origins"
                type="textarea"
                :rows="3"
                placeholder="每行一个域名"
                :disabled="!apiConfig.enable_cors"
              />
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { PageHeader } from '../components/common'
import { ElMessage } from 'element-plus'
import { Check, EditPen, CollectionTag, ArrowRight } from '@element-plus/icons-vue'

const router = useRouter()

// 导航到写作风格管理
const goToWritingStyles = () => {
  router.push('/writing-styles')
}

// 导航到内容主题管理
const goToContentThemes = () => {
  router.push('/content-themes')
}

const activeTab = ref('basic')
const loading = ref(false)

const basicConfig = reactive({
  system_name: 'ContentHub',
  system_description: '内容运营管理系统',
  admin_email: 'admin@contethub.com',
  default_language: 'zh-CN',
  timezone: 'Asia/Shanghai'
})

const contentConfig = reactive({
  default_article_length: 2000,
  generation_timeout: 120,
  auto_save: true,
  auto_save_interval: 60
})

const publishConfig = reactive({
  default_strategy: 'immediate',
  retry_count: 3,
  retry_interval: 30,
  enable_review: false
})

const schedulerConfig = reactive({
  max_concurrent_jobs: 5,
  job_timeout: 600,
  enable_job_log: true,
  log_retention_days: 30
})

const apiConfig = reactive({
  rate_limit: 1000,
  token_expiration: 24,
  enable_cors: true,
  allowed_origins: 'http://localhost:5173\nhttp://localhost:3000'
})

const handleSave = async () => {
  try {
    loading.value = true

    // 这里应该调用后端API保存配置
    // 暂时使用 setTimeout 模拟
    await new Promise(resolve => setTimeout(resolve, 1000))

    ElMessage.success('配置保存成功')

    // 保存到 localStorage（临时方案）
    const config = {
      basic: basicConfig,
      content: contentConfig,
      publish: publishConfig,
      scheduler: schedulerConfig,
      api: apiConfig
    }
    localStorage.setItem('system_config', JSON.stringify(config))
  } catch (error) {
    console.error('保存配置失败:', error)
    ElMessage.error('保存配置失败')
  } finally {
    loading.value = false
  }
}

const loadConfig = () => {
  try {
    const savedConfig = localStorage.getItem('system_config')
    if (savedConfig) {
      const config = JSON.parse(savedConfig)
      Object.assign(basicConfig, config.basic || {})
      Object.assign(contentConfig, config.content || {})
      Object.assign(publishConfig, config.publish || {})
      Object.assign(schedulerConfig, config.scheduler || {})
      Object.assign(apiConfig, config.api || {})
    }
  } catch (error) {
    console.error('加载配置失败:', error)
  }
}

onMounted(() => {
  loadConfig()
})
</script>

<style scoped>
.system-config {
  padding: 0;
}

.config-card {
  margin-bottom: 20px;
}

.config-card :deep(.el-tabs__content) {
  padding: 20px;
}

:deep(.el-form-item__content) {
  flex-direction: column;
  align-items: flex-start;
}

:deep(.el-form-item__content > *) {
  width: 100%;
  max-width: 500px;
}

:deep(.el-input-number) {
  width: 100%;
}

/* 快速导航样式 */
.quick-nav {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 20px;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
}

.nav-item:hover {
  border-color: #409eff;
  box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.2);
  transform: translateY(-2px);
}

.nav-text {
  flex: 1;
  margin-left: 15px;
}

.nav-title {
  font-size: 16px;
  font-weight: 500;
  color: #303133;
  margin-bottom: 5px;
}

.nav-desc {
  font-size: 13px;
  color: #909399;
}

.nav-arrow {
  color: #c0c4cc;
  transition: color 0.3s;
}

.nav-item:hover .nav-arrow {
  color: #409eff;
}
</style>
