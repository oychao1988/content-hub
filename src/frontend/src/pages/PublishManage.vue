<template>
  <div class="publish-manage">
    <page-header title="发布管理" icon="Promotion" />

    <!-- 搜索表单 -->
    <search-form v-model="searchForm" @search="handleSearch" @reset="handleReset">
      <template #default>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="内容标题">
            <el-input v-model="searchForm.title" placeholder="请输入标题" clearable />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="发布状态">
            <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
              <el-option label="待发布" value="pending" />
              <el-option label="发布中" value="publishing" />
              <el-option label="已发布" value="published" />
              <el-option label="发布失败" value="failed" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="平台">
            <el-select v-model="searchForm.platform_id" placeholder="请选择平台" clearable>
              <el-option
                v-for="platform in platforms"
                :key="platform.id"
                :label="platform.name"
                :value="platform.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
      </template>
    </search-form>

    <!-- 数据表格 -->
    <data-table
      :data="tableData"
      :loading="loading"
      :total="total"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    >
      <el-table-column prop="content_title" label="内容标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="platform_name" label="平台" width="120" />
      <el-table-column prop="account_name" label="账号" width="150" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="published_at" label="发布时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="handleView(row)">
            查看
          </el-button>
          <el-button
            v-if="row.status === 'failed'"
            link
            type="warning"
            :icon="RefreshRight"
            @click="handleRetry(row)"
          >
            重试
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            link
            type="danger"
            :icon="Close"
            @click="handleCancel(row)"
          >
            取消
          </el-button>
        </template>
      </el-table-column>
    </data-table>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { PageHeader, DataTable, SearchForm } from '../components/common'
import { publisher as publisherApi, platforms as platformsApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { View, RefreshRight, Close } from '@element-plus/icons-vue'

const searchForm = reactive({
  title: '',
  status: '',
  platform_id: null,
  page: 1,
  pageSize: 20
})

const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const platforms = ref([])

const getStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    publishing: 'warning',
    published: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    pending: '待发布',
    publishing: '发布中',
    published: '已发布',
    failed: '发布失败'
  }
  return textMap[status] || status
}

const fetchTableData = async () => {
  try {
    loading.value = true
    const params = {
      ...searchForm,
      page: searchForm.page,
      page_size: searchForm.pageSize
    }
    const response = await publisherApi.getPublishRecords(params)
    tableData.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取发布记录失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchPlatforms = async () => {
  try {
    const response = await platformsApi.getPlatforms({ page_size: 100 })
    platforms.value = response.items || []
  } catch (error) {
    console.error('获取平台列表失败:', error)
  }
}

const handleSearch = () => {
  searchForm.page = 1
  fetchTableData()
}

const handleReset = () => {
  searchForm.page = 1
  fetchTableData()
}

const handlePageChange = (page) => {
  searchForm.page = page
  fetchTableData()
}

const handleSizeChange = (size) => {
  searchForm.pageSize = size
  searchForm.page = 1
  fetchTableData()
}

const handleView = (row) => {
  ElMessageBox.alert(`
    <p><strong>内容标题:</strong> ${row.content_title}</p>
    <p><strong>平台:</strong> ${row.platform_name}</p>
    <p><strong>账号:</strong> ${row.account_name}</p>
    <p><strong>状态:</strong> ${getStatusText(row.status)}</p>
    <p><strong>发布时间:</strong> ${row.published_at || '未发布'}</p>
    ${row.error_message ? `<p><strong>错误信息:</strong> ${row.error_message}</p>` : ''}
  `, '发布详情', {
    dangerouslyUseHTMLString: true,
    confirmButtonText: '关闭'
  })
}

const handleRetry = async (row) => {
  try {
    await ElMessageBox.confirm('确定要重试发布吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await publisherApi.retryPublish(row.id)
    ElMessage.success('重试成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('重试失败:', error)
    }
  }
}

const handleCancel = async (row) => {
  try {
    await ElMessageBox.confirm('确定要取消发布吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await publisherApi.cancelPublish(row.id)
    ElMessage.success('取消成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('取消失败:', error)
    }
  }
}

onMounted(() => {
  fetchTableData()
  fetchPlatforms()
})
</script>

<style scoped>
.publish-manage {
  padding: 0;
}
</style>
