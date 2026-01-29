import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/modules/user'

// Mock auth API
vi.mock('@/api/modules/auth', () => ({
  login: vi.fn(),
  logout: vi.fn(),
  getCurrentUser: vi.fn()
}))

describe('User Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useUserStore()

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.permissions).toEqual([])
    })

    it('应该正确计算 isAuthenticated', () => {
      const store = useUserStore()

      expect(store.isAuthenticated).toBe(false)

      store.token = 'test-token'
      expect(store.isAuthenticated).toBe(true)
    })

    it('应该正确计算 isAdmin', () => {
      const store = useUserStore()

      expect(store.isAdmin).toBe(false)

      store.user = { role: 'admin' }
      expect(store.isAdmin).toBe(true)

      store.user = { role: 'user' }
      expect(store.isAdmin).toBe(false)
    })

    it('应该正确计算 userName', () => {
      const store = useUserStore()

      expect(store.userName).toBe('')

      store.user = { username: 'testuser' }
      expect(store.userName).toBe('testuser')
    })

    it('应该正确计算 userEmail', () => {
      const store = useUserStore()

      expect(store.userEmail).toBe('')

      store.user = { email: 'test@example.com' }
      expect(store.userEmail).toBe('test@example.com')
    })
  })

  describe('login 方法', () => {
    it('应该成功登录并设置 token', async () => {
      const { login, getCurrentUser } = require('@/api/modules/auth')
      login.mockResolvedValue({ access_token: 'test-token' })
      getCurrentUser.mockResolvedValue({
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'admin',
        permissions: ['account:create', 'account:update']
      })

      const store = useUserStore()
      const credentials = { username: 'testuser', password: 'password' }

      const response = await store.login(credentials)

      expect(store.token).toBe('test-token')
      expect(store.user).toBeDefined()
      expect(store.user.username).toBe('testuser')
      expect(response.access_token).toBe('test-token')
      expect(login).toHaveBeenCalledWith(credentials)
      expect(getCurrentUser).toHaveBeenCalled()
    })

    it('应该处理登录失败', async () => {
      const { login } = require('@/api/modules/auth')
      login.mockRejectedValue(new Error('Login failed'))

      const store = useUserStore()

      await expect(store.login({ username: 'test', password: 'wrong' }))
        .rejects.toThrow('Login failed')

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
    })
  })

  describe('logout 方法', () => {
    it('应该成功登出并清除状态', async () => {
      const { logout } = require('@/api/modules/auth')
      logout.mockResolvedValue({})

      const store = useUserStore()
      store.token = 'test-token'
      store.user = { username: 'testuser' }
      store.permissions = ['account:create']

      await store.logout()

      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.permissions).toEqual([])
      expect(logout).toHaveBeenCalled()
    })

    it('应该处理登出 API 错误但仍清除状态', async () => {
      const { logout } = require('@/api/modules/auth')
      logout.mockRejectedValue(new Error('Logout failed'))

      const store = useUserStore()
      store.token = 'test-token'
      store.user = { username: 'testuser' }
      store.permissions = ['account:create']

      await store.logout()

      // 即使 API 失败，也应该清除状态
      expect(store.token).toBe('')
      expect(store.user).toBeNull()
      expect(store.permissions).toEqual([])
    })
  })

  describe('getUserInfo 方法', () => {
    it('应该获取用户信息', async () => {
      const { getCurrentUser } = require('@/api/modules/auth')
      const mockUser = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'operator',
        permissions: ['content:create', 'content:update']
      }
      getCurrentUser.mockResolvedValue(mockUser)

      const store = useUserStore()
      const response = await store.getUserInfo()

      expect(store.user).toEqual(mockUser)
      expect(store.permissions).toEqual(['content:create', 'content:update'])
      expect(response).toEqual(mockUser)
      expect(getCurrentUser).toHaveBeenCalled()
    })

    it('应该处理获取用户信息失败', async () => {
      const { getCurrentUser } = require('@/api/modules/auth')
      getCurrentUser.mockRejectedValue(new Error('Failed to get user info'))

      const store = useUserStore()

      await expect(store.getUserInfo()).rejects.toThrow('Failed to get user info')
    })
  })

  describe('权限检查方法', () => {
    it('hasPermission - admin 应该有所有权限', () => {
      const store = useUserStore()
      store.user = { role: 'admin' }
      store.permissions = []

      expect(store.hasPermission('any:permission')).toBe(true)
    })

    it('hasPermission - 非管理员应该检查实际权限', () => {
      const store = useUserStore()
      store.user = { role: 'operator' }
      store.permissions = ['account:create', 'account:update']

      expect(store.hasPermission('account:create')).toBe(true)
      expect(store.hasPermission('account:delete')).toBe(false)
    })

    it('hasAnyPermission - admin 应该通过', () => {
      const store = useUserStore()
      store.user = { role: 'admin' }
      store.permissions = []

      expect(store.hasAnyPermission(['any:permission'])).toBe(true)
    })

    it('hasAnyPermission - 应该满足任意一个权限', () => {
      const store = useUserStore()
      store.user = { role: 'operator' }
      store.permissions = ['account:create']

      expect(store.hasAnyPermission(['account:create', 'account:delete'])).toBe(true)
      expect(store.hasAnyPermission(['account:update', 'account:delete'])).toBe(false)
    })

    it('hasAllPermissions - admin 应该通过', () => {
      const store = useUserStore()
      store.user = { role: 'admin' }
      store.permissions = []

      expect(store.hasAllPermissions(['any:permission', 'another:permission'])).toBe(true)
    })

    it('hasAllPermissions - 非管理员应该拥有所有权限', () => {
      const store = useUserStore()
      store.user = { role: 'operator' }
      store.permissions = ['account:create', 'account:update', 'account:delete']

      expect(store.hasAllPermissions(['account:create', 'account:update'])).toBe(true)
      expect(store.hasAllPermissions(['account:create', 'content:create'])).toBe(false)
    })
  })
})
