import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { rest } from 'msw'
import { setupServer } from 'msw/node'
import axios from 'axios'
import request from '@/utils/request'

// Mock Element Plus
vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    warning: vi.fn(),
    success: vi.fn()
  }
}))

// Mock stores
vi.mock('@/stores/modules/user', () => ({
  useUserStore: vi.fn(() => ({
    token: 'mock-token',
    logout: vi.fn()
  }))
}))

vi.mock('@/stores/modules/cache', () => ({
  useCacheStore: vi.fn(() => ({
    set: vi.fn(),
    get: vi.fn(() => null)
  }))
}))

// Mock config
vi.mock('@/config', () => ({
  default: {
    apiBaseUrl: 'http://localhost:8000',
    apiVersion: '/api/v1',
    timeout: 10000
  }
}))

// Mock errorHandler
vi.mock('@/utils/errorHandler', () => ({
  default: {
    extractAxiosError: vi.fn((error) => ({
      status: error.response?.status,
      data: error.response?.data,
      message: error.response?.data?.message || 'Error',
      degraded: error.response?.status === 503
    })),
    shouldLogout: vi.fn((status, data) => status === 401),
    isRetryable: vi.fn((status, data) => status === 503 || status === 504),
    handleValidationError: vi.fn((details) => 'Validation error')
  }
}))

// 创建 MSW 服务器
const server = setupServer(
  // 成功响应
  rest.get('/api/v1/test', (req, res, ctx) => {
    return res(
      ctx.status(200),
      ctx.json({ message: 'Success', data: { id: 1, name: 'Test' } })
    )
  }),

  // 401 响应
  rest.get('/api/v1/unauthorized', (req, res, ctx) => {
    return res(
      ctx.status(401),
      ctx.json({ detail: 'Unauthorized' })
    )
  }),

  // 404 响应
  rest.get('/api/v1/notfound', (req, res, ctx) => {
    return res(
      ctx.status(404),
      ctx.json({ detail: 'Not found' })
    )
  }),

  // 500 响应
  rest.get('/api/v1/error', (req, res, ctx) => {
    return res(
      ctx.status(500),
      ctx.json({ detail: 'Internal server error' })
    )
  }),

  // 503 降级响应
  rest.get('/api/v1/degraded', (req, res, ctx) => {
    return res(
      ctx.status(503),
      ctx.json({ message: 'Service temporarily unavailable' })
    )
  }),

  // 422 验证错误
  rest.post('/api/v1/validation', (req, res, ctx) => {
    return res(
      ctx.status(422),
      ctx.json({
        detail: [
          { loc: ['body', 'name'], msg: 'Field required', type: 'value_error.missing' }
        ]
      })
    )
  }),

  // 慢请求
  rest.get('/api/v1/slow', (req, res, ctx) => {
    return res(
      ctx.delay(4000),
      ctx.status(200),
      ctx.json({ message: 'Slow response' })
    )
  }),

  // POST 请求
  rest.post('/api/v1/create', (req, res, ctx) => {
    return res(
      ctx.status(201),
      ctx.json({ message: 'Created', id: 1 })
    )
  })
)

describe('API Request 工具', () => {
  beforeEach(() => {
    // 启动 MSW 服务器
    server.listen()
    vi.clearAllMocks()
  })

  afterEach(() => {
    // 重置处理器
    server.resetHandlers()
    // 关闭服务器
    server.close()
  })

  describe('请求拦截器', () => {
    it('应该在请求头中添加 Authorization token', async () => {
      const response = await request.get('/test')

      expect(response.config.headers.Authorization).toBeDefined()
      expect(response.config.headers.Authorization).toContain('Bearer')
    })

    it('应该添加 X-Request-ID 头', async () => {
      const response = await request.get('/test')

      expect(response.config.headers['X-Request-ID']).toBeDefined()
      expect(response.config.headers['X-Request-ID']).toMatch(/^req_/)
    })

    it('应该添加元数据到请求配置', async () => {
      const response = await request.get('/test')

      expect(response.config.metadata).toBeDefined()
      expect(response.config.metadata.startTime).toBeDefined()
      expect(response.config.metadata.requestId).toBeDefined()
    })
  })

  describe('响应拦截器 - 成功响应', () => {
    it('应该返回响应数据', async () => {
      const response = await request.get('/test')

      expect(response).toBeDefined()
      expect(response.message).toBe('Success')
      expect(response.data).toEqual({ id: 1, name: 'Test' })
    })

    it('应该缓存 GET 请求当启用缓存时', async () => {
      const { useCacheStore } = require('@/stores/modules/cache')
      const cacheStore = useCacheStore()

      await request.get('/test', { enableCache: true, cacheTTL: 60000 })

      expect(cacheStore.set).toHaveBeenCalledWith(
        '/test',
        {},
        { message: 'Success', data: { id: 1, name: 'Test' } },
        60000
      )
    })

    it('应该警告慢请求', async () => {
      const consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})

      await request.get('/slow')

      expect(consoleWarnSpy).toHaveBeenCalledWith(
        expect.stringContaining('慢请求警告')
      )

      consoleWarnSpy.mockRestore()
    })
  })

  describe('响应拦截器 - 错误处理', () => {
    it('应该处理 401 未授权错误', async () => {
      const { useUserStore } = require('@/stores/modules/user')
      const { ElMessage } = require('element-plus')
      const userStore = useUserStore()

      await expect(request.get('/unauthorized')).rejects.toThrow()

      expect(ElMessage.error).toHaveBeenCalledWith('登录已过期，请重新登录')
      expect(userStore.logout).toHaveBeenCalled()
    })

    it('应该处理 404 错误', async () => {
      const { ElMessage } = require('element-plus')

      await expect(request.get('/notfound')).rejects.toThrow()

      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('应该处理 500 服务器错误', async () => {
      const { ElMessage } = require('element-plus')

      await expect(request.get('/error')).rejects.toThrow()

      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('应该处理 503 降级响应', async () => {
      const { ElMessage } = require('element-plus')

      const error = await request.get('/degraded').catch(err => err)

      expect(ElMessage.warning).toHaveBeenCalled()
      expect(error.degraded).toBe(true)
    })

    it('应该处理 422 验证错误', async () => {
      const { ElMessage } = require('element-plus')

      await expect(request.post('/validation', {})).rejects.toThrow()

      expect(ElMessage.error).toHaveBeenCalledWith('Validation error')
    })
  })

  describe('请求重试机制', () => {
    it('应该在可重试错误时自动重试', async () => {
      let attemptCount = 0

      server.use(
        rest.get('/api/v1/retry', (req, res, ctx) => {
          attemptCount++
          if (attemptCount < 3) {
            return res(ctx.status(503))
          }
          return res(ctx.status(200), ctx.json({ message: 'Success after retry' }))
        })
      )

      const response = await request.get('/retry')

      expect(attemptCount).toBe(3)
      expect(response.message).toBe('Success after retry')
    })

    it('应该在达到最大重试次数后失败', async () => {
      server.use(
        rest.get('/api/v1/fail', (req, res, ctx) => {
          return res(ctx.status(503))
        })
      )

      await expect(request.get('/fail')).rejects.toThrow()
    })

    it('应该支持跳过重试', async () => {
      let attemptCount = 0

      server.use(
        rest.get('/api/v1/skip-retry', (req, res, ctx) => {
          attemptCount++
          return res(ctx.status(503))
        })
      )

      await expect(request.get('/skip-retry', { _skipRetry: true })).rejects.toThrow()

      expect(attemptCount).toBe(1)
    })
  })

  describe('静默模式', () => {
    it('不应该在静默模式下显示错误消息', async () => {
      const { ElMessage } = require('element-plus')

      await expect(
        request.get('/error', { _silent: true })
      ).rejects.toThrow()

      expect(ElMessage.error).not.toHaveBeenCalled()
    })
  })

  describe('辅助函数', () => {
    it('silentRequest.get 应该使用静默模式', async () => {
      const { silentRequest } = require('@/utils/request')
      const { ElMessage } = require('element-plus')

      await expect(silentRequest.get('/error')).rejects.toThrow()

      expect(ElMessage.error).not.toHaveBeenCalled()
    })

    it('noRetryRequest.get 应该跳过重试', async () => {
      const { noRetryRequest } = require('@/utils/request')
      let attemptCount = 0

      server.use(
        rest.get('/api/v1/no-retry', (req, res, ctx) => {
          attemptCount++
          return res(ctx.status(503))
        })
      )

      await expect(noRetryRequest.get('/no-retry')).rejects.toThrow()

      expect(attemptCount).toBe(1)
    })

    it('cachedGet 应该使用缓存', async () => {
      const { cachedGet } = require('@/utils/request')
      const { useCacheStore } = require('@/stores/modules/cache')
      const cacheStore = useCacheStore()

      // Mock 缓存命中
      cacheStore.get.mockReturnValue({ message: 'Cached data' })

      const response = await cachedGet('/test', {}, 60000)

      expect(response).toEqual({ message: 'Cached data' })
      expect(cacheStore.get).toHaveBeenCalledWith('/test', {})
    })
  })

  describe('请求日志', () => {
    it('应该记录错误日志', async () => {
      const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      await expect(request.get('/error')).rejects.toThrow()

      expect(consoleErrorSpy).toHaveBeenCalledWith(
        'API 请求失败:',
        expect.objectContaining({
          url: '/error',
          method: 'get'
        })
      )

      consoleErrorSpy.mockRestore()
    })
  })
})
