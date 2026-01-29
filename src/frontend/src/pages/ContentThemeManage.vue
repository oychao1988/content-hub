<template>
  <div class="content-theme-manage">
    <page-header title="内容主题管理" icon="CollectionTag">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建主题
      </el-button>
    </page-header>

    <!-- 搜索表单 -->
    <search-form v-model="searchForm" @search="handleSearch" @reset="handleReset">
      <template #default>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="主题名称">
            <el-input v-model="searchForm.name" placeholder="请输入主题名称" clearable />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="主题代码">
            <el-input v-model="searchForm.code" placeholder="请输入主题代码" clearable />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="类型">
            <el-select v-model="searchForm.type" placeholder="请选择主题类型" clearable>
              <el-option label="技术" value="技术" />
              <el-option label="生活" value="生活" />
              <el-option label="教育" value="教育" />
              <el-option label="娱乐" value="娱乐" />
              <el-option label="商业" value="商业" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="系统级">
            <el-select v-model="searchForm.is_system" placeholder="请选择" clearable>
              <el-option label="系统级" :value="true" />
              <el-option label="自定义" :value="false" />
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
      <el-table-column prop="name" label="主题名称" min-width="180" />
      <el-table-column prop="code" label="主题代码" width="150" />
      <el-table-column prop="type" label="主题类型" width="120">
        <template #default="{ row }">
          <el-tag v-if="row.type" type="primary" size="small">{{ row.type }}</el-tag>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="description" label="描述" min-width="250" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_system ? 'warning' : 'success'" size="small">
            {{ row.is_system ? '系统级' : '自定义' }}
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
          <el-button
            link
            type="danger"
            :icon="Delete"
            @click="handleDelete(row)"
            :disabled="row.is_system"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </data-table>

    <!-- 表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="600px"
      @close="handleDialogClose"
      destroy-on-close
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-form-item label="主题名称" prop="name">
          <el-input v-model="formData.name" placeholder="请输入主题名称" />
        </el-form-item>

        <el-form-item label="主题代码" prop="code">
          <el-input
            v-model="formData.code"
            placeholder="请输入主题代码（英文）"
            :disabled="isEdit"
          />
        </el-form-item>

        <el-form-item label="主题类型" prop="type">
          <el-select v-model="formData.type" placeholder="请选择主题类型" clearable>
            <el-option label="技术" value="技术" />
            <el-option label="生活" value="生活" />
            <el-option label="教育" value="教育" />
            <el-option label="娱乐" value="娱乐" />
            <el-option label="商业" value="商业" />
            <el-option label="其他" value="其他" />
          </el-select>
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="4"
            placeholder="请输入主题描述"
          />
        </el-form-item>

        <el-form-item label="系统级主题" prop="is_system">
          <el-switch v-model="formData.is_system" active-text="是" inactive-text="否" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            系统级主题不允许删除
          </span>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="主题详情" width="600px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="主题名称" :span="2">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="主题代码" :span="2">{{ detailData.code }}</el-descriptions-item>
        <el-descriptions-item label="主题类型">
          <el-tag v-if="detailData.type" type="primary" size="small">{{ detailData.type }}</el-tag>
          <span v-else>-</span>
        </el-descriptions-item>
        <el-descriptions-item label="系统级">
          <el-tag :type="detailData.is_system ? 'warning' : 'success'" size="small">
            {{ detailData.is_system ? '系统级' : '自定义' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ detailData.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ detailData.created_at }}</el-descriptions-item>
        <el-descriptions-item label="更新时间" :span="2">{{ detailData.updated_at }}</el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { PageHeader, SearchForm, DataTable } from '../components/common'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, View, Edit, Delete } from '@element-plus/icons-vue'
import * as config from '../api/modules/config'

// 搜索表单
const searchForm = reactive({
  name: '',
  code: '',
  type: '',
  is_system: null
})

// 表格数据
const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const selectedRows = ref([])

// 分页
const pagination = reactive({
  page: 1,
  pageSize: 10
})

// 对话框
const dialogVisible = ref(false)
const detailVisible = ref(false)
const dialogTitle = computed(() => (isEdit.value ? '编辑内容主题' : '新建内容主题'))
const isEdit = ref(false)
const submitLoading = ref(false)

// 表单
const formRef = ref(null)
const formData = reactive({
  name: '',
  code: '',
  description: '',
  type: '',
  is_system: false
})

// 表单验证规则
const formRules = {
  name: [{ required: true, message: '请输入主题名称', trigger: 'blur' }],
  code: [
    { required: true, message: '请输入主题代码', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '主题代码只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ]
}

// 详情数据
const detailData = ref({})

// 获取列表数据
const fetchData = async () => {
  try {
    loading.value = true
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      ...searchForm
    }

    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })

    const res = await config.getContentThemes(params)
    tableData.value = res.data || res
    // 假设后端不返回总数，使用数据长度
    total.value = res.total || res.length
  } catch (error) {
    console.error('获取内容主题列表失败:', error)
    ElMessage.error('获取内容主题列表失败')
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  pagination.page = 1
  fetchData()
}

// 重置
const handleReset = () => {
  Object.assign(searchForm, {
    name: '',
    code: '',
    type: '',
    is_system: null
  })
  pagination.page = 1
  fetchData()
}

// 分页变化
const handlePageChange = (page) => {
  pagination.page = page
  fetchData()
}

const handleSizeChange = (size) => {
  pagination.pageSize = size
  pagination.page = 1
  fetchData()
}

// 选择变化
const handleSelectionChange = (rows) => {
  selectedRows.value = rows
}

// 新建
const handleCreate = () => {
  isEdit.value = false
  dialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  isEdit.value = true
  Object.assign(formData, {
    name: row.name,
    code: row.code,
    description: row.description,
    type: row.type,
    is_system: row.is_system
  })
  dialogVisible.value = true
}

// 查看
const handleView = async (row) => {
  try {
    const res = await config.getContentTheme(row.id)
    detailData.value = res.data || res
    detailVisible.value = true
  } catch (error) {
    console.error('获取内容主题详情失败:', error)
    ElMessage.error('获取内容主题详情失败')
  }
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除内容主题"${row.name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await config.deleteContentTheme(row.id)
        ElMessage.success('删除成功')
        fetchData()
      } catch (error) {
        console.error('删除内容主题失败:', error)
        ElMessage.error(error.response?.data?.detail || '删除内容主题失败')
      }
    })
    .catch(() => {})
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true

    if (isEdit.value) {
      // 编辑
      const id = tableData.value.find((item) => item.code === formData.code)?.id
      if (id) {
        await config.updateContentTheme(id, formData)
        ElMessage.success('更新成功')
      }
    } else {
      // 新建
      await config.createContentTheme(formData)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    fetchData()
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
      ElMessage.error(error.response?.data?.detail || '提交失败')
    }
  } finally {
    submitLoading.value = false
  }
}

// 对话框关闭
const handleDialogClose = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    name: '',
    code: '',
    description: '',
    type: '',
    is_system: false
  })
}

// 初始化
fetchData()
</script>

<style scoped>
.content-theme-manage {
  padding: 0;
}
</style>
