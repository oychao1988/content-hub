import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import ContentManage from '@/pages/ContentManage.vue'
import { content as contentApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// Mock API modules
vi.mock('@/api', () => ({
  content: {
    getContentList: vi.fn(),
    createContent: vi.fn(),
    updateContent: vi.fn(),
    deleteContent: vi.fn(),
    batchDeleteContent: vi.fn(),
    generateContent: vi.fn(),
    getContentStats: vi.fn()
  }
}))

// Mock Element Plus components
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn()
    }
  }
})

describe('ContentManage.vue', () => {
  let wrapper
  let pinia

  const mockContentList = {
    items: [
      {
        id: 1,
        title: 'Test Content 1',
        content_type: 'article',
        publish_status: 'draft',
        content: 'Test content',
        summary: 'Test summary',
        tags: 'test',
        cover_image: '',
        created_at: '2024-01-01 00:00:00'
      },
      {
        id: 2,
        title: 'Test Content 2',
        content_type: 'image',
        publish_status: 'published',
        content: 'Test image content',
        summary: 'Test image summary',
        tags: 'image,test',
        cover_image: 'https://example.com/image.jpg',
        created_at: '2024-01-02 00:00:00'
      }
    ],
    total: 2
  }

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    // Mock API responses
    contentApi.getContentList.mockResolvedValue(mockContentList)
    contentApi.createContent.mockResolvedValue({ id: 1 })
    contentApi.updateContent.mockResolvedValue({ id: 1 })
    contentApi.deleteContent.mockResolvedValue({})
    contentApi.batchDeleteContent.mockResolvedValue({})
    contentApi.generateContent.mockResolvedValue({
      title: 'Generated Content',
      content: 'AI generated content',
      summary: 'AI summary',
      content_type: 'article'
    })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  describe('页面加载和数据获取', () => {
    it('应该正确渲染页面', async () => {
      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.content-manage').exists()).toBe(true)
    })

    it('应该在挂载时获取内容列表', async () => {
      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      // 等待异步操作完成
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(contentApi.getContentList).toHaveBeenCalledWith({
        title: '',
        status: '',
        content_type: '',
        page: 1,
        page_size: 20
      })
    })

    it('应该正确处理获取数据失败', async () => {
      contentApi.getContentList.mockRejectedValue(new Error('API Error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(consoleSpy).toHaveBeenCalledWith('获取内容列表失败:', expect.any(Error))
      consoleSpy.mockRestore()
    })
  })

  describe('搜索和过滤功能', () => {
    beforeEach(async () => {
      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确执行搜索', async () => {
      wrapper.vm.searchForm.title = 'Test Content'
      await wrapper.vm.handleSearch()

      expect(contentApi.getContentList).toHaveBeenCalledWith({
        title: 'Test Content',
        status: '',
        content_type: '',
        page: 1,
        page_size: 20
      })
    })

    it('应该正确执行重置', async () => {
      wrapper.vm.searchForm.title = 'Test'
      wrapper.vm.searchForm.status = 'draft'
      wrapper.vm.searchForm.content_type = 'article'

      await wrapper.vm.handleReset()

      expect(wrapper.vm.searchForm.page).toBe(1)
      expect(contentApi.getContentList).toHaveBeenCalled()
    })
  })

  describe('分页导航', () => {
    beforeEach(async () => {
      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确处理页码变化', async () => {
      await wrapper.vm.handlePageChange(2)

      expect(wrapper.vm.searchForm.page).toBe(2)
      expect(contentApi.getContentList).toHaveBeenCalledWith({
        title: '',
        status: '',
        content_type: '',
        page: 2,
        page_size: 20
      })
    })

    it('应该正确处理每页数量变化', async () => {
      await wrapper.vm.handleSizeChange(50)

      expect(wrapper.vm.searchForm.pageSize).toBe(50)
      expect(wrapper.vm.searchForm.page).toBe(1)
      expect(contentApi.getContentList).toHaveBeenCalledWith({
        title: '',
        status: '',
        content_type: '',
        page: 1,
        page_size: 50
      })
    })
  })

  describe('操作按钮', () => {
    beforeEach(async () => {
      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该打开新建对话框', async () => {
      await wrapper.vm.handleCreate()

      expect(wrapper.vm.dialogMode).toBe('create')
      expect(wrapper.vm.dialogTitle).toBe('新建内容')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该打开查看对话框', async () => {
      const row = mockContentList.items[0]
      await wrapper.vm.handleView(row)

      expect(wrapper.vm.dialogMode).toBe('view')
      expect(wrapper.vm.dialogTitle).toBe('查看内容')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该打开编辑对话框', async () => {
      const row = mockContentList.items[0]
      await wrapper.vm.handleEdit(row)

      expect(wrapper.vm.dialogMode).toBe('edit')
      expect(wrapper.vm.dialogTitle).toBe('编辑内容')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该正确预览内容', async () => {
      const row = mockContentList.items[0]
      await wrapper.vm.handlePreview(row)

      expect(wrapper.vm.previewTitle).toBe(row.title)
      expect(wrapper.vm.previewContent).toBe(row.content)
      expect(wrapper.vm.previewDialogVisible).toBe(true)
    })

    it('应该正确删除内容', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      const row = mockContentList.items[0]
      await wrapper.vm.handleDelete(row)

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        `确定要删除内容"${row.title}"吗？`,
        '提示',
        expect.any(Object)
      )
      expect(contentApi.deleteContent).toHaveBeenCalledWith(row.id)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('应该正确处理批量删除', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper.vm.selectedRows = mockContentList.items
      await wrapper.vm.handleBatchDelete()

      expect(ElMessageBox.confirm).toHaveBeenCalled()
      expect(contentApi.batchDeleteContent).toHaveBeenCalledWith([1, 2])
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
      expect(wrapper.vm.selectedRows).toEqual([])
    })

    it('应该正确打开生成对话框', async () => {
      const row = mockContentList.items[0]
      await wrapper.vm.handleGenerate(row)

      expect(wrapper.vm.generateForm.topic).toBe(row.title)
      expect(wrapper.vm.generateDialogVisible).toBe(true)
    })

    it('应该正确生成内容', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper.vm.generateForm.topic = 'Test Topic'
      wrapper.vm.generateForm.keywords = 'test,ai'
      wrapper.vm.generateForm.content_type = 'article'

      // Mock form validation
      wrapper.vm.generateFormRef = {
        validate: vi.fn().mockResolvedValue(true)
      }

      await wrapper.vm.handleGenerateSubmit()

      expect(contentApi.generateContent).toHaveBeenCalledWith({
        topic: 'Test Topic',
        keywords: ['test', 'ai'],
        content_type: 'article'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('生成成功')
    })
  })

  describe('表单提交', () => {
    beforeEach(async () => {
      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确创建内容', async () => {
      wrapper.vm.dialogMode = 'create'
      wrapper.vm.formData = {
        title: 'New Content',
        content_type: 'article',
        content: 'New content',
        summary: 'New summary',
        status: 'draft',
        tags: 'test',
        cover_image: ''
      }

      // Mock form validation
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }

      await wrapper.vm.handleSubmit()

      expect(contentApi.createContent).toHaveBeenCalledWith({
        title: 'New Content',
        content_type: 'article',
        content: 'New content',
        summary: 'New summary',
        status: 'draft',
        tags: ['test'],
        cover_image: ''
      })
      expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    })

    it('应该正确更新内容', async () => {
      wrapper.vm.dialogMode = 'edit'
      wrapper.vm.formData = {
        id: 1,
        title: 'Updated Content',
        content_type: 'article',
        content: 'Updated content',
        summary: 'Updated summary',
        status: 'published',
        tags: 'test',
        cover_image: ''
      }

      // Mock form validation
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }

      await wrapper.vm.handleSubmit()

      expect(contentApi.updateContent).toHaveBeenCalledWith(1, {
        title: 'Updated Content',
        content_type: 'article',
        content: 'Updated content',
        summary: 'Updated summary',
        status: 'published',
        tags: ['test'],
        cover_image: ''
      })
      expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
    })
  })

  describe('选择功能', () => {
    beforeEach(async () => {
      wrapper = mount(ContentManage, {
        global: {
          plugins: [pinia],
          stubs: {
            PageHeader: true,
            DataTable: true,
            SearchForm: true,
            'el-button': true,
            'el-table-column': true,
            'el-tag': true,
            'el-dialog': true,
            'el-form': true,
            'el-form-item': true,
            'el-input': true,
            'el-select': true,
            'el-option': true,
            'el-radio-group': true,
            'el-radio': true,
            'el-col': true,
            'el-alert': true,
            MarkdownPreview: true,
            ImagePreview: true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确处理选择变化', () => {
      const selection = [mockContentList.items[0]]
      wrapper.vm.handleSelectionChange(selection)

      expect(wrapper.vm.selectedRows).toEqual(selection)
    })
  })
})
