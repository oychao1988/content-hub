/**
 * 统一错误处理工具
 * 提供友好的错误提示和错误码映射
 */

/**
 * 错误码常量
 */
export const ErrorCode = {
  // 通用错误 (1xxx)
  INTERNAL_SERVER_ERROR: 'INTERNAL_SERVER_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  NOT_FOUND: 'NOT_FOUND',
  UNAUTHORIZED: 'UNAUTHORIZED',
  FORBIDDEN: 'FORBIDDEN',
  METHOD_NOT_ALLOWED: 'METHOD_NOT_ALLOWED',
  RATE_LIMIT_EXCEEDED: 'RATE_LIMIT_EXCEEDED',

  // 认证授权错误 (2xxx)
  TOKEN_INVALID: 'TOKEN_INVALID',
  TOKEN_EXPIRED: 'TOKEN_EXPIRED',
  CREDENTIALS_INVALID: 'CREDENTIALS_INVALID',
  PERMISSION_DENIED: 'PERMISSION_DENIED',

  // 资源错误 (3xxx)
  RESOURCE_NOT_FOUND: 'RESOURCE_NOT_FOUND',
  RESOURCE_ALREADY_EXISTS: 'RESOURCE_ALREADY_EXISTS',
  RESOURCE_CONFLICT: 'RESOURCE_CONFLICT',
  RESOURCE_LOCKED: 'RESOURCE_LOCKED',

  // 业务逻辑错误 (4xxx)
  BUSINESS_ERROR: 'BUSINESS_ERROR',
  OPERATION_FAILED: 'OPERATION_FAILED',
  INVALID_STATE: 'INVALID_STATE',
  CONSTRAINT_VIOLATION: 'CONSTRAINT_VIOLATION',

  // 外部服务错误 (5xxx)
  EXTERNAL_SERVICE_ERROR: 'EXTERNAL_SERVICE_ERROR',
  EXTERNAL_SERVICE_TIMEOUT: 'EXTERNAL_SERVICE_TIMEOUT',
  EXTERNAL_SERVICE_UNAVAILABLE: 'EXTERNAL_SERVICE_UNAVAILABLE',

  // Content-Creator 错误 (51xx)
  CREATOR_CLI_NOT_FOUND: 'CREATOR_CLI_NOT_FOUND',
  CREATOR_EXECUTION_FAILED: 'CREATOR_EXECUTION_FAILED',
  CREATOR_TIMEOUT: 'CREATOR_TIMEOUT',
  CREATOR_INVALID_RESPONSE: 'CREATOR_INVALID_RESPONSE',

  // Content-Publisher 错误 (52xx)
  PUBLISHER_API_ERROR: 'PUBLISHER_API_ERROR',
  PUBLISHER_TIMEOUT: 'PUBLISHER_TIMEOUT',
  PUBLISHER_UNAUTHORIZED: 'PUBLISHER_UNAUTHORIZED',
  PUBLISHER_INVALID_RESPONSE: 'PUBLISHER_INVALID_RESPONSE',

  // Tavily API 错误 (53xx)
  TAVILY_API_ERROR: 'TAVILY_API_ERROR',
  TAVILY_QUOTA_EXCEEDED: 'TAVILY_QUOTA_EXCEEDED',
  TAVILY_INVALID_KEY: 'TAVILY_INVALID_KEY',

  // 数据库错误 (6xxx)
  DATABASE_ERROR: 'DATABASE_ERROR',
  DATABASE_CONNECTION_ERROR: 'DATABASE_CONNECTION_ERROR',
  DATABASE_QUERY_ERROR: 'DATABASE_QUERY_ERROR',

  // 文件操作错误 (7xxx)
  FILE_NOT_FOUND: 'FILE_NOT_FOUND',
  FILE_UPLOAD_FAILED: 'FILE_UPLOAD_FAILED',
  FILE_SIZE_EXCEEDED: 'FILE_SIZE_EXCEEDED',
  INVALID_FILE_TYPE: 'INVALID_FILE_TYPE',

  // 降级服务标识
  SERVICE_DEGRADED: 'SERVICE_DEGRADED'
}

/**
 * 错误码到友好提示的映射
 */
const errorMessages = {
  [ErrorCode.INTERNAL_SERVER_ERROR]: '服务器内部错误，请稍后重试',
  [ErrorCode.VALIDATION_ERROR]: '输入数据格式不正确',
  [ErrorCode.NOT_FOUND]: '请求的资源不存在',
  [ErrorCode.UNAUTHORIZED]: '未授权访问',
  [ErrorCode.FORBIDDEN]: '没有权限访问此资源',
  [ErrorCode.METHOD_NOT_ALLOWED]: '请求方法不被允许',
  [ErrorCode.RATE_LIMIT_EXCEEDED]: '请求过于频繁，请稍后再试',

  [ErrorCode.TOKEN_INVALID]: '登录信息无效，请重新登录',
  [ErrorCode.TOKEN_EXPIRED]: '登录已过期，请重新登录',
  [ErrorCode.CREDENTIALS_INVALID]: '用户名或密码错误',
  [ErrorCode.PERMISSION_DENIED]: '您没有权限执行此操作',

  [ErrorCode.RESOURCE_NOT_FOUND]: '请求的资源不存在',
  [ErrorCode.RESOURCE_ALREADY_EXISTS]: '资源已存在',
  [ErrorCode.RESOURCE_CONFLICT]: '资源冲突',
  [ErrorCode.RESOURCE_LOCKED]: '资源已被锁定',

  [ErrorCode.BUSINESS_ERROR]: '业务处理失败',
  [ErrorCode.OPERATION_FAILED]: '操作失败',
  [ErrorCode.INVALID_STATE]: '当前状态不允许此操作',
  [ErrorCode.CONSTRAINT_VIOLATION]: '违反了业务约束',

  [ErrorCode.EXTERNAL_SERVICE_ERROR]: '外部服务调用失败',
  [ErrorCode.EXTERNAL_SERVICE_TIMEOUT]: '外部服务响应超时',
  [ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE]: '外部服务暂时不可用',

  [ErrorCode.CREATOR_CLI_NOT_FOUND]: '内容生成工具未找到，请联系管理员',
  [ErrorCode.CREATOR_EXECUTION_FAILED]: '内容生成失败',
  [ErrorCode.CREATOR_TIMEOUT]: '内容生成超时，请稍后重试',
  [ErrorCode.CREATOR_INVALID_RESPONSE]: '内容生成返回了无效的数据',

  [ErrorCode.PUBLISHER_API_ERROR]: '发布服务调用失败',
  [ErrorCode.PUBLISHER_TIMEOUT]: '发布服务响应超时，请稍后重试',
  [ErrorCode.PUBLISHER_UNAUTHORIZED]: '发布服务认证失败，请联系管理员',
  [ErrorCode.PUBLISHER_INVALID_RESPONSE]: '发布服务返回了无效的数据',

  [ErrorCode.TAVILY_API_ERROR]: '选题搜索服务调用失败',
  [ErrorCode.TAVILY_QUOTA_EXCEEDED]: '选题搜索次数已达上限',
  [ErrorCode.TAVILY_INVALID_KEY]: '选题搜索服务配置错误',

  [ErrorCode.DATABASE_ERROR]: '数据库错误',
  [ErrorCode.DATABASE_CONNECTION_ERROR]: '数据库连接失败',
  [ErrorCode.DATABASE_QUERY_ERROR]: '数据查询失败',

  [ErrorCode.FILE_NOT_FOUND]: '文件不存在',
  [ErrorCode.FILE_UPLOAD_FAILED]: '文件上传失败',
  [ErrorCode.FILE_SIZE_EXCEEDED]: '文件大小超出限制',
  [ErrorCode.INVALID_FILE_TYPE]: '不支持的文件类型',

  [ErrorCode.SERVICE_DEGRADED]: '服务当前处于降级模式，部分功能可能受限'
}

/**
 * HTTP 状态码到友好提示的映射
 */
const httpStatusMessages = {
  400: '请求参数错误',
  401: '未授权，请登录',
  403: '拒绝访问',
  404: '请求的资源不存在',
  405: '请求方法不允许',
  408: '请求超时',
  422: '数据验证失败',
  429: '请求过于频繁',
  500: '服务器内部错误',
  502: '网关错误',
  503: '服务不可用',
  504: '网关超时'
}

/**
 * 错误处理器类
 */
class ErrorHandler {
  /**
   * 获取友好的错误提示
   * @param {Object} error - 错误对象
   * @param {string} error.code - 错误码
   * @param {string} error.message - 错误消息
   * @param {Object} error.details - 错误详情
   * @returns {string} 友好的错误提示
   */
  getFriendlyMessage(error) {
    if (!error) {
      return '未知错误'
    }

    // 优先使用错误码映射
    if (error.code && errorMessages[error.code]) {
      return errorMessages[error.code]
    }

    // 其次使用错误消息
    if (error.message) {
      return error.message
    }

    // 最后返回通用错误
    return '操作失败，请稍后重试'
  }

  /**
   * 处理 API 错误响应
   * @param {Object} response - 错误响应对象
   * @param {number} status - HTTP 状态码
   * @returns {string} 友好的错误提示
   */
  handleApiResponse(response, status) {
    // 如果响应中有 error 字段
    if (response && response.error) {
      return this.getFriendlyMessage(response.error)
    }

    // 如果响应中有 message 字段
    if (response && response.message) {
      return response.message
    }

    // 使用 HTTP 状态码映射
    if (status && httpStatusMessages[status]) {
      return httpStatusMessages[status]
    }

    return this.getFriendlyMessage({})
  }

  /**
   * 处理网络错误
   * @param {Error} error - 网络错误对象
   * @returns {string} 友好的错误提示
   */
  handleNetworkError(error) {
    if (error.code === 'ECONNABORTED') {
      return '请求超时，请检查网络连接'
    }

    if (error.message === 'Network Error') {
      return '网络错误，请检查网络连接'
    }

    return error.message || '网络请求失败'
  }

  /**
   * 处理验证错误
   * @param {Object} details - 验证错误详情
   * @returns {string} 友好的错误提示
   */
  handleValidationError(details) {
    if (!details || typeof details !== 'object') {
      return '输入数据验证失败'
    }

    // 将所有字段错误拼接成字符串
    const errors = Object.entries(details).map(([field, message]) => {
      // 字段名转换（驼峰转下划线并转中文）
      const fieldName = this.translateFieldName(field)
      return `${fieldName}: ${message}`
    })

    return errors.join('; ')
  }

  /**
   * 字段名翻译
   * @param {string} field - 字段名
   * @returns {string} 中文名称
   */
  translateFieldName(field) {
    const fieldMap = {
      username: '用户名',
      password: '密码',
      email: '邮箱',
      phone: '手机号',
      title: '标题',
      content: '内容',
      topic: '选题',
      category: '分类',
      platform: '平台',
      accountId: '账号',
      publishTime: '发布时间',
      status: '状态'
    }

    return fieldMap[field] || field
  }

  /**
   * 判断错误是否需要重新登录
   * @param {number} status - HTTP 状态码
   * @param {Object} response - 响应对象
   * @param {string} method - HTTP 方法
   * @returns {boolean} 是否需要重新登录
   */
  shouldLogout(status, response, method = null) {
    // 对于 DELETE 请求的 401 错误，不自动登出
    // 因为可能是服务端临时错误，不应该强制用户重新登录
    if (status === 401 && method === 'delete') {
      return false
    }

    // 401 未授权（其他方法）
    if (status === 401) {
      return true
    }

    // TOKEN_EXPIRED 或 TOKEN_INVALID 错误码
    if (response && response.error) {
      const { code } = response.error
      return code === ErrorCode.TOKEN_EXPIRED || code === ErrorCode.TOKEN_INVALID
    }

    return false
  }

  /**
   * 判断错误是否可重试
   * @param {number} status - HTTP 状态码
   * @param {Object} response - 响应对象
   * @returns {boolean} 是否可重试
   */
  isRetryable(status, response) {
    // 某些 HTTP 状态码可重试
    const retryableStatusCodes = [408, 429, 500, 502, 503, 504]
    if (retryableStatusCodes.includes(status)) {
      return true
    }

    // 某些错误码可重试
    if (response && response.error) {
      const { code } = response.error
      return [
        ErrorCode.EXTERNAL_SERVICE_TIMEOUT,
        ErrorCode.EXTERNAL_SERVICE_UNAVAILABLE,
        ErrorCode.CREATOR_TIMEOUT,
        ErrorCode.PUBLISHER_TIMEOUT
      ].includes(code)
    }

    return false
  }

  /**
   * 格式化错误详情用于日志
   * @param {Object} error - 错误对象
   * @returns {Object} 格式化后的错误详情
   */
  formatErrorForLog(error) {
    return {
      code: error.code,
      message: error.message,
      details: error.details,
      requestId: error.requestId,
      timestamp: new Date().toISOString()
    }
  }

  /**
   * 检查是否为降级响应
   * @param {Object} response - 响应对象
   * @returns {boolean} 是否为降级响应
   */
  isDegradedResponse(response) {
    return response && response.degraded === true
  }

  /**
   * 处理降级响应
   * @param {Object} response - 降级响应对象
   * @returns {string} 友好的提示信息
   */
  handleDegradedResponse(response) {
    if (response.message) {
      return response.message
    }
    return '服务当前繁忙，已将您的请求加入队列，请稍后查看'
  }

  /**
   * 从 Axios 错误中提取错误信息
   * @param {Error} error - Axios 错误对象
   * @returns {Object} 提取的错误信息
   */
  extractAxiosError(error) {
    if (error.response) {
      // 服务器返回了错误响应
      const { status, data } = error.response

      // 检查是否为降级响应
      if (this.isDegradedResponse(data)) {
        return {
          status,
          data,
          message: this.handleDegradedResponse(data),
          degraded: true
        }
      }

      return {
        status,
        data,
        message: this.handleApiResponse(data, status)
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      return {
        status: null,
        data: null,
        message: this.handleNetworkError(error)
      }
    } else {
      // 请求配置错误
      return {
        status: null,
        data: null,
        message: error.message || '请求配置错误'
      }
    }
  }
}

// 创建单例实例
const errorHandler = new ErrorHandler()

export default errorHandler
