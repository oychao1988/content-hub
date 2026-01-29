import request, { cachedGet } from '../../utils/request'
import { useCacheStore } from '../../stores/modules/cache'

// ============= 写作风格相关 API =============

// 获取写作风格列表（带缓存，1小时）
export const getWritingStyles = (params) => {
  return cachedGet('/config/writing-styles', { params }, 60 * 60 * 1000)
}

// 获取写作风格详情（带缓存，1小时）
export const getWritingStyle = (id) => {
  return cachedGet(`/config/writing-styles/${id}`, {}, 60 * 60 * 1000)
}

// 创建写作风格（创建后清除缓存）
export const createWritingStyle = (data) => {
  return request({
    url: '/config/writing-styles',
    method: 'post',
    data
  }).then(response => {
    // 清除写作风格缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/config/writing-styles')
    return response
  })
}

// 更新写作风格（更新后清除缓存）
export const updateWritingStyle = (id, data) => {
  return request({
    url: `/config/writing-styles/${id}`,
    method: 'put',
    data
  }).then(response => {
    // 清除写作风格缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/config/writing-styles')
    return response
  })
}

// 删除写作风格（删除后清除缓存）
export const deleteWritingStyle = (id) => {
  return request({
    url: `/config/writing-styles/${id}`,
    method: 'delete'
  }).then(response => {
    // 清除写作风格缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/config/writing-styles')
    return response
  })
}

// ============= 内容主题相关 API =============

// 获取内容主题列表（带缓存，1小时）
export const getContentThemes = (params) => {
  return cachedGet('/config/content-themes', { params }, 60 * 60 * 1000)
}

// 获取内容主题详情（带缓存，1小时）
export const getContentTheme = (id) => {
  return cachedGet(`/config/content-themes/${id}`, {}, 60 * 60 * 1000)
}

// 创建内容主题（创建后清除缓存）
export const createContentTheme = (data) => {
  return request({
    url: '/config/content-themes',
    method: 'post',
    data
  }).then(response => {
    // 清除内容主题缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/config/content-themes')
    return response
  })
}

// 更新内容主题（更新后清除缓存）
export const updateContentTheme = (id, data) => {
  return request({
    url: `/config/content-themes/${id}`,
    method: 'put',
    data
  }).then(response => {
    // 清除内容主题缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/config/content-themes')
    return response
  })
}

// 删除内容主题（删除后清除缓存）
export const deleteContentTheme = (id) => {
  return request({
    url: `/config/content-themes/${id}`,
    method: 'delete'
  }).then(response => {
    // 清除内容主题缓存
    const cacheStore = useCacheStore()
    cacheStore.removePattern('/config/content-themes')
    return response
  })
}
