import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import SchedulerManage from '@/pages/SchedulerManage.vue'
import { scheduler as schedulerApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

// Mock API modules
vi.mock('@/api', () => ({
  scheduler: {
    getSchedulerTasks: vi.fn(),
    createSchedulerTask: vi.fn(),
    updateSchedulerTask: vi.fn(),
    deleteSchedulerTask: vi.fn(),
    pauseTask: vi.fn(),
    resumeTask: vi.fn(),
    stopTask: vi.fn(),
    executeTask: vi.fn()
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

describe('SchedulerManage.vue', () => {
  let wrapper
  let pinia

  const mockTaskList = {
    items: [
      {
        id: 1,
        name: 'Content Generation Task',
        job_type: 'content_generation',
        cron_expression: '0 0 * * *',
        status: 'running',
        job_params: '{}',
        description: 'Generate content daily',
        next_run_time: '2024-01-02 00:00:00',
        last_run_time: '2024-01-01 00:00:00'
      },
      {
        id: 2,
        name: 'Scheduled Publish Task',
        job_type: 'scheduled_publish',
        cron_expression: '0 9 * * 1-5',
        status: 'paused',
        job_params: '{}',
        description: 'Publish on weekdays',
        next_run_time: '2024-01-02 09:00:00',
        last_run_time: '2024-01-01 09:00:00'
      }
    ],
    total: 2
  }

  beforeEach(() => {
    pinia = createPinia()
    setActivePinia(pinia)

    // Mock API responses
    schedulerApi.getSchedulerTasks.mockResolvedValue(mockTaskList)
    schedulerApi.createSchedulerTask.mockResolvedValue({ id: 1 })
    schedulerApi.updateSchedulerTask.mockResolvedValue({ id: 1 })
    schedulerApi.pauseTask.mockResolvedValue({})
    schedulerApi.resumeTask.mockResolvedValue({})
    schedulerApi.stopTask.mockResolvedValue({})
    schedulerApi.executeTask.mockResolvedValue({})
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  describe('页面加载和数据获取', () => {
    it('应该正确渲染页面', async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      expect(wrapper.exists()).toBe(true)
      expect(wrapper.find('.scheduler-manage').exists()).toBe(true)
    })

    it('应该在挂载时获取任务列表', async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      // 等待异步操作完成
      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(schedulerApi.getSchedulerTasks).toHaveBeenCalledWith({
        name: '',
        job_type: '',
        status: '',
        page: 1,
        page_size: 20
      })
    })

    it('应该正确处理获取数据失败', async () => {
      schedulerApi.getSchedulerTasks.mockRejectedValue(new Error('API Error'))

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      await wrapper.vm.$nextTick()
      await new Promise(resolve => setTimeout(resolve, 0))

      expect(consoleSpy).toHaveBeenCalledWith('获取定时任务失败:', expect.any(Error))
      consoleSpy.mockRestore()
    })
  })

  describe('搜索和过滤功能', () => {
    beforeEach(async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确执行搜索', async () => {
      wrapper.vm.searchForm.name = 'Content Generation'
      wrapper.vm.searchForm.job_type = 'content_generation'
      wrapper.vm.searchForm.status = 'running'

      await wrapper.vm.handleSearch()

      expect(schedulerApi.getSchedulerTasks).toHaveBeenCalledWith({
        name: 'Content Generation',
        job_type: 'content_generation',
        status: 'running',
        page: 1,
        page_size: 20
      })
    })

    it('应该正确执行重置', async () => {
      wrapper.vm.searchForm.name = 'Test'
      wrapper.vm.searchForm.job_type = 'scheduled_publish'
      wrapper.vm.searchForm.status = 'paused'

      await wrapper.vm.handleReset()

      expect(wrapper.vm.searchForm.page).toBe(1)
      expect(schedulerApi.getSchedulerTasks).toHaveBeenCalled()
    })
  })

  describe('分页导航', () => {
    beforeEach(async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确处理页码变化', async () => {
      await wrapper.vm.handlePageChange(2)

      expect(wrapper.vm.searchForm.page).toBe(2)
      expect(schedulerApi.getSchedulerTasks).toHaveBeenCalledWith({
        name: '',
        job_type: '',
        status: '',
        page: 2,
        page_size: 20
      })
    })

    it('应该正确处理每页数量变化', async () => {
      await wrapper.vm.handleSizeChange(50)

      expect(wrapper.vm.searchForm.pageSize).toBe(50)
      expect(wrapper.vm.searchForm.page).toBe(1)
      expect(schedulerApi.getSchedulerTasks).toHaveBeenCalledWith({
        name: '',
        job_type: '',
        status: '',
        page: 1,
        page_size: 50
      })
    })
  })

  describe('任务操作', () => {
    beforeEach(async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该打开新建任务对话框', async () => {
      await wrapper.vm.handleCreate()

      expect(wrapper.vm.dialogMode).toBe('create')
      expect(wrapper.vm.dialogTitle).toBe('新建任务')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该打开查看任务对话框', async () => {
      const row = mockTaskList.items[0]
      await wrapper.vm.handleView(row)

      expect(wrapper.vm.dialogMode).toBe('view')
      expect(wrapper.vm.dialogTitle).toBe('查看任务')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该打开编辑任务对话框', async () => {
      const row = mockTaskList.items[0]
      await wrapper.vm.handleEdit(row)

      expect(wrapper.vm.dialogMode).toBe('edit')
      expect(wrapper.vm.dialogTitle).toBe('编辑任务')
      expect(wrapper.vm.dialogVisible).toBe(true)
    })

    it('应该正确暂停任务', async () => {
      const row = mockTaskList.items[0] // running task
      await wrapper.vm.handlePause(row)

      expect(schedulerApi.pauseTask).toHaveBeenCalledWith(row.id)
      expect(ElMessage.success).toHaveBeenCalledWith('暂停成功')
    })

    it('应该正确恢复任务', async () => {
      const row = mockTaskList.items[1] // paused task
      await wrapper.vm.handleResume(row)

      expect(schedulerApi.resumeTask).toHaveBeenCalledWith(row.id)
      expect(ElMessage.success).toHaveBeenCalledWith('恢复成功')
    })

    it('应该正确停止任务', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      const row = mockTaskList.items[0]
      await wrapper.vm.handleStop(row)

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要停止此任务吗？',
        '提示',
        expect.any(Object)
      )
      expect(schedulerApi.stopTask).toHaveBeenCalledWith(row.id)
      expect(ElMessage.success).toHaveBeenCalledWith('停止成功')
    })

    it('应该正确立即执行任务', async () => {
      ElMessageBox.confirm.mockResolvedValue('confirm')

      const row = mockTaskList.items[0]
      await wrapper.vm.handleExecute(row)

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要立即执行此任务吗？',
        '提示',
        expect.any(Object)
      )
      expect(schedulerApi.executeTask).toHaveBeenCalledWith(row.id)
      expect(ElMessage.success).toHaveBeenCalledWith('执行成功')
    })
  })

  describe('表单提交', () => {
    beforeEach(async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确创建任务', async () => {
      wrapper.vm.dialogMode = 'create'
      wrapper.vm.formData = {
        name: 'New Task',
        job_type: 'content_generation',
        cron_expression: '0 0 * * *',
        job_params: '{}',
        description: 'New task description'
      }

      // Mock form validation
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }

      await wrapper.vm.handleSubmit()

      expect(schedulerApi.createSchedulerTask).toHaveBeenCalledWith({
        name: 'New Task',
        job_type: 'content_generation',
        cron_expression: '0 0 * * *',
        job_params: '{}',
        description: 'New task description'
      })
      expect(ElMessage.success).toHaveBeenCalledWith('创建成功')
    })

    it('应该正确更新任务', async () => {
      wrapper.vm.dialogMode = 'edit'
      wrapper.vm.formData = {
        id: 1,
        name: 'Updated Task',
        job_type: 'scheduled_publish',
        cron_expression: '0 9 * * 1-5',
        job_params: '{}',
        description: 'Updated description'
      }

      // Mock form validation
      wrapper.vm.formRef = {
        validate: vi.fn().mockResolvedValue(true),
        resetFields: vi.fn()
      }

      await wrapper.vm.handleSubmit()

      expect(schedulerApi.updateSchedulerTask).toHaveBeenCalledWith(1, {
        name: 'Updated Task',
        job_type: 'scheduled_publish',
        cron_expression: '0 9 * * 1-5',
        job_params: '{}',
        description: 'Updated description'
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

      expect(schedulerApi.createSchedulerTask).not.toHaveBeenCalled()
    })
  })

  describe('工具函数', () => {
    beforeEach(async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确获取任务类型文本', () => {
      expect(wrapper.vm.getJobTypeText('content_generation')).toBe('内容生成')
      expect(wrapper.vm.getJobTypeText('scheduled_publish')).toBe('定时发布')
      expect(wrapper.vm.getJobTypeText('unknown')).toBe('unknown')
    })

    it('应该正确获取状态类型', () => {
      expect(wrapper.vm.getStatusType('running')).toBe('success')
      expect(wrapper.vm.getStatusType('paused')).toBe('warning')
      expect(wrapper.vm.getStatusType('stopped')).toBe('info')
      expect(wrapper.vm.getStatusType('unknown')).toBe('info')
    })

    it('应该正确获取状态文本', () => {
      expect(wrapper.vm.getStatusText('running')).toBe('运行中')
      expect(wrapper.vm.getStatusText('paused')).toBe('暂停')
      expect(wrapper.vm.getStatusText('stopped')).toBe('已停止')
      expect(wrapper.vm.getStatusText('unknown')).toBe('unknown')
    })
  })

  describe('对话框关闭', () => {
    beforeEach(async () => {
      wrapper = mount(SchedulerManage, {
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
            'el-col': true
          }
        }
      })

      await wrapper.vm.$nextTick()
    })

    it('应该正确关闭对话框并重置表单', () => {
      wrapper.vm.formData.name = 'Test Task'
      wrapper.vm.formData.job_type = 'content_generation'

      wrapper.vm.formRef = {
        resetFields: vi.fn()
      }

      wrapper.vm.handleDialogClose()

      expect(wrapper.vm.formRef.resetFields).toHaveBeenCalled()
      expect(wrapper.vm.formData.name).toBe('')
      expect(wrapper.vm.formData.job_type).toBe('')
    })
  })
})
