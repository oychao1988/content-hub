/**
 * API 响应缓存 Store
 *
 * 提供 GET 请求的内存缓存功能
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCacheStore = defineStore('cache', () => {
  // 缓存存储
  const cache = ref(new Map())

  // 缓存统计
  const stats = ref({
    hits: 0,
    misses: 0,
    sets: 0,
    deletes: 0
  })

  // 计算属性
  const size = computed(() => cache.value.size)
  const hitRate = computed(() => {
    const total = stats.value.hits + stats.value.misses
    return total > 0 ? ((stats.value.hits / total) * 100).toFixed(2) : '0.00'
  })

  /**
   * 生成缓存键
   * @param {string} url - 请求URL
   * @param {Object} params - 请求参数
   * @returns {string} 缓存键
   */
  function generateKey(url, params = {}) {
    // 过滤掉 undefined 和 null 的参数
    const filteredParams = Object.keys(params)
      .filter(key => params[key] !== undefined && params[key] !== null)
      .sort()
      .map(key => `${key}=${JSON.stringify(params[key])}`)
      .join('&')

    return filteredParams ? `${url}?${filteredParams}` : url
  }

  /**
   * 获取缓存数据
   * @param {string} url - 请求URL
   * @param {Object} params - 请求参数
   * @returns {any|null} 缓存的数据或null
   */
  function get(url, params = {}) {
    const key = generateKey(url, params)
    const item = cache.value.get(key)

    if (!item) {
      stats.value.misses++
      return null
    }

    // 检查是否过期
    if (item.expireTime && Date.now() > item.expireTime) {
      cache.value.delete(key)
      stats.value.misses++
      return null
    }

    stats.value.hits++
    console.debug(`[缓存命中] ${key}`)
    return item.data
  }

  /**
   * 设置缓存数据
   * @param {string} url - 请求URL
   * @param {Object} params - 请求参数
   * @param {any} data - 要缓存的数据
   * @param {number} ttl - 过期时间（毫秒）
   */
  function set(url, params = {}, data, ttl = 5 * 60 * 1000) {
    const key = generateKey(url, params)
    const expireTime = ttl ? Date.now() + ttl : null

    cache.value.set(key, {
      data,
      expireTime,
      createTime: Date.now()
    })

    stats.value.sets++
    console.debug(`[缓存设置] ${key} (TTL: ${ttl}ms)`)
  }

  /**
   * 删除缓存
   * @param {string} url - 请求URL（可选）
   * @param {Object} params - 请求参数（可选）
   */
  function remove(url, params = {}) {
    if (!url) {
      // 清空所有缓存
      const count = cache.value.size
      cache.value.clear()
      stats.value.deletes += count
      console.info(`[缓存清空] 已清空 ${count} 个缓存项`)
      return
    }

    const key = generateKey(url, params)
    const deleted = cache.value.delete(key)
    if (deleted) {
      stats.value.deletes++
      console.debug(`[缓存删除] ${key}`)
    }
  }

  /**
   * 根据URL模式删除缓存
   * @param {string} pattern - URL模式（支持通配符）
   */
  function removePattern(pattern) {
    let count = 0
    const regex = new RegExp('^' + pattern.replace(/\*/g, '.*'))

    for (const key of cache.value.keys()) {
      if (regex.test(key)) {
        cache.value.delete(key)
        count++
      }
    }

    if (count > 0) {
      stats.value.deletes += count
      console.info(`[缓存批量删除] ${pattern} (${count} 个缓存项)`)
    }
  }

  /**
   * 清理过期的缓存
   */
  function cleanup() {
    const now = Date.now()
    let count = 0

    for (const [key, item] of cache.value.entries()) {
      if (item.expireTime && now > item.expireTime) {
        cache.value.delete(key)
        count++
      }
    }

    if (count > 0) {
      console.info(`[缓存清理] 清理了 ${count} 个过期缓存项`)
    }
  }

  /**
   * 获取缓存统计信息
   */
  function getStats() {
    return {
      ...stats.value,
      size: size.value,
      hitRate: hitRate.value
    }
  }

  /**
   * 重置缓存统计
   */
  function resetStats() {
    stats.value = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0
    }
    console.info('[缓存统计] 统计信息已重置')
  }

  /**
   * 带缓存的 GET 请求包装器
   * @param {Function} requestFn - 请求函数
   * @param {string} url - 请求URL
   * @param {Object} config - 请求配置
   * @param {number} ttl - 缓存时间（毫秒）
   */
  async function cachedGet(requestFn, url, config = {}, ttl = 5 * 60 * 1000) {
    const params = config.params || {}

    // 尝试从缓存获取
    const cachedData = get(url, params)
    if (cachedData !== null) {
      return cachedData
    }

    // 缓存未命中，发起请求
    try {
      const response = await requestFn(url, config)
      set(url, params, response, ttl)
      return response
    } catch (error) {
      console.error(`[缓存请求失败] ${url}`, error)
      throw error
    }
  }

  return {
    // 状态
    cache,
    stats,
    // 计算属性
    size,
    hitRate,
    // 方法
    get,
    set,
    remove,
    removePattern,
    cleanup,
    getStats,
    resetStats,
    cachedGet,
    generateKey
  }
})
