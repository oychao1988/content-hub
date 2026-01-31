<template>
  <div class="content-manage">
    <page-header title="内容管理" icon="Document">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建内容
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
          <el-form-item label="标题">
            <el-input
              v-model="searchForm.title"
              placeholder="请输入标题"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="状态">
            <el-select
              v-model="searchForm.status"
              placeholder="请选择状态"
              clearable
            >
              <el-option label="草稿" value="draft" />
              <el-option label="待审核" value="pending" />
              <el-option label="已发布" value="published" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="内容类型">
            <el-select
              v-model="searchForm.content_type"
              placeholder="请选择类型"
              clearable
            >
              <el-option label="文章" value="article" />
              <el-option label="图文" value="image" />
              <el-option label="视频" value="video" />
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
      <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip />
      <el-table-column label="类型" width="100">
        <template #default="{ row }">
          <el-tag>{{ getContentTypeText(row.content_type) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.publish_status)">
            {{ getStatusText(row.publish_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="350" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="handleView(row)">
            查看
          </el-button>
          <el-button link type="primary" :icon="Edit" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button link type="info" :icon="Document" @click="handlePreview(row)">
            预览
          </el-button>
          <el-button link type="success" :icon="MagicStick" @click="handleGenerate(row)">
            生成
          </el-button>
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)">
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
          <el-button type="primary" :icon="Promotion" @click="handleBatchPublish">
            添加到发布池
          </el-button>
        </template>
      </el-alert>
    </div>

    <!-- 表单对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="800px"
      @close="handleDialogClose"
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="100px"
      >
        <el-form-item label="标题" prop="title">
          <el-input v-model="formData.title" placeholder="请输入标题" />
        </el-form-item>
        <el-form-item label="内容类型" prop="content_type">
          <el-select
            v-model="formData.content_type"
            placeholder="请选择内容类型"
            style="width: 100%"
          >
            <el-option label="文章" value="article" />
            <el-option label="图文" value="image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-form-item>
        <el-form-item label="内容" prop="content">
          <el-input
            v-model="formData.content"
            type="textarea"
            :rows="10"
            placeholder="请输入内容"
          />
        </el-form-item>
        <el-form-item label="摘要" prop="summary">
          <el-input
            v-model="formData.summary"
            type="textarea"
            :rows="3"
            placeholder="请输入摘要"
          />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="formData.status">
            <el-radio label="draft">草稿</el-radio>
            <el-radio label="pending">待审核</el-radio>
            <el-radio label="published">已发布</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="标签" prop="tags">
          <el-input v-model="formData.tags" placeholder="请输入标签，多个标签用逗号分隔" />
        </el-form-item>
        <el-form-item label="封面图" prop="cover_image">
          <el-input v-model="formData.cover_image" placeholder="请输入封面图URL" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
          确定
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      :title="previewTitle"
      width="900px"
      class="preview-dialog"
    >
      <div class="preview-content">
        <MarkdownPreview
          :content="previewContent"
          @image-click="handleImageClick"
        />
      </div>
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 图片预览 -->
    <ImagePreview
      v-model="imagePreviewVisible"
      :image-src="previewImageSrc"
    />

    <!-- AI 生成对话框 -->
    <el-dialog
      v-model="generateDialogVisible"
      title="AI 生成内容"
      width="600px"
    >
      <el-form
        ref="generateFormRef"
        :model="generateForm"
        :rules="generateRules"
        label-width="100px"
      >
        <el-form-item label="主题" prop="topic">
          <el-input v-model="generateForm.topic" placeholder="请输入要生成的主题" />
        </el-form-item>
        <el-form-item label="关键词" prop="keywords">
          <el-input v-model="generateForm.keywords" placeholder="请输入关键词，多个关键词用逗号分隔" />
        </el-form-item>
        <el-form-item label="内容类型" prop="content_type">
          <el-select
            v-model="generateForm.content_type"
            placeholder="请选择内容类型"
            style="width: 100%"
          >
            <el-option label="文章" value="article" />
            <el-option label="图文" value="image" />
            <el-option label="视频" value="video" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="generateDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="generateLoading" @click="handleGenerateSubmit">
          {{ generateLoading ? '生成中...' : '开始生成' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { PageHeader, DataTable, SearchForm } from '../components/common'
import { content as contentApi } from '../api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  View,
  Edit,
  Delete,
  MagicStick,
  Promotion,
  Document
} from '@element-plus/icons-vue'
import MarkdownPreview from '../components/content/MarkdownPreview.vue'
import ImagePreview from '../components/content/ImagePreview.vue'

// 搜索表单
const searchForm = reactive({
  title: '',
  status: '',
  content_type: '',
  page: 1,
  pageSize: 20
})

// 表格数据
const tableData = ref([])
const loading = ref(false)
const total = ref(0)
const selectedRows = ref([])

// 对话框
const dialogVisible = ref(false)
const dialogTitle = ref('')
const dialogMode = ref('')
const formRef = ref()
const submitLoading = ref(false)

const formData = reactive({
  title: '',
  content_type: 'article',
  content: '',
  summary: '',
  status: 'draft',
  tags: '',
  cover_image: ''
})

const formRules = {
  title: [{ required: true, message: '请输入标题', trigger: 'blur' }],
  content_type: [{ required: true, message: '请选择内容类型', trigger: 'change' }],
  content: [{ required: true, message: '请输入内容', trigger: 'blur' }]
}

// 预览对话框
const previewDialogVisible = ref(false)
const previewTitle = ref('')
const previewContent = ref('')

// 图片预览
const imagePreviewVisible = ref(false)
const previewImageSrc = ref('')

// 处理图片点击
const handleImageClick = (src) => {
  previewImageSrc.value = src
  imagePreviewVisible.value = true
}

// AI 生成对话框
const generateDialogVisible = ref(false)
const generateFormRef = ref()
const generateLoading = ref(false)

const generateForm = reactive({
  topic: '',
  keywords: '',
  content_type: 'article'
})

const generateRules = {
  topic: [{ required: true, message: '请输入主题', trigger: 'blur' }],
  content_type: [{ required: true, message: '请选择内容类型', trigger: 'change' }]
}

// 获取内容类型文本
const getContentTypeText = (type) => {
  const typeMap = {
    article: '文章',
    image: '图文',
    video: '视频'
  }
  return typeMap[type] || type
}

// 获取状态类型
const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    pending: 'warning',
    published: 'success'
  }
  return typeMap[status] || 'info'
}

// 获取状态文本
const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    pending: '待审核',
    published: '已发布'
  }
  return textMap[status] || status
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
    const response = await contentApi.getContentList(params)
    tableData.value = response.items || []
    total.value = response.total || 0
  } catch (error) {
    console.error('获取内容列表失败:', error)
  } finally {
    loading.value = false
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
  dialogTitle.value = '新建内容'
  dialogVisible.value = true
}

// 查看
const handleView = (row) => {
  dialogMode.value = 'view'
  dialogTitle.value = '查看内容'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 预览
const handlePreview = (row) => {
  previewTitle.value = row.title
  previewContent.value = row.content
  previewDialogVisible.value = true
}

// 编辑
const handleEdit = (row) => {
  dialogMode.value = 'edit'
  dialogTitle.value = '编辑内容'
  Object.assign(formData, row)
  dialogVisible.value = true
}

// 删除
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除内容"${row.title}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await contentApi.deleteContent(row.id)
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
      `确定要删除选中的 ${selectedRows.value.length} 个内容吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const ids = selectedRows.value.map(row => row.id)
    await contentApi.batchDeleteContent(ids)
    ElMessage.success('删除成功')
    selectedRows.value = []
    fetchTableData()
  } catch (error) {
    if (error !== 'cancel') {
      console.error('批量删除失败:', error)
    }
  }
}

// 批量添加到发布池
const handleBatchPublish = () => {
  ElMessage.info('功能开发中')
}

// AI 生成
const handleGenerate = (row) => {
  if (row) {
    generateForm.topic = row.title
  }
  generateDialogVisible.value = true
}

// 提交生成
const handleGenerateSubmit = async () => {
  try {
    const valid = await generateFormRef.value.validate()
    if (!valid) return

    generateLoading.value = true

    const response = await contentApi.generateContent({
      topic: generateForm.topic,
      keywords: generateForm.keywords.split(',').map(k => k.trim()),
      content_type: generateForm.content_type
    })

    ElMessage.success('生成成功')

    // 将生成的内容填充到表单
    Object.assign(formData, response)
    generateDialogVisible.value = false
    dialogMode.value = 'create'
    dialogTitle.value = '新建内容'
    dialogVisible.value = true
  } catch (error) {
    console.error('生成失败:', error)
  } finally {
    generateLoading.value = false
  }
}

// 提交表单
const handleSubmit = async () => {
  try {
    const valid = await formRef.value.validate()
    if (!valid) return

    submitLoading.value = true

    const data = {
      ...formData,
      tags: formData.tags.split(',').map(t => t.trim()).filter(t => t)
    }

    if (dialogMode.value === 'create') {
      await contentApi.createContent(data)
      ElMessage.success('创建成功')
    } else if (dialogMode.value === 'edit') {
      await contentApi.updateContent(formData.id, data)
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
    formData[key] = key === 'content_type' || key === 'status' ? 'draft' : ''
  })
}

onMounted(() => {
  fetchTableData()
})
</script>

<style scoped>
.content-manage {
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

.preview-dialog {
  .el-dialog__body {
    padding: 20px;
    max-height: 70vh;
    overflow-y: auto;
  }
}

.preview-content {
  width: 100%;
}
</style>
