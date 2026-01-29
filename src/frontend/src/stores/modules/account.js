import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as accountsApi from '../../api/modules/accounts'

export const useAccountStore = defineStore(
  'account',
  () => {
    // 状态
    const accounts = ref([])
    const currentAccount = ref(null)
    const loading = ref(false)
    const total = ref(0)

    // 计算属性
    const accountCount = computed(() => accounts.value.length)
    const activeAccounts = computed(() => accounts.value.filter(acc => acc.is_active))

    // 获取账号列表
    const fetchAccounts = async (filters = {}) => {
      try {
        loading.value = true
        const response = await accountsApi.getAccounts(filters)
        accounts.value = response.items || response.data || response
        total.value = response.total || accounts.value.length
        return response
      } catch (error) {
        console.error('获取账号列表失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 获取账号详情
    const getAccountById = async (id) => {
      try {
        loading.value = true
        const response = await accountsApi.getAccount(id)
        currentAccount.value = response
        return response
      } catch (error) {
        console.error('获取账号详情失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 创建账号
    const createAccount = async (data) => {
      try {
        loading.value = true
        const response = await accountsApi.createAccount(data)
        // 创建成功后刷新列表
        await fetchAccounts()
        return response
      } catch (error) {
        console.error('创建账号失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 更新账号
    const updateAccount = async (id, data) => {
      try {
        loading.value = true
        const response = await accountsApi.updateAccount(id, data)
        // 更新成功后刷新列表
        await fetchAccounts()
        // 如果更新的是当前账号，也更新当前账号
        if (currentAccount.value?.id === id) {
          await getAccountById(id)
        }
        return response
      } catch (error) {
        console.error('更新账号失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 删除账号
    const deleteAccount = async (id) => {
      try {
        loading.value = true
        const response = await accountsApi.deleteAccount(id)
        // 删除成功后刷新列表
        await fetchAccounts()
        // 如果删除的是当前账号，清除当前账号
        if (currentAccount.value?.id === id) {
          clearCurrentAccount()
        }
        return response
      } catch (error) {
        console.error('删除账号失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 批量删除账号
    const batchDeleteAccounts = async (ids) => {
      try {
        loading.value = true
        const response = await accountsApi.batchDeleteAccounts(ids)
        // 删除成功后刷新列表
        await fetchAccounts()
        // 如果当前账号在删除列表中，清除当前账号
        if (ids.includes(currentAccount.value?.id)) {
          clearCurrentAccount()
        }
        return response
      } catch (error) {
        console.error('批量删除账号失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 同步账号状态
    const syncAccount = async (id) => {
      try {
        loading.value = true
        const response = await accountsApi.syncAccount(id)
        // 同步成功后刷新列表和当前账号
        await fetchAccounts()
        if (currentAccount.value?.id === id) {
          await getAccountById(id)
        }
        return response
      } catch (error) {
        console.error('同步账号失败:', error)
        throw error
      } finally {
        loading.value = false
      }
    }

    // 设置当前账号
    const setCurrentAccount = (account) => {
      currentAccount.value = account
    }

    // 清除当前账号
    const clearCurrentAccount = () => {
      currentAccount.value = null
    }

    // 根据平台类型筛选账号
    const getAccountsByPlatform = (platform) => {
      return accounts.value.filter(acc => acc.platform === platform)
    }

    // 重置状态
    const resetState = () => {
      accounts.value = []
      currentAccount.value = null
      loading.value = false
      total.value = 0
    }

    return {
      // 状态
      accounts,
      currentAccount,
      loading,
      total,
      // 计算属性
      accountCount,
      activeAccounts,
      // 方法
      fetchAccounts,
      getAccountById,
      createAccount,
      updateAccount,
      deleteAccount,
      batchDeleteAccounts,
      syncAccount,
      setCurrentAccount,
      clearCurrentAccount,
      getAccountsByPlatform,
      resetState
    }
  }
)
