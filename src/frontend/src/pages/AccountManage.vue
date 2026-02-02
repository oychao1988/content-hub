<template>
  <div class="account-manage">
    <page-header title="账号管理" icon="User">
      <!-- 使用权限指令控制按钮显示 - 只有 admin 和 operator 可以创建账号 -->
      <el-button
        v-permission="['account:create']"
        type="primary"
        :icon="Plus"
        @click="handleCreate"
      >
        新建账号
      </el-button>
    </page-header>

    <!-- 搜索表单 -->
    <search-form
      v-model="searchForm"
      @search="handleSearch"
      @reset="handleReset"
    >
      <template #default>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="账号名称">
            <el-input
              v-model="searchForm.name"
              placeholder="请输入账号名称"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="平台">
            <el-select
              v-model="searchForm.platform_id"
              placeholder="请选择平台"
              clearable
            >
              <el-option
                v-for="platform in platforms"
                :key="platform.id"
                :label="platform.name"
                :value="platform.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.status"
              placeholder="请选择状态"
              clearable
            >
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
      selectable
      @selection-change="handleSelectionChange"
      @page-change="handlePageChange"
      @size-change="handleSizeChange"
    >
      <el-table-column prop="name" label="账号名称" min-width="150" />
      <el-table-column prop="platform_name" label="平台" width="120" />
      <el-table-column prop="account_id" label="账号ID" width="150" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'">
            {{ row.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <!-- 查看权限 - 所有角色都可以查看 -->
          <el-button link type="primary" :icon="View" @click="handleView(row)">
            查看
          </el-button>
          <!-- 编辑权限 - admin 和 operator 可以编辑 -->
          <el-button
            v-permission="['account:update']"
            link
            type="primary"
            :icon="Edit"
            @click="handleEdit(row)"
          >
            编辑
          </el-button>
          <!-- 同步权限 - admin 和 operator 可以同步 -->
          <el-button
            v-permission="['account:update']"
            link
            type="primary"
            :icon="Refresh"
            @click="handleSync(row)"
          >
            同步
          </el-button>
          <!-- 删除权限 - 只有 admin 可以删除 -->
          <el-button
            v-role="'admin'"
            link
            type="danger"
            :icon="Delete"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </data-table>

    <!-- 批量操作 -->
    <div v-if="selectedRows.length > 0" class="batch-actions">
      <el-alert
        :title="`已选择 ${selectedRows.length} 项`"
        type="info"
        :closable="false"
      >
        <template #default>
          <el-button type="danger" :icon="Delete" @click="handleBatchDelete">
            批量删除
          </el-button>
        </template>
      </el-alert>
    </div>

    <!-- 表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="120px"
      >
        <el-form-item label="所属客户" prop="customer_id">
          <el-select
            v-model="formData.customer_id"
            placeholder="请选择客户"
            style="width: 100%"
          >
            <el-option
              v-for="customer in customers"
              :key="customer.id"
              :label="customer.name"
              :value="customer.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="显示名称" prop="display_name">
          <el-input v-model="formData.display_name" placeholder="请输入显示名称" />
        </el-form-item>
        <el-form-item label="目录名称" prop="directory_name">
          <el-input v-model="formData.directory_name" placeholder="请输入目录名称（唯一标识）" />
        </el-form-item>
        <el-form-item label="所属平台" prop="platform_id">
          <el-select
            v-model="formData.platform_id"
            placeholder="请选择平台"
            style="width: 100%"
          >
            <el-option
              v-for="platform in platforms"
              :key="platform.id"
              :label="platform.name"
              :value="platform.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="账号描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入账号描述"
          />
        </el-form-item>
        <el-form-item label="垂直领域" prop="niche">
          <el-input v-model="formData.niche" placeholder="请输入垂直领域（可选）" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio label="active">启用</el-radio>
            <el-radio label="inactive">禁用</el-radio>
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
import { accounts as accountsApi, platforms as platformsApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  View,
  Edit,
  Delete,
  Refresh
} from '@element-plus/icons-vue'
import { commonRules } from '../composables/useFormValidation'

// 搜索表单
const searchForm = reactive({
  name: '',
  platform_id: null,
  status: ''
})

// 表格数据
const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const selectedRows = ref([])

// 平台列表
const platforms = ref([])

// 客户列表
const customers = ref([])

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMode = ref('') // create, edit, view
const formRef = ref()
const submitLoading = ref(false)

const formData = reactive({
  customer_id: null,
  display_name: '',
  directory_name: '',
  platform_id: null,
  description: '',
  niche: '',
  status: 'active'
})

const formRules = {
  customer_id: [
    { required: true, message: '请选择客户', trigger: 'change' }
  ],
  display_name: [
    { required: true, message: '请输入显示名称', trigger: 'blur' },
    { minLength: 1, message: '显示名称不能为空', trigger: 'blur' }
  ],
  directory_name: [
    { required: true, message: '请输入目录名称', trigger: 'blur' },
    { minLength: 1, message: '目录名称不能为空', trigger: 'blur' }
  ],
  platform_id: [
    { required: true, message: '请选择平台', trigger: 'change' }
  ]
}

// 获取表格数据
const fetchTableData = async () => {
  try {
    loading.value = true
    const params = {
      ...searchForm,
      page: searchForm.page,
      page_size: searchForm.pageSize
    }
    const response = await accountsApi.getAccounts(params)
    tableData.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取账号列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 获取平台列表
const fetchPlatforms = async () => {
  try {
    const response = await platformsApi.getPlatforms({ page_size: 100 })
    platforms.value = response.items || []
  } catch (error) {
    console.error('获取平台列表失败:', error)
  }
}

// 获取客户列表
const fetchCustomers = async () => {
  try {
    const response = await fetch('http://localhost:8010/api/v1/customers/', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
      }
    })
    const data = await response.json()
    customers.value = data.items || []
  } catch (error) {
    console.error('获取客户列表失败:', error)
  }
}

// 搜索
const handleSearch = () => {
  searchForm.page = 1
  fetchTableData()
}

// 重置
const handleReset = () => {
  searchForm.page = 1
  fetchTableData()
}

// 页码改变
const handlePageChange = (page) => {
  searchForm.page = page
  fetchTableData()
}

// 每页数量改变
const handleSizeChange = (size) => {
  searchForm.pageSize = size
  searchForm.page = 1
  fetchTableData()
}

// 选择改变
const handleSelectionChange = (selection) => {
  selectedRows.value = selection
}

// 新建
const handleCreate = () => {
  dialogMode.value = 'create'
  dialogTitle.value = '新建账号'
  // 设置默认值
  formData.customer_id = 1  // 默认客户ID
  formData.status = 'active'
  dialogVisible.value = true
}

// 查看
const handleView = (row) => {
  dialogMode.value = 'view'
  dialogTitle.value = '查看账号'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑账号'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除账号"${row.name}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await accountsApi.deleteAccount(row.id)
    ElMessage.success('删除成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个账号吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedRows.value.map(row => row.id)
    await accountsApi.batchDeleteAccounts(ids)
    ElMessage.success('删除成功')
    selectedRows.value = []
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
    }
  }
}

// 同步
const handleSync = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要同步账号"${row.name}"的状态吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'info'
    })

    await accountsApi.syncAccount(row.id)
    ElMessage.success('同步成功')
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('同步失败:', error)
    }
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    submitLoading.value = true

    if (dialogMode.value === 'create') {
      await accountsApi.createAccount(formData)
      ElMessage.success('创建成功')
    } else if (dialogMode.value === 'edit') {
      await accountsApi.updateAccount(formData.id, formData)
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

// 关闭对话框
const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.keys(formData).forEach(key => {
    formData[key] = key === 'status' ? 'active' : null
  })
}

onMounted(() => {
  fetchTableData()
  fetchPlatforms()
  fetchCustomers()
})
</script>

<style scoped>
.account-manage {
  padding: 0;
}

.batch-actions {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.batch-actions :deep(.el-alert) {
  padding: 12px 20px;
}
</style>
