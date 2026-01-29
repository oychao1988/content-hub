<template>
  <div class="cache-manager">
    <el-card header="缓存管理">
      <!-- 缓存统计 -->
      <div class="stats-section">
        <h3>缓存统计</h3>
        <el-row :gutter="20">
          <el-col :span="6">
            <el-statistic title="缓存命中" :value="backendStats.hits" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="缓存未命中" :value="backendStats.misses" />
          </el-col>
          <el-col :span="6">
            <el-statistic title="缓存大小" :value="backendStats.size" />
          </el-col>
          <el-col :span="6">
            <el-statistic
              title="命中率"
              :value="backendStats.hit_rate"
              suffix="%"
              :value-style="{ color: hitRateColor }"
            />
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <!-- 前端缓存统计 -->
      <div class="frontend-stats-section">
        <h3>前端缓存统计</h3>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-statistic title="内存缓存大小" :value="frontendCache.size" />
          </el-col>
          <el-col :span="8">
            <el-statistic
              title="内存缓存命中率"
              :value="frontendCache.hitRate"
              suffix="%"
            />
          </el-col>
          <el-col :span="8">
            <el-statistic
              title="LocalStorage"
              :value="frontendCache.storageSize?.localStorage?.sizeKB || 0"
              suffix="KB"
            />
          </el-col>
        </el-row>
      </div>

      <el-divider />

      <!-- 操作按钮 -->
      <div class="actions-section">
        <h3>缓存操作</h3>
        <el-space>
          <el-button type="primary" @click="refreshStats">
            <el-icon><Refresh /></el-icon>
            刷新统计
          </el-button>
          <el-button type="warning" @click="resetStats">
            <el-icon><RefreshLeft /></el-icon>
            重置统计
          </el-button>
          <el-button type="danger" @click="clearAllCache">
            <el-icon><Delete /></el-icon>
            清空所有缓存
          </el-button>
          <el-button type="info" @click="cleanupExpired">
            <el-icon><Cleaning /></el-icon>
            清理过期缓存
          </el-button>
        </el-space>
      </div>

      <el-divider />

      <!-- 缓存配置信息 -->
      <div class="config-section">
        <h3>缓存配置</h3>
        <el-descriptions :column="2" border>
          <el-descriptions-item label="写作风格">1 小时</el-descriptions-item>
          <el-descriptions-item label="内容主题">1 小时</el-descriptions-item>
          <el-descriptions-item label="平台配置">30 分钟</el-descriptions-item>
          <el-descriptions-item label="账号列表">5 分钟</el-descriptions-item>
          <el-descriptions-item label="用户权限">30 分钟</el-descriptions-item>
          <el-descriptions-item label="内容列表">2 分钟</el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider />

      <!-- 测试区域 -->
      <div class="test-section">
        <h3>缓存测试</h3>
        <el-space>
          <el-button @click="testAccountCache">测试账号缓存</el-button>
          <el-button @click="testConfigCache">测试配置缓存</el-button>
          <el-button @click="testPlatformCache">测试平台缓存</el-button>
        </el-space>
        <div v-if="testResult" class="test-result">
          <el-alert :type="testResult.type" :title="testResult.message" :closable="false" />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, RefreshLeft, Delete, Cleaning } from '@element-plus/icons-vue'
import * as dashboardApi from '../api/modules/dashboard'
import * as accountsApi from '../api/modules/accounts'
import * as configApi from '../api/modules/config'
import * as platformsApi from '../api/modules/platforms'
import { useCacheStore } from '../stores/modules/cache'
import Cache from '../utils/cache'

// 状态
const backendStats = ref({
  hits: 0,
  misses: 0,
  sets: 0,
  deletes: 0,
  size: 0,
  hit_rate: 0
})

const frontendCache = ref({
  size: 0,
  hitRate: '0.00',
  storageSize: null
})

const testResult = ref(null)

// 计算属性
const hitRateColor = computed(() => {
  const rate = backendStats.value.hit_rate
  if (rate >= 60) return '#67C23A' // 绿色
  if (rate >= 30) return '#E6A23C' // 橙色
  return '#F56C6C' // 红色
})

// 方法
const refreshStats = async () => {
  try {
    // 获取后端缓存统计
    const backendData = await dashboardApi.getCacheStats()
    backendStats.value = backendData

    // 获取前端缓存统计
    const cacheStore = useCacheStore()
    frontendCache.value = {
      size: cacheStore.size,
      hitRate: cacheStore.hitRate,
      storageSize: Cache.getSize()
    }

    ElMessage.success('缓存统计已刷新')
  } catch (error) {
    ElMessage.error('刷新缓存统计失败')
    console.error(error)
  }
}

const resetStats = async () => {
  try {
    await dashboardApi.resetCacheStats()

    // 重置前端统计
    const cacheStore = useCacheStore()
    cacheStore.resetStats()

    await refreshStats()
    ElMessage.success('缓存统计已重置')
  } catch (error) {
    ElMessage.error('重置缓存统计失败')
    console.error(error)
  }
}

const clearAllCache = async () => {
  try {
    await dashboardApi.clearCache()

    // 清空前端缓存
    const cacheStore = useCacheStore()
    cacheStore.cache.clear()
    Cache.clear()

    await refreshStats()
    ElMessage.success('所有缓存已清空')
  } catch (error) {
    ElMessage.error('清空缓存失败')
    console.error(error)
  }
}

const cleanupExpired = async () => {
  try {
    await dashboardApi.cleanupCache()

    // 清理前端缓存
    const cacheStore = useCacheStore()
    cacheStore.cleanup()
    Cache.cleanup()

    await refreshStats()
    ElMessage.success('过期缓存已清理')
  } catch (error) {
    ElMessage.error('清理缓存失败')
    console.error(error)
  }
}

const testAccountCache = async () => {
  try {
    testResult.value = null
    const startTime = Date.now()

    // 第一次请求（缓存未命中）
    await accountsApi.getAccounts()
    const firstTime = Date.now() - startTime

    // 第二次请求（应该命中缓存）
    const startTime2 = Date.now()
    await accountsApi.getAccounts()
    const secondTime = Date.now() - startTime2

    testResult.value = {
      type: 'success',
      message: `账号缓存测试完成 - 第一次请求: ${firstTime}ms, 第二次请求: ${secondTime}ms (应该更快)`
    }
  } catch (error) {
    testResult.value = {
      type: 'error',
      message: `账号缓存测试失败: ${error.message}`
    }
  }
}

const testConfigCache = async () => {
  try {
    testResult.value = null
    const startTime = Date.now()

    // 第一次请求（缓存未命中）
    await configApi.getWritingStyles()
    const firstTime = Date.now() - startTime

    // 第二次请求（应该命中缓存）
    const startTime2 = Date.now()
    await configApi.getWritingStyles()
    const secondTime = Date.now() - startTime2

    testResult.value = {
      type: 'success',
      message: `写作风格缓存测试完成 - 第一次请求: ${firstTime}ms, 第二次请求: ${secondTime}ms (应该更快)`
    }
  } catch (error) {
    testResult.value = {
      type: 'error',
      message: `写作风格缓存测试失败: ${error.message}`
    }
  }
}

const testPlatformCache = async () => {
  try {
    testResult.value = null
    const startTime = Date.now()

    // 第一次请求（缓存未命中）
    await platformsApi.getPlatforms()
    const firstTime = Date.now() - startTime

    // 第二次请求（应该命中缓存）
    const startTime2 = Date.now()
    await platformsApi.getPlatforms()
    const secondTime = Date.now() - startTime2

    testResult.value = {
      type: 'success',
      message: `平台缓存测试完成 - 第一次请求: ${firstTime}ms, 第二次请求: ${secondTime}ms (应该更快)`
    }
  } catch (error) {
    testResult.value = {
      type: 'error',
      message: `平台缓存测试失败: ${error.message}`
    }
  }
}

// 生命周期
onMounted(() => {
  refreshStats()
})
</script>

<style scoped>
.cache-manager {
  padding: 20px;
}

.stats-section,
.frontend-stats-section,
.actions-section,
.config-section,
.test-section {
  margin-bottom: 20px;
}

.stats-section h3,
.frontend-stats-section h3,
.actions-section h3,
.config-section h3,
.test-section h3 {
  margin-bottom: 15px;
  font-size: 16px;
  font-weight: 600;
}

.test-result {
  margin-top: 15px;
}
</style>
