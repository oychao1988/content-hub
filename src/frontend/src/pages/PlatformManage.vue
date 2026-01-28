<template>
  <div class="platform-manage">
    <page-header title="平台管理" icon="Platform">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建平台
      </el-button>
    </page-header>

    <!-- 搜索表单 -->
    <search-form v-model="searchForm" @search="handleSearch" @reset="handleReset">
      <template #default>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="平台名称">
            <el-input v-model="searchForm.name" placeholder="请输入平台名称" clearable />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="平台类型">
            <el-select v-model="searchForm.platform_type" placeholder="请选择类型" clearable>
              <el-option label="微信公众号" value="wechat_mp" />
              <el-option label="微博" value="weibo" />
              <el-option label="抖音" value="douyin" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="状态">
            <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
              <el-option label="启用" value="active" />
              <el-option label="禁用" value="inactive" />
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
      <el-table-column prop="name" label="平台名称" min-width="180" />
      <el-table-column label="平台类型" width="150">
        <template #default="{ row }">
          <el-tag>{{ getPlatformTypeText(row.platform_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="app_id" label="App ID" width="200" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'info'">
            {{ row.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="handleView(row)">
            查看
          </el-button>
          <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">
            编辑
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
        <el-form-item label="平台名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入平台名称" />
        </el-form-item>
        <el-form-item label="平台类型" prop="platform_type">
          <el-select v-model="formData.platform_type" placeholder="请选择平台类型" style="width: 100%">
            <el-option label="微信公众号" value="wechat_mp" />
            <el-option label="微博" value="weibo" />
            <el-option label="抖音" value="douyin" />
          </el-select>
        </el-form-item>
        <el-form-item label="App ID" prop="app_id">
          <el-input v-model="formData.app_id" placeholder="请输入App ID" />
        </el-form-item>
        <el-form-item label="App Secret" prop="app_secret">
          <el-input v-model="formData.app_secret" type="password" placeholder="请输入App Secret" show-password />
        </el-form-item>
        <el-form-item label="回调地址" prop="callback_url">
          <el-input v-model="formData.callback_url" placeholder="请输入回调地址" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="配置" prop="config">
          <el-input
            v-model="formData.config"
            type="textarea"
            :rows="4"
            placeholder="请输入其他配置（JSON格式）"
          />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="formData.remark" type="textarea" :rows="3" placeholder="请输入备注" />
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
import { platforms as platformsApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete } from '@element-plus/icons-vue'

const searchForm = reactive({
  name: '',
  platform_type: '',
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
  platform_type: '',
  app_id: '',
  app_secret: '',
  callback_url: '',
  status: 'active',
  config: '',
  remark: ''
})

const formRules = {
  name: [{ required: true, message: '请输入平台名称', trigger: 'blur' }],
  platform_type: [{ required: true, message: '请选择平台类型', trigger: 'change' }],
  app_id: [{ required: true, message: '请输入App ID', trigger: 'blur' }],
  app_secret: [{ required: true, message: '请输入App Secret', trigger: 'blur' }]
}

const getPlatformTypeText = (type) => {
  const typeMap = {
    wechat_mp: '微信公众号',
    weibo: '微博',
    douyin: '抖音'
  }
  return typeMap[type] || type
}

const fetchTableData = async () => {
  try {
    loading.value = true
    const params = {
      ...searchForm,
      page: searchForm.page,
      page_size: searchForm.pageSize
    }
    const response = await platformsApi.getPlatforms(params)
    tableData.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取平台列表失败:', error)
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
  dialogTitle.value = '新建平台'
  dialogVisible.value = true
}

const handleView = (row) => {
  dialogMode.value = 'view'
  dialogTitle.value = '查看平台'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleEdit = (row) => {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑平台'
  Object.assign(formData, row)
  dialogVisible.value = true
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除平台"${row.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await platformsApi.deletePlatform(row.id)
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
      await platformsApi.createPlatform(formData)
      ElMessage.success('创建成功')
    } else if (dialogMode.value === 'edit') {
      await platformsApi.updatePlatform(formData.id, formData)
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
    formData[key] = key === 'status' ? 'active' : ''
  })
}

onMounted(() => {
  fetchTableData()
})
</script>

<style scoped>
.platform-manage {
  padding: 0;
}
</style>
