<template>
  <div class="dashboard">
    <page-header title="仪表盘" icon="Dashboard" />

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :xs="24" :sm="12" :md="6" v-for="stat in stats" :key="stat.title">
        <el-card class="stat-card" shadow="hover">
          <div class="stat-content">
            <div class="stat-icon" :style="{ background: stat.color }">
              <el-icon :size="32">
                <component :is="stat.icon" />
              </el-icon>
            </div>
            <div class="stat-info">
              <p class="stat-title">{{ stat.title }}</p>
              <h3 class="stat-value">{{ stat.value }}</h3>
              <p class="stat-change" :class="stat.trend">
                <el-icon>
                  <component :is="stat.trendIcon" />
                </el-icon>
                {{ stat.change }}
              </p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="charts-row">
      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span>内容趋势</span>
          </template>
          <div class="chart-container">
            <div v-loading="contentTrendLoading" class="chart-placeholder">
              <el-icon :size="60" color="#dcdfe6">
                <TrendCharts />
              </el-icon>
              <p>内容趋势图表</p>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :xs="24" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <span>发布统计</span>
          </template>
          <div class="chart-container">
            <div v-loading="publishTrendLoading" class="chart-placeholder">
              <el-icon :size="60" color="#dcdfe6">
                <PieChart />
              </el-icon>
              <p>发布统计图表</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 最近活动 -->
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card class="activity-card" shadow="hover">
          <template #header>
            <div class="activity-header">
              <span>最近活动</span>
              <el-button link @click="refreshActivities">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <el-timeline v-loading="activitiesLoading">
            <el-timeline-item
              v-for="activity in activities"
              :key="activity.id"
              :timestamp="activity.timestamp"
              placement="top"
            >
              <el-card>
                <h4>{{ activity.title }}</h4>
                <p>{{ activity.description }}</p>
              </el-card>
            </el-timeline-item>
            <el-timeline-item v-if="activities.length === 0" placement="top">
              <el-empty description="暂无活动记录" />
            </el-timeline-item>
          </el-timeline>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { PageHeader } from '../components/common'
import { dashboard as dashboardApi } from '../api'
import { ElMessage } from 'element-plus'
import {
  User,
  Document,
  Promotion,
  Timer,
  ArrowUp,
  ArrowDown,
  TrendCharts,
  PieChart,
  Refresh
} from '@element-plus/icons-vue'

// 统计数据
const stats = ref([
  {
    title: '总账号数',
    value: '0',
    change: '0%',
    trend: 'up',
    trendIcon: ArrowUp,
    color: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    icon: User
  },
  {
    title: '内容总数',
    value: '0',
    change: '0%',
    trend: 'up',
    trendIcon: ArrowUp,
    color: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    icon: Document
  },
  {
    title: '发布总数',
    value: '0',
    change: '0%',
    trend: 'down',
    trendIcon: ArrowDown,
    color: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    icon: Promotion
  },
  {
    title: '定时任务',
    value: '0',
    change: '0%',
    trend: 'up',
    trendIcon: ArrowUp,
    color: 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    icon: Timer
  }
])

// 最近活动
const activities = ref([])
const contentTrendLoading = ref(false)
const publishTrendLoading = ref(false)
const activitiesLoading = ref(false)

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await dashboardApi.getDashboardStats()
    stats.value[0].value = response.account_count || 0
    stats.value[1].value = response.content_count || 0
    stats.value[2].value = response.published_count || 0
    stats.value[3].value = response.scheduled_task_count || 0
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 获取最近活动
const fetchActivities = async () => {
  try {
    activitiesLoading.value = true
    const response = await dashboardApi.getRecentActivities({ limit: 5 })
    activities.value = response.items || []
  } catch (error) {
    console.error('获取最近活动失败:', error)
    activities.value = []
  } finally {
    activitiesLoading.value = false
  }
}

// 刷新活动
const refreshActivities = () => {
  fetchActivities()
  ElMessage.success('刷新成功')
}

onMounted(() => {
  fetchStats()
  fetchActivities()
})
</script>

<style scoped>
.dashboard {
  padding: 0;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  margin-bottom: 20px;
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.stat-info {
  flex: 1;
}

.stat-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #909399;
}

.stat-value {
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #303133;
}

.stat-change {
  margin: 0;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-change.up {
  color: #67c23a;
}

.stat-change.down {
  color: #f56c6c;
}

.charts-row {
  margin-bottom: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.chart-container {
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  color: #909399;
}

.activity-card {
  margin-bottom: 20px;
}

.activity-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.activity-header :deep(.el-card__header) {
  padding: 12px 20px;
}

:deep(.el-timeline-item__timestamp) {
  color: #909399;
}

:deep(.el-timeline-item__wrapper) > .el-card {
  margin-bottom: 0;
}

:deep(.el-timeline-item__wrapper) > .el-card h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #303133;
}

:deep(.el-timeline-item__wrapper) > .el-card p {
  margin: 0;
  font-size: 12px;
  color: #606266;
}
</style>
