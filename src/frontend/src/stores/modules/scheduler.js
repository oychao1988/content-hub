import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as schedulerApi from '../../api/modules/scheduler'

export const useSchedulerStore = defineStore(
  'scheduler',
  () => {
    // 状态
    const tasks = ref([])
    const currentTask = ref(null)
    const executions = ref([])
    const loading = ref(false)
    const total = ref(0)

    // 计算属性
    const taskCount = computed(() => tasks.value.length)
    const activeTasks = computed(() => tasks.value.filter(t => t.is_active))
    const inactiveTasks = computed(() => tasks.value.filter(t => !t.is_active))
    const runningTasks = computed(() => tasks.value.filter(t => t.status === 'running'))
    const pausedTasks = computed(() => tasks.value.filter(t => t.status === 'paused'))

    // 获取任务列表
    const fetchTasks = async (params = {}) => {
      try {
        loading.value = true
        const response = await schedulerApi.getSchedulerTasks(params)
        tasks.value = response.items || response.data || response
        total.value = response.total || tasks.value.length
        return response
      } catch (error) {
        console.error('获取任务列表失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 获取任务详情
    const getTaskById = async (id) => {
      try {
        loading.value = true
        const response = await schedulerApi.getSchedulerTask(id)
        currentTask.value = response
        return response
      } catch (error) {
        console.error('获取任务详情失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 创建任务
    const createTask = async (data) => {
      try {
        loading.value = true
        const response = await schedulerApi.createSchedulerTask(data)
        // 创建成功后刷新列表
        await fetchTasks()
        return response
      } catch (error) {
        console.error('创建任务失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 更新任务
    const updateTask = async (id, data) => {
      try {
        loading.value = true
        const response = await schedulerApi.updateSchedulerTask(id, data)
        // 更新成功后刷新列表
        await fetchTasks()
        // 如果更新的是当前任务，也更新当前任务
        if (currentTask.value?.id === id) {
          await getTaskById(id)
        }
        return response
      } catch (error) {
        console.error('更新任务失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 删除任务
    const deleteTask = async (id) => {
      try {
        loading.value = true
        const response = await schedulerApi.deleteSchedulerTask(id)
        // 删除成功后刷新列表
        await fetchTasks()
        // 如果删除的是当前任务，清除当前任务
        if (currentTask.value?.id === id) {
          clearCurrentTask()
        }
        return response
      } catch (error) {
        console.error('删除任务失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 启用/禁用任务
    const toggleTask = async (id, isActive) => {
      try {
        loading.value = true
        const response = isActive
          ? await schedulerApi.startTask(id)
          : await schedulerApi.stopTask(id)
        // 切换成功后刷新列表
        await fetchTasks()
        // 如果切换的是当前任务，也更新当前任务
        if (currentTask.value?.id === id) {
          await getTaskById(id)
        }
        return response
      } catch (error) {
        console.error('切换任务状态失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 启动任务
    const startTask = async (id) => {
      return toggleTask(id, true)
    }

    // 停止任务
    const stopTask = async (id) => {
      return toggleTask(id, false)
    }

    // 暂停任务
    const pauseTask = async (id) => {
      try {
        loading.value = true
        const response = await schedulerApi.pauseTask(id)
        // 暂停成功后刷新列表
        await fetchTasks()
        // 如果暂停的是当前任务，也更新当前任务
        if (currentTask.value?.id === id) {
          await getTaskById(id)
        }
        return response
      } catch (error) {
        console.error('暂停任务失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 恢复任务
    const resumeTask = async (id) => {
      try {
        loading.value = true
        const response = await schedulerApi.resumeTask(id)
        // 恢复成功后刷新列表
        await fetchTasks()
        // 如果恢复的是当前任务，也更新当前任务
        if (currentTask.value?.id === id) {
          await getTaskById(id)
        }
        return response
      } catch (error) {
        console.error('恢复任务失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 手动运行任务
    const runTask = async (id) => {
      try {
        loading.value = true
        const response = await schedulerApi.executeTask(id)
        // 执行成功后刷新列表和执行历史
        await fetchTasks()
        if (currentTask.value?.id === id) {
          await getTaskById(id)
          await fetchExecutions(id)
        }
        return response
      } catch (error) {
        console.error('执行任务失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 获取执行历史
    const fetchExecutions = async (taskId, params = {}) => {
      try {
        loading.value = true
        const response = await schedulerApi.getTaskHistory(taskId, params)
        executions.value = response.items || response.data || response
        return response
      } catch (error) {
        console.error('获取执行历史失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 设置当前任务
    const setCurrentTask = (task) => {
      currentTask.value = task
    }

    // 清除当前任务
    const clearCurrentTask = () => {
      currentTask.value = null
    }

    // 清除执行历史
    const clearExecutions = () => {
      executions.value = []
    }

    // 根据任务类型筛选
    const getTasksByType = (taskType) => {
      return tasks.value.filter(t => t.task_type === taskType)
    }

    // 根据任务状态筛选
    const getTasksByStatus = (status) => {
      return tasks.value.filter(t => t.status === status)
    }

    // 重置状态
    const resetState = () => {
      tasks.value = []
      currentTask.value = null
      executions.value = []
      loading.value = false
      total.value = 0
    }

    return {
      // 状态
      tasks,
      currentTask,
      executions,
      loading,
      total,
      // 计算属性
      taskCount,
      activeTasks,
      inactiveTasks,
      runningTasks,
      pausedTasks,
      // 方法
      fetchTasks,
      getTaskById,
      createTask,
      updateTask,
      deleteTask,
      toggleTask,
      startTask,
      stopTask,
      pauseTask,
      resumeTask,
      runTask,
      fetchExecutions,
      setCurrentTask,
      clearCurrentTask,
      clearExecutions,
      getTasksByType,
      getTasksByStatus,
      resetState
    }
  }
)
