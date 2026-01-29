import request, { cachedGet } from '../../utils/request'
import { useCacheStore } from '../../stores/modules/cache'

// 获取账号列表（带缓存，5分钟）
export const getAccounts = (params) => {
  return cachedGet('/accounts/', { params }, 5 * 60 * 1000)
}

// 获取账号详情（带缓存，5分钟）
export const getAccount = (id) => {
  return cachedGet(`/accounts/${id}`, {}, 5 * 60 * 1000)
}

// 创建账号（创建后清除缓存）
export const createAccount = (data) => {
  return request({
    url: '/accounts/',
    method: 'post',
    data
  }).then(response => {
    // 清除账号列表缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/accounts/')
    return response
  })
}

// 更新账号（更新后清除缓存）
export const updateAccount = (id, data) => {
  return request({
    url: `/accounts/${id}`,
    method: 'put',
    data
  }).then(response => {
    // 清除账号列表和详情缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/accounts/')
    return response
  })
}

// 删除账号（删除后清除缓存）
export const deleteAccount = (id) => {
  return request({
    url: `/accounts/${id}`,
    method: 'delete'
  }).then(response => {
    // 清除账号列表和详情缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/accounts/')
    return response
  })
}

// 批量删除账号（删除后清除缓存）
export const batchDeleteAccounts = (ids) => {
  return request({
    url: '/accounts/batch',
    method: 'delete',
    data: { ids }
  }).then(response => {
    // 清除账号列表缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/accounts/')
    return response
  })
}

// 同步账号状态
export const syncAccount = (id) => {
  return request({
    url: `/accounts/${id}/sync`,
    method: 'post'
  })
}
