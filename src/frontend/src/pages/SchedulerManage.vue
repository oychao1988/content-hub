<template>
  <div class="scheduler-manage">
    <page-header title="定时任务" icon="Timer">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建任务
      </el-button>
    </page-header>

    <!-- 搜索表单 -->
    <search-form v-model="searchForm" @search="handleSearch" @reset="handleReset">
      <template #default>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="任务名称">
            <el-input v-model="searchForm.name" placeholder="请输入任务名称" clearable />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="任务类型">
            <el-select v-model="searchForm.job_type" placeholder="请选择类型" clearable>
              <el-option label="内容生成" value="content_generation" />
              <el-option label="定时发布" value="scheduled_publish" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
              <el-option label="运行中" value="running" />
              <el-option label="暂停" value="paused" />
              <el-option label="已停止" value="stopped" />
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
      <el-table-column prop="name" label="任务名称" min-width="180" />
      <el-table-column label="任务类型" width="120">
        <template #default="{ row }">
          <el-tag>{{ getJobTypeText(row.job_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="cron_expression" label="Cron表达式" width="150" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="next_run_time" label="下次运行" width="180" />
      <el-table-column prop="last_run_time" label="上次运行" width="180" />
      <el-table-column label="操作" width="300" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="handleView(row)">
            查看
          </el-button>
          <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button
            v-if="row.status === 'running'"
            link
            type="warning"
            :icon="VideoPause"
            @click="handlePause(row)"
          >
            暂停
          </el-button>
          <el-button
            v-if="row.status === 'paused'"
            link
            type="success"
            :icon="VideoPlay"
            @click="handleResume(row)"
          >
            恢复
          </el-button>
          <el-button
            v-if="row.status !== 'stopped'"
            link
            type="danger"
            :icon="Delete"
            @click="handleStop(row)"
          >
            停止
          </el-button>
          <el-button link type="info" :icon="Clock" @click="handleExecute(row)">
            立即执行
          </el-button>
        </template>
      </el-table-column>
    </data-table>

    <!-- 表单对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" @close="handleDialogClose">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入任务名称" />
        </el-form-item>
        <el-form-item label="任务类型" prop="job_type">
          <el-select v-model="formData.job_type" placeholder="请选择任务类型" style="width: 100%">
            <el-option label="内容生成" value="content_generation" />
            <el-option label="定时发布" value="scheduled_publish" />
          </el-select>
        </el-form-item>
        <el-form-item label="Cron表达式" prop="cron_expression">
          <el-input v-model="formData.cron_expression" placeholder="例如: 0 0 * * * (每天0点)" />
          <div class="form-tip">格式: 分 时 日 月 周</div>
        </el-form-item>
        <el-form-item label="任务参数" prop="job_params">
          <el-input
            v-model="formData.job_params"
            type="textarea"
            :rows="4"
            placeholder="请输入任务参数（JSON格式）"
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input v-model="formData.description" type="textarea" :rows="3" placeholder="请输入描述" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { PageHeader, DataTable, SearchForm } from '../components/common'
import { scheduler as schedulerApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  View,
  Edit,
  Delete,
  VideoPause,
  VideoPlay,
  Clock
} from '@element-plus/icons-vue'

const searchForm = reactive({
  name: '',
  job_type: '',
  status: '',
  page: 1,
  pageSize: 20
})

const tableData = ref([])
const loading = ref(false)
const total = ref(0)

const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMode = ref('')
const formRef = ref()
const submitLoading = ref(false)

const formData = reactive({
  name: '',
  job_type: '',
  cron_expression: '',
  job_params: '',
  description: ''
})

const formRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  job_type: [{ required: true, message: '请选择任务类型', trigger: 'change' }],
  cron_expression: [{ required: true, message: '请输入Cron表达式', trigger: 'blur' }],
  job_params: [{ required: true, message: '请输入任务参数', trigger: 'blur' }]
}

const getJobTypeText = (type) => {
  const typeMap = {
    content_generation: '内容生成',
    scheduled_publish: '定时发布'
  }
  return typeMap[type] || type
}

const getStatusType = (status) => {
  const typeMap = {
    running: 'success',
    paused: 'warning',
    stopped: 'info'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    running: '运行中',
    paused: '暂停',
    stopped: '已停止'
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
    const response = await schedulerApi.getSchedulerTasks(params)
    tableData.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取定时任务失败:', error)
  } finally {
    loading.value = false
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

const handleCreate = () => {
  dialogMode.value = 'create'
  dialogTitle.value = '新建任务'
  dialogVisible.value = true
}

const handleView = (row) => {
  dialogMode.value = 'view'
  dialogTitle.value = '查看任务'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑任务'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handlePause = async (row) => {
  try {
    await schedulerApi.pauseTask(row.id)
    ElMessage.success('暂停成功')
    fetchTableData()
  } catch (error) {
    console.error('暂停失败:', error)
  }
}

const handleResume = async (row) => {
  try {
    await schedulerApi.resumeTask(row.id)
    ElMessage.success('恢复成功')
    fetchTableData()
  } catch (error) {
    console.error('恢复失败:', error)
  }
}

const handleStop = async (row) => {
  try {
    await ElMessageBox.confirm('确定要停止此任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await schedulerApi.stopTask(row.id)
    ElMessage.success('停止成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('停止失败:', error)
    }
  }
}

const handleExecute = async (row) => {
  try {
    await ElMessageBox.confirm('确定要立即执行此任务吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })

    await schedulerApi.executeTask(row.id)
    ElMessage.success('执行成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('执行失败:', error)
    }
  }
}

const handleSubmit = async () => {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    submitLoading.value = true

    if (dialogMode.value === 'create') {
      await schedulerApi.createSchedulerTask(formData)
      ElMessage.success('创建成功')
    } else if (dialogMode.value === 'edit') {
      await schedulerApi.updateSchedulerTask(formData.id, formData)
      ElMessage.success('更新成功')
    }

    dialogVisible.value = false
    fetchTableData()
  } catch (error) {
    console.error('提交失败:', error)
  } finally {
    submitLoading.value = false
  }
}

const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.keys(formData).forEach(key => {
    formData[key] = ''
  })
}

onMounted(() => {
  fetchTableData()
})
</script>

<style scoped>
.scheduler-manage {
  padding: 0;
}

.form-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}
</style>
