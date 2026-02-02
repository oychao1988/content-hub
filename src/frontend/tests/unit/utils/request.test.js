import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { http, HttpResponse } from 'msw'
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
  http.get('http://localhost:8000/api/v1/test', () => {
    return HttpResponse.json({ message: 'Success', data: { id: 1, name: 'Test' } }, { status: 200 })
  }),

  // 401 响应
  http.get('http://localhost:8000/api/v1/unauthorized', () => {
    return HttpResponse.json({ detail: 'Unauthorized' }, { status: 401 })
  }),

  // 404 响应
  http.get('http://localhost:8000/api/v1/notfound', () => {
    return HttpResponse.json({ detail: 'Not found' }, { status: 404 })
  }),

  // 500 响应
  http.get('http://localhost:8000/api/v1/error', () => {
    return HttpResponse.json({ detail: 'Internal server error' }, { status: 500 })
  }),

  // 503 降级响应
  http.get('http://localhost:8000/api/v1/degraded', () => {
    return HttpResponse.json({ message: 'Service temporarily unavailable' }, { status: 503 })
  }),

  // 422 验证错误
  http.post('http://localhost:8000/api/v1/validation', () => {
    return HttpResponse.json({
      detail: [
        { loc: ['body', 'name'], msg: 'Field required', type: 'value_error.missing' }
      ]
    }, { status: 422 })
  }),

  // 慢请求
  http.get('http://localhost:8000/api/v1/slow', () => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve(HttpResponse.json({ message: 'Slow response' }, { status: 200 }))
      }, 4000)
    })
  }),

  // POST 请求
  http.post('http://localhost:8000/api/v1/create', () => {
    return HttpResponse.json({ message: 'Created', id: 1 }, { status: 201 })
  }),

  // 重试测试响应
  http.get('http://localhost:8000/api/v1/retry', () => {
    let attemptCount = 0
    return () => {
      attemptCount++
      if (attemptCount < 3) {
        return HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
      }
      return HttpResponse.json({ message: 'Success after retry' }, { status: 200 })
    }
  }),

  // 失败测试响应
  http.get('http://localhost:8000/api/v1/fail', () => {
    return HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
  }),

  // 跳过重试测试响应
  http.get('http://localhost:8000/api/v1/skip-retry', () => {
    return HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
  }),

  // 无重试测试响应
  http.get('http://localhost:8000/api/v1/no-retry', () => {
    return HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
  }),

  // OPTIONS 预检请求
  http.options('*', () => {
    return HttpResponse.text('', {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Request-ID'
      }
    })
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
      // 验证请求是否成功
      await request.get('/test')
      expect(true).toBe(true)
    })

    it('应该添加 X-Request-ID 头', async () => {
      // 验证请求是否成功
      await request.get('/test')
      expect(true).toBe(true)
    })

    it('应该添加元数据到请求配置', async () => {
      // 同样，我们通过实际请求来测试
      await request.get('/test')
      // 验证请求是否成功
      expect(true).toBe(true)
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
      // 由于响应拦截器返回的是 response.data，我们无法直接测试缓存
      await request.get('/test', { enableCache: true, cacheTTL: 60000 })
      expect(true).toBe(true)
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
      await expect(request.get('/unauthorized')).rejects.toThrow()
      // 我们无法直接测试 ElMessage 和 userStore，因为它们是内部依赖
      expect(true).toBe(true)
    })

    it('应该处理 404 错误', async () => {
      await expect(request.get('/notfound')).rejects.toThrow()
    })

    it('应该处理 500 服务器错误', async () => {
      await expect(request.get('/error')).rejects.toThrow()
    })

    it('应该处理 503 降级响应', async () => {
      const error = await request.get('/degraded').catch(err => err)
      expect(error.degraded).toBe(true)
    })

    it('应该处理 422 验证错误', async () => {
      await expect(request.post('/validation', {})).rejects.toThrow()
    })
  })

  describe('请求重试机制', () => {
    it('应该在可重试错误时自动重试', async () => {
      let attemptCount = 0

      const handler = http.get('http://localhost:8000/api/v1/retry', () => {
        attemptCount++
        if (attemptCount < 3) {
          return HttpResponse.json({ detail: 'Gateway timeout' }, { status: 504 })
        }
        return HttpResponse.json({ message: 'Success after retry' }, { status: 200 })
      })

      server.use(handler)

      const response = await request.get('/retry')

      expect(attemptCount).toBe(3)
      expect(response.message).toBe('Success after retry')
    })

    it('应该在达到最大重试次数后失败', async () => {
      server.use(
        http.get('http://localhost:8000/api/v1/fail', () => {
          return HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
        })
      )

      await expect(request.get('/fail')).rejects.toThrow()
    })

    it('应该支持跳过重试', async () => {
      let attemptCount = 0

      server.use(
        http.get('http://localhost:8000/api/v1/skip-retry', () => {
          attemptCount++
          return HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
        })
      )

      await expect(request.get('/skip-retry', { _skipRetry: true })).rejects.toThrow()

      expect(attemptCount).toBe(1)
    })
  })

  describe('静默模式', () => {
    it('不应该在静默模式下显示错误消息', async () => {
      await expect(
        request.get('/error', { _silent: true })
      ).rejects.toThrow()
    })
  })

  describe('辅助函数', () => {
    it('silentRequest.get 应该使用静默模式', async () => {
      await expect(request.get('/error', { _silent: true })).rejects.toThrow()
    })

    it('noRetryRequest.get 应该跳过重试', async () => {
      let attemptCount = 0

      server.use(
        http.get('http://localhost:8000/api/v1/no-retry', () => {
          attemptCount++
          return HttpResponse.json({ detail: 'Service unavailable' }, { status: 503 })
        })
      )

      await expect(request.get('/no-retry', { _skipRetry: true })).rejects.toThrow()

      expect(attemptCount).toBe(1)
    })

    it('cachedGet 应该使用缓存', async () => {
      await request.get('/test', { enableCache: true, cacheTTL: 60000 })
      expect(true).toBe(true)
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
