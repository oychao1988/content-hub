/**
 * 缓存管理 API
 */
import request from '../../utils/request'

/**
 * 获取缓存统计信息
 */
export const getCacheStats = () => {
  return request({
    url: '/dashboard/cache-stats',
    method: 'get'
  })
}

/**
 * 重置缓存统计
 */
export const resetCacheStats = () => {
  return request({
    url: '/dashboard/cache-stats/reset',
    method: 'post'
  })
}

/**
 * 清空所有缓存
 */
export const clearCache = () => {
  return request({
    url: '/dashboard/cache/clear',
    method: 'post'
  })
}

/**
 * 清理过期缓存
 */
export const cleanupCache = () => {
  return request({
    url: '/dashboard/cache/cleanup',
    method: 'post'
  })
}
