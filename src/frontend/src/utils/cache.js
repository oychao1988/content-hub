/**
 * 统一缓存工具
 *
 * 封装 localStorage 和 sessionStorage，提供统一的缓存接口
 */

// ============================================================================
// 常量定义
// ============================================================================

const STORAGE_PREFIX = 'contenthub_'

// 缓存键前缀
const CACHE_KEYS = {
  // 用户相关
  USER_INFO: 'user_info',
  USER_PERMISSIONS: 'user_permissions',

  // 配置相关
  WRITING_STYLES: 'writing_styles',
  CONTENT_THEMES: 'content_themes',
  PLATFORMS: 'platforms',

  // 账号相关
  ACCOUNTS: 'accounts',

  // 内容相关
  CONTENT_LIST: 'content_list',

  // 其他
  SETTINGS: 'settings'
}

// 缓存时长（毫秒）
const CACHE_TTL = {
  USER_INFO: 30 * 60 * 1000,      // 30分钟
  USER_PERMISSIONS: 30 * 60 * 1000, // 30分钟
  WRITING_STYLES: 60 * 60 * 1000,   // 1小时
  CONTENT_THEMES: 60 * 60 * 1000,   // 1小时
  PLATFORMS: 30 * 60 * 1000,        // 30分钟
  ACCOUNTS: 5 * 60 * 1000,          // 5分钟
  CONTENT_LIST: 2 * 60 * 1000,      // 2分钟
  SETTINGS: 24 * 60 * 60 * 1000     // 24小时
}

// ============================================================================
// 工具函数
// ============================================================================

/**
 * 生成完整的缓存键
 * @param {string} key - 缓存键
 * @returns {string} 完整的缓存键
 */
function getFullKey(key) {
  return `${STORAGE_PREFIX}${key}`
}

/**
 * 序列化数据
 * @param {any} data - 要序列化的数据
 * @returns {string} 序列化后的字符串
 */
function serialize(data) {
  try {
    return JSON.stringify({
      data,
      timestamp: Date.now()
    })
  } catch (error) {
    console.error('缓存序列化失败:', error)
    return null
  }
}

/**
 * 反序列化数据
 * @param {string} value - 序列化的字符串
 * @param {number} ttl - 缓存时长（毫秒）
 * @returns {any|null} 反序列化后的数据或null
 */
function deserialize(value, ttl) {
  try {
    const parsed = JSON.parse(value)
    const { data, timestamp } = parsed

    // 检查是否过期
    if (ttl && Date.now() - timestamp > ttl) {
      return null
    }

    return data
  } catch (error) {
    console.error('缓存反序列化失败:', error)
    return null
  }
}

// ============================================================================
// localStorage 封装
// ============================================================================

const LocalStorage = {
  /**
   * 设置缓存
   * @param {string} key - 缓存键
   * @param {any} value - 缓存值
   * @param {number} ttl - 过期时间（毫秒），可选
   */
  set(key, value, ttl) {
    try {
      const fullKey = getFullKey(key)
      const serialized = serialize(value)

      if (serialized) {
        localStorage.setItem(fullKey, serialized)

        // 如果有TTL，单独存储过期时间
        if (ttl) {
          const expireKey = `${fullKey}_expire`
          localStorage.setItem(expireKey, String(Date.now() + ttl))
        }

        console.debug(`[LocalStorage] 设置缓存: ${key}`)
      }
    } catch (error) {
      console.error('[LocalStorage] 设置缓存失败:', error)
    }
  },

  /**
   * 获取缓存
   * @param {string} key - 缓存键
   * @param {number} ttl - 过期时间（毫秒），可选
   * @returns {any|null} 缓存值或null
   */
  get(key, ttl) {
    try {
      const fullKey = getFullKey(key)
      const value = localStorage.getItem(fullKey)

      if (!value) {
        return null
      }

      // 检查是否过期
      if (ttl) {
        const expireKey = `${fullKey}_expire`
        const expireTime = localStorage.getItem(expireKey)

        if (expireTime && Date.now() > Number(expireTime)) {
          this.remove(key)
          return null
        }
      }

      const parsed = deserialize(value, ttl)
      if (parsed !== null) {
        console.debug(`[LocalStorage] 缓存命中: ${key}`)
      }

      return parsed
    } catch (error) {
      console.error('[LocalStorage] 获取缓存失败:', error)
      return null
    }
  },

  /**
   * 删除缓存
   * @param {string} key - 缓存键
   */
  remove(key) {
    try {
      const fullKey = getFullKey(key)
      localStorage.removeItem(fullKey)

      // 同时删除过期时间
      const expireKey = `${fullKey}_expire`
      localStorage.removeItem(expireKey)

      console.debug(`[LocalStorage] 删除缓存: ${key}`)
    } catch (error) {
      console.error('[LocalStorage] 删除缓存失败:', error)
    }
  },

  /**
   * 清空所有缓存
   */
  clear() {
    try {
      const keysToRemove = []

      // 找出所有带前缀的键
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith(STORAGE_PREFIX)) {
          keysToRemove.push(key)
        }
      }

      // 删除所有带前缀的键
      keysToRemove.forEach(key => localStorage.removeItem(key))

      console.info(`[LocalStorage] 清空了 ${keysToRemove.length} 个缓存项`)
    } catch (error) {
      console.error('[LocalStorage] 清空缓存失败:', error)
    }
  },

  /**
   * 检查缓存是否存在且未过期
   * @param {string} key - 缓存键
   * @param {number} ttl - 过期时间（毫秒）
   * @returns {boolean} 是否存在且未过期
   */
  has(key, ttl) {
    return this.get(key, ttl) !== null
  }
}

// ============================================================================
// sessionStorage 封装
// ============================================================================

const SessionStorage = {
  /**
   * 设置缓存
   * @param {string} key - 缓存键
   * @param {any} value - 缓存值
   * @param {number} ttl - 过期时间（毫秒），可选
   */
  set(key, value, ttl) {
    try {
      const fullKey = getFullKey(key)
      const serialized = serialize(value)

      if (serialized) {
        sessionStorage.setItem(fullKey, serialized)

        // 如果有TTL，单独存储过期时间
        if (ttl) {
          const expireKey = `${fullKey}_expire`
          sessionStorage.setItem(expireKey, String(Date.now() + ttl))
        }

        console.debug(`[SessionStorage] 设置缓存: ${key}`)
      }
    } catch (error) {
      console.error('[SessionStorage] 设置缓存失败:', error)
    }
  },

  /**
   * 获取缓存
   * @param {string} key - 缓存键
   * @param {number} ttl - 过期时间（毫秒），可选
   * @returns {any|null} 缓存值或null
   */
  get(key, ttl) {
    try {
      const fullKey = getFullKey(key)
      const value = sessionStorage.getItem(fullKey)

      if (!value) {
        return null
      }

      // 检查是否过期
      if (ttl) {
        const expireKey = `${fullKey}_expire`
        const expireTime = sessionStorage.getItem(expireKey)

        if (expireTime && Date.now() > Number(expireTime)) {
          this.remove(key)
          return null
        }
      }

      const parsed = deserialize(value, ttl)
      if (parsed !== null) {
        console.debug(`[SessionStorage] 缓存命中: ${key}`)
      }

      return parsed
    } catch (error) {
      console.error('[SessionStorage] 获取缓存失败:', error)
      return null
    }
  },

  /**
   * 删除缓存
   * @param {string} key - 缓存键
   */
  remove(key) {
    try {
      const fullKey = getFullKey(key)
      sessionStorage.removeItem(fullKey)

      // 同时删除过期时间
      const expireKey = `${fullKey}_expire`
      sessionStorage.removeItem(expireKey)

      console.debug(`[SessionStorage] 删除缓存: ${key}`)
    } catch (error) {
      console.error('[SessionStorage] 删除缓存失败:', error)
    }
  },

  /**
   * 清空所有缓存
   */
  clear() {
    try {
      const keysToRemove = []

      // 找出所有带前缀的键
      for (let i = 0; i < sessionStorage.length; i++) {
        const key = sessionStorage.key(i)
        if (key && key.startsWith(STORAGE_PREFIX)) {
          keysToRemove.push(key)
        }
      }

      // 删除所有带前缀的键
      keysToRemove.forEach(key => sessionStorage.removeItem(key))

      console.info(`[SessionStorage] 清空了 ${keysToRemove.length} 个缓存项`)
    } catch (error) {
      console.error('[SessionStorage] 清空缓存失败:', error)
    }
  },

  /**
   * 检查缓存是否存在且未过期
   * @param {string} key - 缓存键
   * @param {number} ttl - 过期时间（毫秒）
   * @returns {boolean} 是否存在且未过期
   */
  has(key, ttl) {
    return this.get(key, ttl) !== null
  }
}

// ============================================================================
// 统一缓存接口
// ============================================================================

const Cache = {
  // 导出缓存键常量
  CACHE_KEYS,
  CACHE_TTL,

  // localStorage 方法
  LocalStorage,

  // sessionStorage 方法
  SessionStorage,

  /**
   * 设置缓存（默认使用 localStorage）
   * @param {string} key - 缓存键
   * @param {any} value - 缓存值
   * @param {number} ttl - 过期时间（毫秒），可选
   * @param {boolean} useSession - 是否使用 sessionStorage，默认 false
   */
  set(key, value, ttl, useSession = false) {
    const storage = useSession ? SessionStorage : LocalStorage
    storage.set(key, value, ttl)
  },

  /**
   * 获取缓存（默认使用 localStorage）
   * @param {string} key - 缓存键
   * @param {number} ttl - 过期时间（毫秒），可选
   * @param {boolean} useSession - 是否使用 sessionStorage，默认 false
   * @returns {any|null} 缓存值或null
   */
  get(key, ttl, useSession = false) {
    const storage = useSession ? SessionStorage : LocalStorage
    return storage.get(key, ttl)
  },

  /**
   * 删除缓存（默认使用 localStorage）
   * @param {string} key - 缓存键
   * @param {boolean} useSession - 是否使用 sessionStorage，默认 false
   */
  remove(key, useSession = false) {
    const storage = useSession ? SessionStorage : LocalStorage
    storage.remove(key)
  },

  /**
   * 清空所有缓存
   */
  clear() {
    LocalStorage.clear()
    SessionStorage.clear()
  },

  /**
   * 清理过期的缓存
   */
  cleanup() {
    // localStorage 和 sessionStorage 会自动在 get 时清理过期数据
    // 这里只需要清理所有缓存，让下次 get 时自动判断
    console.info('[Cache] 缓存清理完成')
  },

  /**
   * 获取缓存大小信息
   * @returns {Object} 缓存大小信息
   */
  getSize() {
    const localCount = localStorage.length
    const sessionCount = sessionStorage.length

    // 估算大小（UTF-16 每个字符 2 字节）
    let localSize = 0
    let sessionSize = 0

    for (let i = 0; i < localCount; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith(STORAGE_PREFIX)) {
        localSize += key.length + (localStorage.getItem(key)?.length || 0)
      }
    }

    for (let i = 0; i < sessionCount; i++) {
      const key = sessionStorage.key(i)
      if (key && key.startsWith(STORAGE_PREFIX)) {
        sessionSize += key.length + (sessionStorage.getItem(key)?.length || 0)
      }
    }

    return {
      localStorage: {
        count: localCount,
        sizeBytes: localSize * 2,
        sizeKB: (localSize * 2 / 1024).toFixed(2)
      },
      sessionStorage: {
        count: sessionCount,
        sizeBytes: sessionSize * 2,
        sizeKB: (sessionSize * 2 / 1024).toFixed(2)
      }
    }
  }
}

export default Cache
export { LocalStorage, SessionStorage, CACHE_KEYS, CACHE_TTL }
