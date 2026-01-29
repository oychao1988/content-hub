<template>
  <div class="content-detail">
    <page-header :title="content.title" icon="Document">
      <el-button type="primary" :icon="Edit" @click="handleEdit">
        编辑
      </el-button>
      <el-button :icon="Share" @click="handleShare">
        分享
      </el-button>
    </page-header>

    <el-row :gutter="20">
      <el-col :span="16">
        <!-- 内容主体 -->
        <el-card class="content-card">
          <template #header>
            <div class="card-header">
              <span>内容详情</span>
              <el-tag :type="getStatusType(content.status)">
                {{ getStatusText(content.status) }}
              </el-tag>
            </div>
          </template>

          <div class="content-info">
            <div class="content-meta">
              <el-tag>{{ getContentTypeText(content.content_type) }}</el-tag>
              <span class="create-time">{{ formatDate(content.created_at) }}</span>
            </div>

            <div v-if="content.cover_image" class="cover-image">
              <img :src="content.cover_image" alt="封面图" />
            </div>

            <div class="content-body">
              <MarkdownPreview
                :content="content.content"
                @image-click="handleImageClick"
              />
            </div>

            <div v-if="content.summary" class="content-summary">
              <h3>摘要</h3>
              <p>{{ content.summary }}</p>
            </div>

            <div v-if="content.tags" class="content-tags">
              <h3>标签</h3>
              <el-tag
                v-for="tag in content.tags.split(',').map(t => t.trim()).filter(t => t)"
                :key="tag"
                type="info"
              >
                {{ tag }}
              </el-tag>
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8">
        <!-- 侧边栏 -->
        <el-card class="sidebar-card">
          <template #header>
            <span>内容信息</span>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="内容ID">
              {{ content.id || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="内容类型">
              {{ getContentTypeText(content.content_type) }}
            </el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(content.status)">
                {{ getStatusText(content.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="创建时间">
              {{ formatDate(content.created_at) }}
            </el-descriptions-item>
            <el-descriptions-item label="更新时间">
              {{ formatDate(content.updated_at) }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="sidebar-card" style="margin-top: 20px">
          <template #header>
            <span>操作</span>
          </template>

          <div class="action-buttons">
            <el-button type="primary" :icon="Edit" @click="handleEdit">
              编辑内容
            </el-button>
            <el-button :icon="View" @click="handlePreview">
              预览内容
            </el-button>
            <el-button :icon="Promotion" @click="handleAddToPublishPool">
              添加到发布池
            </el-button>
            <el-button type="danger" :icon="Delete" @click="handleDelete">
              删除内容
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title="编辑内容"
      width="80%"
      class="edit-dialog"
    >
      <ContentEditor
        v-model="editFormData.content"
        @submit="handleEditSubmit"
      />
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="editLoading" @click="handleEditSubmit">
          {{ editLoading ? '保存中...' : '保存' }}
        </el-button>
      </template>
    </el-dialog>

    <!-- 预览对话框 -->
    <el-dialog
      v-model="previewDialogVisible"
      :title="content.title"
      width="900px"
    >
      <MarkdownPreview
        :content="content.content"
        @image-click="handleImageClick"
      />
      <template #footer>
        <el-button @click="previewDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 图片预览 -->
    <ImagePreview
      v-model="imagePreviewVisible"
      :image-src="previewImageSrc"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { PageHeader } from '../components/common'
import { content as contentApi } from '../api'
import MarkdownPreview from '../components/content/MarkdownPreview.vue'
import ContentEditor from '../components/content/ContentEditor.vue'
import ImagePreview from '../components/content/ImagePreview.vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Edit,
  Share,
  View,
  Promotion,
  Delete
} from '@element-plus/icons-vue'

// Route
const route = useRoute()
const router = useRouter()

// Content data
const content = reactive({
  id: '',
  title: '',
  content_type: 'article',
  content: '',
  summary: '',
  status: 'draft',
  tags: '',
  cover_image: '',
  created_at: '',
  updated_at: ''
})

// Loading
const loading = ref(false)

// Edit dialog
const editDialogVisible = ref(false)
const editPreviewMode = ref(false)
const editLoading = ref(false)

const editFormData = reactive({
  content: ''
})

// Preview dialog
const previewDialogVisible = ref(false)

// Image preview
const imagePreviewVisible = ref(false)
const previewImageSrc = ref('')

// Handle image click
const handleImageClick = (src) => {
  previewImageSrc.value = src
  imagePreviewVisible.value = true
}

// Get content type text
const getContentTypeText = (type) => {
  const typeMap = {
    article: '文章',
    image: '图文',
    video: '视频'
  }
  return typeMap[type] || type
}

// Get status type
const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    pending: 'warning',
    published: 'success'
  }
  return typeMap[status] || 'info'
}

// Get status text
const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    pending: '待审核',
    published: '已发布'
  }
  return textMap[status] || status
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString()
}

// Fetch content detail
const fetchContentDetail = async () => {
  try {
    loading.value = true
    const id = route.params.id
    const response = await contentApi.getContent(id)
    Object.assign(content, response)
  } catch (error) {
    console.error('获取内容详情失败:', error)
    ElMessage.error('获取内容详情失败')
  } finally {
    loading.value = false
  }
}

// Handle edit
const handleEdit = () => {
  editFormData.content = content.content
  editDialogVisible.value = true
}

// Handle content input
const handleContentInput = (value) => {
  editFormData.content = value
}

// Handle edit submit
const handleEditSubmit = async () => {
  try {
    editLoading.value = true
    await contentApi.updateContent(content.id, {
      ...content,
      content: editFormData.content
    })
    ElMessage.success('更新成功')
    content.content = editFormData.content
    editDialogVisible.value = false
  } catch (error) {
    console.error('更新失败:', error)
    ElMessage.error('更新失败')
  } finally {
    editLoading.value = false
  }
}

// Handle preview
const handlePreview = () => {
  previewDialogVisible.value = true
}

// Handle share
const handleShare = () => {
  ElMessage.info('分享功能开发中')
}

// Handle add to publish pool
const handleAddToPublishPool = () => {
  ElMessage.info('添加到发布池功能开发中')
}

// Handle delete
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm(`确定要删除内容"${content.title}"吗？`, '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    await contentApi.deleteContent(content.id)
    ElMessage.success('删除成功')
    router.push('/content')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

onMounted(() => {
  fetchContentDetail()
})
</script>

<style scoped>
.content-detail {
  padding: 0;
}

.content-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.content-info {
  padding: 16px 0;
}

.content-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.create-time {
  color: #909399;
  font-size: 14px;
}

.cover-image {
  width: 100%;
  margin-bottom: 20px;
  border-radius: 8px;
  overflow: hidden;
}

.cover-image img {
  width: 100%;
  height: auto;
  display: block;
}

.content-body {
  margin-bottom: 20px;
}

.content-summary {
  margin-bottom: 20px;
  padding: 16px;
  background-color: #f8f9fa;
  border-radius: 8px;
}

.content-summary h3 {
  margin-bottom: 8px;
  font-size: 16px;
  color: #303133;
}

.content-summary p {
  color: #606266;
  line-height: 1.6;
}

.content-tags {
  margin-bottom: 20px;
}

.content-tags h3 {
  margin-bottom: 8px;
  font-size: 16px;
  color: #303133;
}

.sidebar-card {
  margin-bottom: 20px;
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-buttons .el-button {
  width: 100%;
}
</style>
