import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import PublishPool from '@/pages/PublishPool.vue'
import { publishPool, accounts, platforms, content } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// Mock API modules
vi.mock('@/api', () => ({
  publishPool: {
    getPublishPool: vi.fn(),
    addToPublishPool: vi.fn(),
    updatePublishPoolItem: vi.fn(),
    deletePublishPoolItem: vi.fn(),
    batchPublish: vi.fn(),
    clearPublished: vi.fn()
  },
  accounts: {
    getAccounts: vi.fn()
  },
  platforms: {
    getPlatforms: vi.fn()
  },
  content: {
    getContentList: vi.fn()
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

describe('PublishPool.vue', () => {
  let wrapper
  let pinia

  const mockPublishPoolList = {
    items: [
      {
        id: 1,
        content_id: 1,
        content_title: 'Test Content 1',
        platform_id: 1,
        platform_name: 'WeChat',
        account_id: 1,
        account_name: 'WeChat Account 1',
        status: 'pending',
        publish_time: '2024-01-02 09:00:00',
        priority: 2
      },
      {
        id: 2,
        content_id: 2,
        content_title: 'Test Content 2',
        platform_id: 2,
        platform_name: 'Weibo',
        account_id: 2,
        account_name: 'Weibo Account 1',
        status: 'published',
        publish_time: '2024-01-01 10:00:00',
        priority: 3
      }
    ],
    total: 2
  }

  const mockContents = {
    items: [
      { id: 1, title: 'Content 1' },
      { id: 2, title: 'Content 2' }
    ]
  }

  const mockPlatforms = {
    items: [
      { id: 1, name: 'WeChat' },
      { id: 2, name: 'Weibo' }
    ]
  }

  const mockAccounts = {
    items: [
      { id: 1, name: 'WeChat Account 1' },
      { id: 2, name: 'Weibo Account 1' }
    ]
  }

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    // Mock API responses
    publishPool.getPublishPool.mockResolvedValue(mockPublishPoolList)
    publishPool.addToPublishPool.mockResolvedValue({ id: 1 })
    publishPool.updatePublishPoolItem.mockResolvedValue({ id: 1 })
    publishPool.deletePublishPoolItem.mockResolvedValue({})
    publishPool.batchPublish.mockResolvedValue({})
    publishPool.clearPublished.mockResolvedValue({})

    content.getContentList.mockResolvedValue(mockContents)
    platforms.getPlatforms.mockResolvedValue(mockPlatforms)
    accounts.getAccounts.mockResolvedValue(mockAccounts)
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  describe('页面加载和数据获取', () => {
    it('应该正确渲染页面', async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.publish-pool').exists()).toBe(true)
    })

    it('应该在挂载时获取发布池列表', async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      // 等待异步操作完成
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(publishPool.getPublishPool).toHaveBeenCalledWith({
        title: '',
        status: '',
        page: 1,
        page_size: 20
      })
    })

    it('应该在挂载时获取选项数据', async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(content.getContentList).toHaveBeenCalledWith({ page_size: 100 })
      expect(platforms.getPlatforms).toHaveBeenCalledWith({ page_size: 100 })
      expect(accounts.getAccounts).toHaveBeenCalledWith({ page_size: 100 })
    })

    it('应该正确处理获取数据失败', async () => {
      publishPool.getPublishPool.mockRejectedValue(new Error('API Error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(consoleSpy).toHaveBeenCalledWith('获取发布池失败:', expect.any(Error))
      consoleSpy.mockRestore()
    })
  })

  describe('搜索和过滤功能', () => {
    beforeEach(async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确执行搜索', async () => {
      wrapper.vm.searchForm.title = 'Test Content'
      wrapper.vm.searchForm.status = 'pending'

      await wrapper.vm.handleSearch()

      expect(publishPool.getPublishPool).toHaveBeenCalledWith({
        title: 'Test Content',
        status: 'pending',
        page: 1,
        page_size: 20
      })
    })

    it('应该正确执行重置', async () => {
      wrapper.vm.searchForm.title = 'Test'
      wrapper.vm.searchForm.status = 'published'

      await wrapper.vm.handleReset()

      expect(wrapper.vm.searchForm.page).toBe(1)
      expect(publishPool.getPublishPool).toHaveBeenCalled()
    })
  })

  describe('分页导航', () => {
    beforeEach(async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确处理页码变化', async () => {
      await wrapper.vm.handlePageChange(2)

      expect(wrapper.vm.searchForm.page).toBe(2)
      expect(publishPool.getPublishPool).toHaveBeenCalledWith({
        title: '',
        status: '',
        page: 2,
        page_size: 20
      })
    })

    it('应该正确处理每页数量变化', async () => {
      await wrapper.vm.handleSizeChange(50)

      expect(wrapper.vm.searchForm.pageSize).toBe(50)
      expect(wrapper.vm.searchForm.page).toBe(1)
      expect(publishPool.getPublishPool).toHaveBeenCalledWith({
        title: '',
        status: '',
        page: 1,
        page_size: 50
      })
    })
  })

  describe('发布操作', () => {
    beforeEach(async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确发布单个项目', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      const row = mockPublishPoolList.items[0]
      await wrapper.vm.handlePublish(row)

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要立即发布此内容吗？',
        '提示',
        expect.any(Object)
      )
      expect(publishPool.batchPublish).toHaveBeenCalledWith({ ids: [row.id] })
      expect(ElMessage.success).toHaveBeenCalledWith('发布成功')
    })

    it('应该正确批量发布', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      wrapper.vm.selectedRows = mockPublishPoolList.items
      await wrapper.vm.handleBatchPublish()

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        `确定要发布选中的 ${mockPublishPoolList.items.length} 个内容吗？`,
        '提示',
        expect.any(Object)
      )
      expect(publishPool.batchPublish).toHaveBeenCalledWith({
        ids: [1, 2]
      })
      expect(ElMessage.success).toHaveBeenCalledWith('发布成功')
      expect(wrapper.vm.selectedRows).toEqual([])
    })

    it('应该正确清空已发布项', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      await wrapper.vm.handleClearPublished()

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要清空所有已发布的项吗？',
        '提示',
        expect.any(Object)
      )
      expect(publishPool.clearPublished).toHaveBeenCalled()
      expect(ElMessage.success).toHaveBeenCalledWith('清空成功')
    })
  })

  describe('CRUD操作', () => {
    beforeEach(async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该打开添加对话框', async () => {
      await wrapper.vm.handleCreate()

      expect(wrapper.vm.dialogMode).toBe('create')
      expect(wrapper.vm.dialogTitle).toBe('添加到发布池')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该打开查看对话框', async () => {
      const row = mockPublishPoolList.items[0]
      await wrapper.vm.handleView(row)

      expect(wrapper.vm.dialogMode).toBe('view')
      expect(wrapper.vm.dialogTitle).toBe('查看发布项')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该打开编辑对话框', async () => {
      const row = mockPublishPoolList.items[0]
      await wrapper.vm.handleEdit(row)

      expect(wrapper.vm.dialogMode).toBe('edit')
      expect(wrapper.vm.dialogTitle).toBe('编辑发布项')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该正确删除项目', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      const row = mockPublishPoolList.items[0]
      await wrapper.vm.handleDelete(row)

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除此项吗？',
        '提示',
        expect.any(Object)
      )
      expect(publishPool.deletePublishPoolItem).toHaveBeenCalledWith(row.id)
      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    it('应该正确创建发布池项', async () => {
      wrapper.vm.dialogMode = 'create'
      wrapper.vm.formData = {
        content_id: 1,
        platform_id: 1,
        account_id: 1,
        publish_time: '2024-01-02 09:00:00',
        priority: 2
      }

      // Mock form validation
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }

      await wrapper.vm.handleSubmit()

      expect(publishPool.addToPublishPool).toHaveBeenCalledWith({
        content_id: 1,
        platform_id: 1,
        account_id: 1,
        publish_time: '2024-01-02 09:00:00',
        priority: 2
      })
      expect(ElMessage.success).toHaveBeenCalledWith('添加成功')
    })

    it('应该正确更新发布池项', async () => {
      wrapper.vm.dialogMode = 'edit'
      wrapper.vm.formData = {
        id: 1,
        content_id: 2,
        platform_id: 2,
        account_id: 2,
        publish_time: '2024-01-03 10:00:00',
        priority: 3
      }

      // Mock form validation
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }

      await wrapper.vm.handleSubmit()

      expect(publishPool.updatePublishPoolItem).toHaveBeenCalledWith(1, {
        content_id: 2,
        platform_id: 2,
        account_id: 2,
        publish_time: '2024-01-03 10:00:00',
        priority: 3
      })
      expect(ElMessage.success).toHaveBeenCalledWith('更新成功')
    })

    it('应该在表单验证失败时不提交', async () => {
      wrapper.vm.dialogMode = 'create'

      // Mock form validation failure
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(false),
        resetFields: vi.fn()
      }

      await wrapper.vm.handleSubmit()

      expect(publishPool.addToPublishPool).not.toHaveBeenCalled()
    })
  })

  describe('选择功能', () => {
    beforeEach(async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确处理选择变化', () => {
      const selection = [mockPublishPoolList.items[0]]
      wrapper.vm.handleSelectionChange(selection)

      expect(wrapper.vm.selectedRows).toEqual(selection)
    })
  })

  describe('对话框关闭', () => {
    beforeEach(async () => {
      wrapper = mount(PublishPool, {
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
            'el-date-picker': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确关闭对话框并重置表单', () => {
      wrapper.vm.formData.content_id = 1
      wrapper.vm.formData.platform_id = 2

      wrapper.vm.formRef = {
        resetFields: vi.fn()
      }

      wrapper.vm.handleDialogClose()

      expect(wrapper.vm.formRef.resetFields).toHaveBeenCalled()
      expect(wrapper.vm.formData.content_id).toBeNull()
      expect(wrapper.vm.formData.platform_id).toBeNull()
      expect(wrapper.vm.formData.priority).toBe(2)
    })
  })
})
