import request, { cachedGet } from '../../utils/request'
import { useCacheStore } from '../../stores/modules/cache'

// 获取平台列表（带缓存，30分钟）
export const getPlatforms = (params) => {
  return cachedGet('/platforms/', { params }, 30 * 60 * 1000)
}

// 获取平台详情（带缓存，30分钟）
export const getPlatform = (id) => {
  return cachedGet(`/platforms/${id}`, {}, 30 * 60 * 1000)
}

// 创建平台（创建后清除缓存）
export const createPlatform = (data) => {
  return request({
    url: '/platforms/',
    method: 'post',
    data
  }).then(response => {
    // 清除平台缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/platforms/')
    return response
  })
}

// 更新平台（更新后清除缓存）
export const updatePlatform = (id, data) => {
  return request({
    url: `/platforms/${id}`,
    method: 'put',
    data
  }).then(response => {
    // 清除平台缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/platforms/')
    return response
  })
}

// 删除平台（删除后清除缓存）
export const deletePlatform = (id) => {
  return request({
    url: `/platforms/${id}`,
    method: 'delete'
  }).then(response => {
    // 清除平台缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/platforms/')
    return response
  })
}

// 获取平台配置
export const getPlatformConfig = (id) => {
  return request({
    url: `/platforms/${id}/config`,
    method: 'get'
  })
}
