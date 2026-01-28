import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../../api/modules/auth'
import config from '../../config'

export const useUserStore = defineStore(
  'user',
  () => {
    // 状态
    const token = ref('')
    const user = ref(null)
    const permissions = ref([])

    // 计算属性
    const isAuthenticated = computed(() => !!token.value)
    const isAdmin = computed(() => user.value?.role === 'admin')
    const userName = computed(() => user.value?.username || '')
    const userEmail = computed(() => user.value?.email || '')

    // 登录
    const login = async (credentials) => {
      try {
        const response = await authApi.login(credentials)
        token.value = response.access_token
        await getUserInfo()
        return response
      } catch (error) {
        console.error('登录失败:', error)
        throw error
      }
    }

    // 登出
    const logout = async () => {
      try {
        await authApi.logout()
      } catch (error) {
        console.error('登出失败:', error)
      } finally {
        token.value = ''
        user.value = null
        permissions.value = []
      }
    }

    // 获取用户信息
    const getUserInfo = async () => {
      try {
        const response = await authApi.getCurrentUser()
        user.value = response
        permissions.value = response.permissions || []
        return response
      } catch (error) {
        console.error('获取用户信息失败:', error)
        throw error
      }
    }

    // 检查权限
    const hasPermission = (permission) => {
      if (isAdmin.value) return true
      return permissions.value.includes(permission)
    }

    // 检查多个权限（满足任意一个即可）
    const hasAnyPermission = (permissionList) => {
      if (isAdmin.value) return true
      return permissionList.some(permission => permissions.value.includes(permission))
    }

    // 检查多个权限（必须满足所有）
    const hasAllPermissions = (permissionList) => {
      if (isAdmin.value) return true
      return permissionList.every(permission => permissions.value.includes(permission))
    }

    return {
      // 状态
      token,
      user,
      permissions,
      // 计算属性
      isAuthenticated,
      isAdmin,
      userName,
      userEmail,
      // 方法
      login,
      logout,
      getUserInfo,
      hasPermission,
      hasAnyPermission,
      hasAllPermissions
    }
  },
  {
    persist: {
      key: 'user-store',
      storage: localStorage,
      paths: ['token', 'user', 'permissions']
    }
  }
)
