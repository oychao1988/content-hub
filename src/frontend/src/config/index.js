// 应用配置
export default {
  // API 基础地址
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:18010',

  // API 版本（注意：不包含 /api 前缀，因为 VITE_API_BASE_URL 已经包含了）
  apiVersion: '/v1',

  // 请求超时时间（毫秒）
  timeout: 30000,

  // Token 存储键
  tokenKey: 'auth_token',

  // 分页配置
  pageSize: 20,
  pageSizes: [10, 20, 50, 100],

  // 上传配置
  uploadMaxSize: 5 * 1024 * 1024, // 5MB
  uploadAllowedTypes: ['image/jpeg', 'image/png', 'image/gif'],

  // 刷新令牌提前时间（毫秒）
  tokenRefreshThreshold: 5 * 60 * 1000 // 5分钟
}
