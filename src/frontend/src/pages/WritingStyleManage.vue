<template>
  <div class="writing-style-manage">
    <page-header title="写作风格管理" icon="EditPen">
      <el-button type="primary" :icon="Plus" @click="handleCreate">
        新建风格
      </el-button>
    </page-header>

    <!-- 搜索表单 -->
    <search-form v-model="searchForm" @search="handleSearch" @reset="handleReset">
      <template #default>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="风格名称">
            <el-input v-model="searchForm.name" placeholder="请输入风格名称" clearable />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="风格代码">
            <el-input v-model="searchForm.code" placeholder="请输入风格代码" clearable />
          </el-form-item>
        </el-col>
        <el-col :xs="24" :sm="12" :md="6">
          <el-form-item label="类型">
            <el-select v-model="searchForm.is_system" placeholder="请选择类型" clearable>
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
      <el-table-column prop="name" label="风格名称" min-width="150" />
      <el-table-column prop="code" label="风格代码" width="150" />
      <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
      <el-table-column prop="tone" label="语气" width="100" />
      <el-table-column prop="persona" label="人设" width="120" show-overflow-tooltip />
      <el-table-column label="字数范围" width="130">
        <template #default="{ row }">
          {{ row.min_words }} - {{ row.max_words }}
        </template>
      </el-table-column>
      <el-table-column prop="emoji_usage" label="表情使用" width="100" />
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
      width="700px"
      @close="handleDialogClose"
      destroy-on-close
    >
      <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="风格名称" prop="name">
              <el-input v-model="formData.name" placeholder="请输入风格名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="风格代码" prop="code">
              <el-input
                v-model="formData.code"
                placeholder="请输入风格代码（英文）"
                :disabled="isEdit"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="请输入风格描述"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="语气" prop="tone">
              <el-select v-model="formData.tone" placeholder="请选择语气">
                <el-option label="专业" value="专业" />
                <el-option label="轻松" value="轻松" />
                <el-option label="幽默" value="幽默" />
                <el-option label="正式" value="正式" />
                <el-option label="亲切" value="亲切" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="表情使用" prop="emoji_usage">
              <el-select v-model="formData.emoji_usage" placeholder="请选择表情使用频率">
                <el-option label="不使用" value="不使用" />
                <el-option label="适度" value="适度" />
                <el-option label="频繁" value="频繁" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="人设" prop="persona">
          <el-input
            v-model="formData.persona"
            type="textarea"
            :rows="2"
            placeholder="请输入人设描述"
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="最小字数" prop="min_words">
              <el-input-number
                v-model="formData.min_words"
                :min="100"
                :max="10000"
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最大字数" prop="max_words">
              <el-input-number
                v-model="formData.max_words"
                :min="100"
                :max="10000"
                :step="100"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="禁用词" prop="forbidden_words">
          <el-select
            v-model="formData.forbidden_words"
            multiple
            filterable
            allow-create
            placeholder="请输入禁用词，按回车添加"
            style="width: 100%"
          >
          </el-select>
        </el-form-item>

        <el-form-item label="系统级风格" prop="is_system">
          <el-switch v-model="formData.is_system" active-text="是" inactive-text="否" />
          <span style="margin-left: 10px; color: #909399; font-size: 12px">
            系统级风格不允许删除
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
    <el-dialog v-model="detailVisible" title="风格详情" width="700px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="风格名称">{{ detailData.name }}</el-descriptions-item>
        <el-descriptions-item label="风格代码">{{ detailData.code }}</el-descriptions-item>
        <el-descriptions-item label="语气">{{ detailData.tone }}</el-descriptions-item>
        <el-descriptions-item label="表情使用">{{ detailData.emoji_usage }}</el-descriptions-item>
        <el-descriptions-item label="字数范围">
          {{ detailData.min_words }} - {{ detailData.max_words }}
        </el-descriptions-item>
        <el-descriptions-item label="类型">
          <el-tag :type="detailData.is_system ? 'warning' : 'success'" size="small">
            {{ detailData.is_system ? '系统级' : '自定义' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="人设" :span="2">{{ detailData.persona || '-' }}</el-descriptions-item>
        <el-descriptions-item label="描述" :span="2">
          {{ detailData.description || '-' }}
        </el-descriptions-item>
        <el-descriptions-item label="禁用词" :span="2">
          <el-tag
            v-for="(word, index) in detailData.forbidden_words"
            :key="index"
            size="small"
            style="margin-right: 5px"
          >
            {{ word }}
          </el-tag>
          <span v-if="!detailData.forbidden_words || detailData.forbidden_words.length === 0">
            -
          </span>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间" :span="2">{{ detailData.created_at }}</el-descriptions-item>
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
import { commonRules } from '../composables/useFormValidation'

// 搜索表单
const searchForm = reactive({
  name: '',
  code: '',
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
const dialogTitle = computed(() => (isEdit.value ? '编辑写作风格' : '新建写作风格'))
const isEdit = ref(false)
const submitLoading = ref(false)

// 表单
const formRef = ref(null)
const formData = reactive({
  name: '',
  code: '',
  description: '',
  tone: '专业',
  persona: '',
  min_words: 800,
  max_words: 1500,
  emoji_usage: '适度',
  forbidden_words: [],
  is_system: false
})

// 表单验证规则
const formRules = {
  name: commonRules.writingStyleName(),
  code: commonRules.writingStyleCode(),
  tone: commonRules.writingStyleTone(),
  min_words: commonRules.writingStyleWordRange().min_words,
  max_words: commonRules.writingStyleWordRange().max_words
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

    const res = await config.getWritingStyles(params)
    tableData.value = res.data || res
    // 假设后端不返回总数，使用数据长度
    total.value = res.total || res.length
  } catch (error) {
    console.error('获取写作风格列表失败:', error)
    ElMessage.error('获取写作风格列表失败')
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
    tone: row.tone,
    persona: row.persona,
    min_words: row.min_words,
    max_words: row.max_words,
    emoji_usage: row.emoji_usage,
    forbidden_words: row.forbidden_words || [],
    is_system: row.is_system
  })
  dialogVisible.value = true
}

// 查看
const handleView = async (row) => {
  try {
    const res = await config.getWritingStyle(row.id)
    detailData.value = res.data || res
    detailVisible.value = true
  } catch (error) {
    console.error('获取写作风格详情失败:', error)
    ElMessage.error('获取写作风格详情失败')
  }
}

// 删除
const handleDelete = (row) => {
  ElMessageBox.confirm(`确定要删除写作风格"${row.name}"吗？`, '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  })
    .then(async () => {
      try {
        await config.deleteWritingStyle(row.id)
        ElMessage.success('删除成功')
        fetchData()
      } catch (error) {
        console.error('删除写作风格失败:', error)
        ElMessage.error(error.response?.data?.detail || '删除写作风格失败')
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
        await config.updateWritingStyle(id, formData)
        ElMessage.success('更新成功')
      }
    } else {
      // 新建
      await config.createWritingStyle(formData)
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
    tone: '专业',
    persona: '',
    min_words: 800,
    max_words: 1500,
    emoji_usage: '适度',
    forbidden_words: [],
    is_system: false
  })
}

// 初始化
fetchData()
</script>

<style scoped>
.writing-style-manage {
  padding: 0;
}
</style>
