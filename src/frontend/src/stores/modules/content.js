import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as contentApi from '../../api/modules/content'

export const useContentStore = defineStore(
  'content',
  () => {
    // 状态
    const contents = ref([])
    const currentContent = ref(null)
    const filters = ref({})
    const loading = ref(false)
    const total = ref(0)
    const stats = ref(null)

    // 计算属性
    const contentCount = computed(() => contents.value.length)
    const pendingContents = computed(() => contents.value.filter(c => c.status === 'pending'))
    const approvedContents = computed(() => contents.value.filter(c => c.status === 'approved'))
    const rejectedContents = computed(() => contents.value.filter(c => c.status === 'rejected'))
    const publishedContents = computed(() => contents.value.filter(c => c.status === 'published'))

    // 获取内容列表
    const fetchContents = async (params = {}) => {
      try {
        loading.value = true
        // 合并现有筛选条件和新参数
        const mergedParams = { ...filters.value, ...params }
        filters.value = mergedParams

        const response = await contentApi.getContentList(mergedParams)
        contents.value = response.items || response.data || response
        total.value = response.total || contents.value.length
        return response
      } catch (error) {
        console.error('获取内容列表失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 获取内容详情
    const getContentById = async (id) => {
      try {
        loading.value = true
        const response = await contentApi.getContent(id)
        currentContent.value = response
        return response
      } catch (error) {
        console.error('获取内容详情失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 生成内容
    const generateContent = async (data) => {
      try {
        loading.value = true
        const response = await contentApi.generateContent(data)
        // 生成成功后刷新列表
        await fetchContents()
        return response
      } catch (error) {
        console.error('生成内容失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 创建内容
    const createContent = async (data) => {
      try {
        loading.value = true
        const response = await contentApi.createContent(data)
        // 创建成功后刷新列表
        await fetchContents()
        return response
      } catch (error) {
        console.error('创建内容失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 更新内容
    const updateContent = async (id, data) => {
      try {
        loading.value = true
        const response = await contentApi.updateContent(id, data)
        // 更新成功后刷新列表
        await fetchContents()
        // 如果更新的是当前内容，也更新当前内容
        if (currentContent.value?.id === id) {
          await getContentById(id)
        }
        return response
      } catch (error) {
        console.error('更新内容失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 删除内容
    const deleteContent = async (id) => {
      try {
        loading.value = true
        const response = await contentApi.deleteContent(id)
        // 删除成功后刷新列表
        await fetchContents()
        // 如果删除的是当前内容，清除当前内容
        if (currentContent.value?.id === id) {
          clearCurrentContent()
        }
        return response
      } catch (error) {
        console.error('删除内容失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 批量删除内容
    const batchDeleteContent = async (ids) => {
      try {
        loading.value = true
        const response = await contentApi.batchDeleteContent(ids)
        // 删除成功后刷新列表
        await fetchContents()
        // 如果当前内容在删除列表中，清除当前内容
        if (ids.includes(currentContent.value?.id)) {
          clearCurrentContent()
        }
        return response
      } catch (error) {
        console.error('批量删除内容失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 审核内容（通过更新内容状态实现）
    const reviewContent = async (id, status, comment = '') => {
      try {
        loading.value = true
        const response = await contentApi.updateContent(id, {
          status,
          review_comment: comment
        })
        // 审核成功后刷新列表
        await fetchContents()
        // 如果审核的是当前内容，也更新当前内容
        if (currentContent.value?.id === id) {
          await getContentById(id)
        }
        return response
      } catch (error) {
        console.error('审核内容失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 通过内容
    const approveContent = async (id, comment = '') => {
      return reviewContent(id, 'approved', comment)
    }

    // 拒绝内容
    const rejectContent = async (id, comment = '') => {
      return reviewContent(id, 'rejected', comment)
    }

    // 设置当前内容
    const setCurrentContent = (content) => {
      currentContent.value = content
    }

    // 清除当前内容
    const clearCurrentContent = () => {
      currentContent.value = null
    }

    // 设置筛选条件
    const setFilters = (newFilters) => {
      filters.value = { ...filters.value, ...newFilters }
    }

    // 清除筛选条件
    const clearFilters = () => {
      filters.value = {}
    }

    // 获取内容统计
    const fetchStats = async () => {
      try {
        const response = await contentApi.getContentStats()
        stats.value = response
        return response
      } catch (error) {
        console.error('获取内容统计失败:', error)
        throw error
      }
    }

    // 根据状态筛选内容
    const getContentsByStatus = (status) => {
      return contents.value.filter(c => c.status === status)
    }

    // 根据账号ID筛选内容
    const getContentsByAccount = (accountId) => {
      return contents.value.filter(c => c.account_id === accountId)
    }

    // 重置状态
    const resetState = () => {
      contents.value = []
      currentContent.value = null
      filters.value = {}
      loading.value = false
      total.value = 0
      stats.value = null
    }

    return {
      // 状态
      contents,
      currentContent,
      filters,
      loading,
      total,
      stats,
      // 计算属性
      contentCount,
      pendingContents,
      approvedContents,
      rejectedContents,
      publishedContents,
      // 方法
      fetchContents,
      getContentById,
      generateContent,
      createContent,
      updateContent,
      deleteContent,
      batchDeleteContent,
      reviewContent,
      approveContent,
      rejectContent,
      setCurrentContent,
      clearCurrentContent,
      setFilters,
      clearFilters,
      fetchStats,
      getContentsByStatus,
      getContentsByAccount,
      resetState
    }
  }
)
