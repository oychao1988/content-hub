<template>
  <div class="publish-pool">
    <page-header title="发布池" icon="Box">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        添加到发布池
      </el-button>
      <el-button type="success" :icon="Promotion" @click="handleBatchPublish" :disabled="selectedRows.length === 0">
        批量发布 ({{ selectedRows.length }})
      </el-button>
      <el-button type="danger" :icon="Delete" @click="handleClearPublished">
        清空已发布
      </el-button>
    </page-header>

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
              <el-option label="已发布" value="published" />
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
      selectable
      @selection-change="handleSelectionChange"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    >
      <el-table-column prop="content_title" label="内容标题" min-width="200" show-overflow-tooltip />
      <el-table-column prop="platform_name" label="平台" width="120" />
      <el-table-column prop="account_name" label="账号" width="150" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'published' ? 'success' : 'info'">
            {{ row.status === 'published' ? '已发布' : '待发布' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="publish_time" label="计划发布时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="handleView(row)">
            查看
          </el-button>
          <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button
            v-if="row.status === 'pending'"
            link
            type="success"
            :icon="Promotion"
            @click="handlePublish(row)"
          >
            发布
          </el-button>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </data-table>

    <!-- 表单对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="700px" @close="handleDialogClose">
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-form-item label="内容" prop="content_id">
          <el-select v-model="formData.content_id" placeholder="请选择内容" style="width: 100%">
            <el-option
              v-for="content in contents"
              :key="content.id"
              :label="content.title"
              :value="content.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="平台" prop="platform_id">
          <el-select v-model="formData.platform_id" placeholder="请选择平台" style="width: 100%">
            <el-option
              v-for="platform in platforms"
              :key="platform.id"
              :label="platform.name"
              :value="platform.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账号" prop="account_id">
          <el-select v-model="formData.account_id" placeholder="请选择账号" style="width: 100%">
            <el-option
              v-for="account in accounts"
              :key="account.id"
              :label="account.name"
              :value="account.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="发布时间" prop="publish_time">
          <el-date-picker
            v-model="formData.publish_time"
            type="datetime"
            placeholder="选择发布时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-radio-group v-model="formData.priority">
            <el-radio :label="1">低</el-radio>
            <el-radio :label="2">中</el-radio>
            <el-radio :label="3">高</el-radio>
          </el-radio-group>
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
import { publishPool as publishPoolApi, accounts as accountsApi, platforms as platformsApi, content as contentApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete, Promotion } from '@element-plus/icons-vue'

const searchForm = reactive({
  title: '',
  status: '',
  page: 1,
  pageSize: 20
})

const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const selectedRows = ref([])

const contents = ref([])
const platforms = ref([])
const accounts = ref([])

const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMode = ref('')
const formRef = ref()
const submitLoading = ref(false)

const formData = reactive({
  content_id: null,
  platform_id: null,
  account_id: null,
  publish_time: '',
  priority: 2
})

const formRules = {
  content_id: [{ required: true, message: '请选择内容', trigger: 'change' }],
  platform_id: [{ required: true, message: '请选择平台', trigger: 'change' }],
  account_id: [{ required: true, message: '请选择账号', trigger: 'change' }],
  publish_time: [{ required: true, message: '请选择发布时间', trigger: 'change' }]
}

const fetchTableData = async () => {
  try {
    loading.value = true
    const params = {
      ...searchForm,
      page: searchForm.page,
      page_size: searchForm.pageSize
    }
    const response = await publishPoolApi.getPublishPool(params)
    tableData.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取发布池失败:', error)
  } finally {
    loading.value = false
  }
}

const fetchOptions = async () => {
  try {
    const [contentRes, platformRes, accountRes] = await Promise.all([
      contentApi.getContentList({ page_size: 100 }),
      platformsApi.getPlatforms({ page_size: 100 }),
      accountsApi.getAccounts({ page_size: 100 })
    ])
    contents.value = contentRes.items || []
    platforms.value = platformRes.items || []
    accounts.value = accountRes.items || []
  } catch (error) {
    console.error('获取选项失败:', error)
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

const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

const handleCreate = () => {
  dialogMode.value = 'create'
  dialogTitle.value = '添加到发布池'
  dialogVisible.value = true
}

const handleView = (row) => {
  dialogMode.value = 'view'
  dialogTitle.value = '查看发布项'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑发布项'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handlePublish = async (row) => {
  try {
    await ElMessageBox.confirm('确定要立即发布此内容吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })

    await publishPoolApi.batchPublish({ ids: [row.id] })
    ElMessage.success('发布成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('发布失败:', error)
    }
  }
}

const handleBatchPublish = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要发布选中的 ${selectedRows.value.length} 个内容吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    const ids = selectedRows.value.map(row => row.id)
    await publishPoolApi.batchPublish({ ids })
    ElMessage.success('发布成功')
    selectedRows.value = []
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量发布失败:', error)
    }
  }
}

const handleClearPublished = async () => {
  try {
    await ElMessageBox.confirm('确定要清空所有已发布的项吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await publishPoolApi.clearPublished()
    ElMessage.success('清空成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('清空失败:', error)
    }
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除此项吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await publishPoolApi.deletePublishPoolItem(row.id)
    ElMessage.success('删除成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleSubmit = async () => {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    submitLoading.value = true

    if (dialogMode.value === 'create') {
      await publishPoolApi.addToPublishPool(formData)
      ElMessage.success('添加成功')
    } else if (dialogMode.value === 'edit') {
      await publishPoolApi.updatePublishPoolItem(formData.id, formData)
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
    formData[key] = key === 'priority' ? 2 : null
  })
}

onMounted(() => {
  fetchTableData()
  fetchOptions()
})
</script>

<style scoped>
.publish-pool {
  padding: 0;
}
</style>
