import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/modules/user'
import { useCacheStore } from '../stores/modules/cache'
import config from '../config'
import errorHandler from './errorHandler'
import Cache from './cache'

// 创建 axios 实例
const request = axios.create({
  baseURL: config.apiBaseUrl + config.apiVersion,
  timeout: config.timeout,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求重试配置
const MAX_RETRY_TIMES = 2
const RETRY_DELAY = 1000 // 1秒

/**
 * 延迟函数
 * @param {number} ms - 延迟毫秒数
 */
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

/**
 * 生成请求 ID
 */
function generateRequestId() {
  return `req_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}

/**
 * 请求拦截器
 */
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()

    // 添加认证 token
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }

    // 添加请求 ID（用于追踪）
    const requestId = generateRequestId()
    config.headers['X-Request-ID'] = requestId

    config.metadata = {
      startTime: new Date(),
      retryCount: 0,
      requestId: requestId
    }

    return config
  },
  (error) => {
    console.error('请求配置错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 */
request.interceptors.response.use(
  (response) => {
    // 记录请求耗时
    const endTime = new Date()
    const startTime = response.config.metadata?.startTime
    if (startTime) {
      const duration = endTime - startTime
      if (duration > 3000) {
        console.warn(`慢请求警告: ${response.config.url} 耗时 ${duration}ms`)
      }
    }

    // 如果是 GET 请求且启用了缓存，存入缓存
    if (response.config.method === 'get' && response.config.enableCache) {
      const cacheStore = useCacheStore()
      const cacheKey = response.config.url
      const cacheParams = response.config.params || {}
      const cacheTTL = response.config.cacheTTL || 5 * 60 * 1000 // 默认5分钟

      cacheStore.set(cacheKey, cacheParams, response.data, cacheTTL)
    }

    // 返回标准化的响应数据
    return response.data
  },
  async (error) => {
    const originalRequest = error.config

    // 提取错误信息
    const errorInfo = errorHandler.extractAxiosError(error)
    const { status, data, message, degraded } = errorInfo

    // 如果是降级响应，显示警告而不是错误
    if (degraded) {
      ElMessage.warning(message)
      return Promise.reject({
        ...error,
        handled: true,
        userMessage: message,
        degraded: true
      })
    }

    // 判断是否需要重新登录
    if (errorHandler.shouldLogout(status, data)) {
      ElMessage.error('登录已过期，请重新登录')

      const userStore = useUserStore()
      await userStore.logout()

      // 跳转到登录页
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }

      return Promise.reject(error)
    }

    // 判断是否可重试
    const isRetryable = errorHandler.isRetryable(status, data)
    const retryCount = originalRequest.metadata?.retryCount || 0

    if (isRetryable && retryCount < MAX_RETRY_TIMES && !originalRequest._skipRetry) {
      // 增加重试计数
      originalRequest.metadata = originalRequest.metadata || {}
      originalRequest.metadata.retryCount = retryCount + 1

      console.warn(
        `请求失败，正在重试 (${retryCount + 1}/${MAX_RETRY_TIMES}):`,
        originalRequest.url
      )

      // 指数退避
      await delay(RETRY_DELAY * Math.pow(2, retryCount))

      // 重新发送请求
      return request(originalRequest)
    }

    // 处理验证错误（422）
    if (status === 422) {
      let validationMessage = '输入数据验证失败'

      // 如果有错误详情，格式化显示
      if (data?.error?.details) {
        validationMessage = errorHandler.handleValidationError(data.error.details)
      } else if (data?.detail) {
        // 兼容旧的 FastAPI 验证错误格式
        if (Array.isArray(data.detail)) {
          const errors = {}
          data.detail.forEach(err => {
            const field = err.loc?.[err.loc.length - 1] || 'unknown'
            errors[field] = err.msg
          })
          validationMessage = errorHandler.handleValidationError(errors)
        } else {
          validationMessage = data.detail
        }
      } else if (data?.error?.message) {
        validationMessage = data.error.message
      }

      ElMessage.error(validationMessage)
      return Promise.reject(error)
    }

    // 显示错误提示（根据错误类型）
    let errorMessage = message

    // 如果是验证错误，使用详情信息
    if (data?.error?.code === 'VALIDATION_ERROR' && data?.error?.details) {
      errorMessage = errorHandler.handleValidationError(data.error.details)
    }

    // 根据配置决定是否显示错误消息
    if (!originalRequest._silent) {
      ElMessage.error(errorMessage)
    }

    // 记录错误日志
    console.error('API 请求失败:', {
      url: originalRequest.url,
      method: originalRequest.method,
      status,
      data,
      message,
      requestId: data?.requestId || error.response?.headers?.['x-request-id'] || originalRequest.metadata?.requestId || 'N/A',
      processTime: error.response?.headers?.['x-process-time'] || 'N/A'
    })

    return Promise.reject({
      ...error,
      handled: true,
      userMessage: errorMessage
    })
  }
)

/**
 * 包装请求方法，支持静默模式
 * @param {Function} requestFn - 请求函数
 * @param {Object} options - 选项
 * @param {boolean} options.silent - 是否静默（不显示错误提示）
 * @param {boolean} options.skipRetry - 是否跳过重试
 */
export function withOptions(requestFn, options = {}) {
  return function(...args) {
    const config = args[args.length - 1] || {}

    if (options.silent) {
      config._silent = true
    }

    if (options.skipRetry) {
      config._skipRetry = true
    }

    args[args.length - 1] = config
    return requestFn.apply(this, args)
  }
}

/**
 * 导出带有常用选项的请求方法
 */
export const silentRequest = {
  get: (url, config) => request.get(url, { ...config, _silent: true }),
  post: (url, data, config) => request.post(url, data, { ...config, _silent: true }),
  put: (url, data, config) => request.put(url, data, { ...config, _silent: true }),
  delete: (url, config) => request.delete(url, { ...config, _silent: true })
}

export const noRetryRequest = {
  get: (url, config) => request.get(url, { ...config, _skipRetry: true }),
  post: (url, data, config) => request.post(url, data, { ...config, _skipRetry: true }),
  put: (url, data, config) => request.put(url, data, { ...config, _skipRetry: true }),
  delete: (url, config) => request.delete(url, { ...config, _skipRetry: true })
}

/**
 * 带缓存的 GET 请求
 * @param {string} url - 请求URL
 * @param {Object} config - 请求配置
 * @param {number} cacheTTL - 缓存时长（毫秒），默认5分钟
 */
export function cachedGet(url, config = {}, cacheTTL = 5 * 60 * 1000) {
  const cacheStore = useCacheStore()
  const params = config.params || {}

  // 尝试从缓存获取
  const cachedData = cacheStore.get(url, params)
  if (cachedData !== null) {
    return Promise.resolve(cachedData)
  }

  // 缓存未命中，发起请求并启用缓存
  return request.get(url, {
    ...config,
    enableCache: true,
    cacheTTL
  })
}

export default request

// 导出带缓存的请求方法
export const cachedRequest = {
  get: cachedGet,
  post: (url, data, config) => request.post(url, data, config),
  put: (url, data, config) => request.put(url, data, config),
  delete: (url, config) => request.delete(url, config)
}
