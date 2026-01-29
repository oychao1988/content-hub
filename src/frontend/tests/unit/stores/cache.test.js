import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useCacheStore } from '@/stores/modules/cache'

describe('Cache Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    // 清空 console.log 输出
    vi.spyOn(console, 'debug').mockImplementation(() => {})
    vi.spyOn(console, 'info').mockImplementation(() => {})
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  describe('初始状态', () => {
    it('应该有正确的初始状态', () => {
      const store = useCacheStore()

      expect(store.size).toBe(0)
      expect(store.stats).toEqual({
        hits: 0,
        misses: 0,
        sets: 0,
        deletes: 0
      })
    })

    it('应该正确计算缓存大小', () => {
      const store = useCacheStore()

      expect(store.size).toBe(0)

      store.set('/api/test', {}, { data: 'test' })
      expect(store.size).toBe(1)

      store.set('/api/test2', {}, { data: 'test2' })
      expect(store.size).toBe(2)
    })

    it('应该正确计算命中率', () => {
      const store = useCacheStore()

      expect(store.hitRate).toBe('0.00')

      store.stats.hits = 5
      store.stats.misses = 5
      expect(store.hitRate).toBe('50.00')
    })
  })

  describe('get 方法', () => {
    it('应该返回缓存的数据', () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      store.set('/api/test', {}, data)
      const result = store.get('/api/test', {})

      expect(result).toEqual(data)
      expect(store.stats.hits).toBe(1)
    })

    it('应该返回 null 当缓存不存在', () => {
      const store = useCacheStore()

      const result = store.get('/api/nonexistent', {})

      expect(result).toBeNull()
      expect(store.stats.misses).toBe(1)
    })

    it('应该正确处理带参数的缓存键', () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      store.set('/api/test', { page: 1, size: 10 }, data)
      const result = store.get('/api/test', { page: 1, size: 10 })

      expect(result).toEqual(data)
    })

    it('应该忽略 undefined 和 null 参数', () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      store.set('/api/test', { page: 1, size: 10, filter: undefined }, data)
      const result = store.get('/api/test', { page: 1, size: 10, filter: null })

      expect(result).toEqual(data)
    })

    it('应该返回 null 当缓存已过期', () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      // 设置一个 1ms TTL 的缓存
      store.set('/api/test', {}, data, 1)

      // 等待过期
      return new Promise(resolve => {
        setTimeout(() => {
          const result = store.get('/api/test', {})
          expect(result).toBeNull()
          expect(store.stats.misses).toBe(1)
          resolve()
        }, 10)
      })
    })
  })

  describe('set 方法', () => {
    it('应该设置缓存数据', () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      store.set('/api/test', {}, data)

      expect(store.size).toBe(1)
      expect(store.stats.sets).toBe(1)
      expect(store.get('/api/test', {})).toEqual(data)
    })

    it('应该覆盖已存在的缓存', () => {
      const store = useCacheStore()

      store.set('/api/test', {}, { data: 'old' })
      store.set('/api/test', {}, { data: 'new' })

      expect(store.size).toBe(1)
      expect(store.get('/api/test', {})).toEqual({ data: 'new' })
    })

    it('应该支持自定义 TTL', () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      store.set('/api/test', {}, data, 10000)

      const result = store.get('/api/test', {})
      expect(result).toEqual(data)
    })
  })

  describe('remove 方法', () => {
    it('应该删除指定缓存', () => {
      const store = useCacheStore()

      store.set('/api/test', {}, { data: 'test' })
      expect(store.size).toBe(1)

      store.remove('/api/test', {})
      expect(store.size).toBe(0)
      expect(store.stats.deletes).toBe(1)
    })

    it('应该清空所有缓存当没有提供 URL', () => {
      const store = useCacheStore()

      store.set('/api/test1', {}, { data: 'test1' })
      store.set('/api/test2', {}, { data: 'test2' })
      expect(store.size).toBe(2)

      store.remove()
      expect(store.size).toBe(0)
      expect(store.stats.deletes).toBe(2)
    })

    it('不应该删除不存在的缓存', () => {
      const store = useCacheStore()

      store.set('/api/test', {}, { data: 'test' })
      store.remove('/api/nonexistent', {})

      expect(store.size).toBe(1)
      expect(store.stats.deletes).toBe(0)
    })
  })

  describe('removePattern 方法', () => {
    it('应该根据模式删除缓存', () => {
      const store = useCacheStore()

      store.set('/api/users', {}, { data: 'users' })
      store.set('/api/users/1', {}, { data: 'user1' })
      store.set('/api/posts', {}, { data: 'posts' })

      store.removePattern('/api/users*')

      expect(store.size).toBe(1)
      expect(store.get('/api/posts', {})).toEqual({ data: 'posts' })
    })

    it('应该支持通配符删除', () => {
      const store = useCacheStore()

      store.set('/api/users', {}, { data: 'users' })
      store.set('/api/users/1', {}, { data: 'user1' })
      store.set('/api/posts', {}, { data: 'posts' })

      store.removePattern('/api/*')

      expect(store.size).toBe(0)
    })
  })

  describe('cleanup 方法', () => {
    it('应该清理过期的缓存', async () => {
      const store = useCacheStore()

      // 设置一个 1ms TTL 的缓存
      store.set('/api/expired', {}, { data: 'expired' }, 1)
      // 设置一个较长的 TTL
      store.set('/api/valid', {}, { data: 'valid' }, 10000)

      expect(store.size).toBe(2)

      // 等待过期
      await new Promise(resolve => setTimeout(resolve, 10))

      store.cleanup()

      expect(store.size).toBe(1)
      expect(store.get('/api/valid', {})).toEqual({ data: 'valid' })
    })
  })

  describe('getStats 方法', () => {
    it('应该返回完整的统计信息', () => {
      const store = useCacheStore()

      store.set('/api/test', {}, { data: 'test' })
      store.get('/api/test', {})
      store.get('/api/nonexistent', {})

      const stats = store.getStats()

      expect(stats).toEqual({
        hits: 1,
        misses: 1,
        sets: 1,
        deletes: 0,
        size: 1,
        hitRate: '50.00'
      })
    })
  })

  describe('resetStats 方法', () => {
    it('应该重置统计信息', () => {
      const store = useCacheStore()

      store.set('/api/test', {}, { data: 'test' })
      store.get('/api/test', {})
      store.get('/api/nonexistent', {})

      expect(store.stats.hits).toBe(1)
      expect(store.stats.misses).toBe(1)

      store.resetStats()

      expect(store.stats).toEqual({
        hits: 0,
        misses: 0,
        sets: 0,
        deletes: 0
      })
    })
  })

  describe('cachedGet 方法', () => {
    it('应该从缓存获取数据', async () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      store.set('/api/test', {}, data)

      const requestFn = vi.fn().mockResolvedValue({ data: 'fresh' })
      const result = await store.cachedGet(requestFn, '/api/test', {})

      expect(result).toEqual(data)
      expect(requestFn).not.toHaveBeenCalled()
    })

    it('应该发起请求当缓存不存在', async () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      const requestFn = vi.fn().mockResolvedValue(data)
      const result = await store.cachedGet(requestFn, '/api/test', {})

      expect(result).toEqual(data)
      expect(requestFn).toHaveBeenCalledWith('/api/test', {})
      expect(store.get('/api/test', {})).toEqual(data)
    })

    it('应该处理请求失败', async () => {
      const store = useCacheStore()

      const requestFn = vi.fn().mockRejectedValue(new Error('Request failed'))

      await expect(store.cachedGet(requestFn, '/api/test', {}))
        .rejects.toThrow('Request failed')
    })

    it('应该支持自定义 TTL', async () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      const requestFn = vi.fn().mockResolvedValue(data)
      await store.cachedGet(requestFn, '/api/test', {}, 10000)

      const result = store.get('/api/test', {})
      expect(result).toEqual(data)
    })

    it('应该正确处理带参数的请求', async () => {
      const store = useCacheStore()
      const data = { id: 1, name: 'test' }

      const requestFn = vi.fn().mockResolvedValue(data)
      const config = { params: { page: 1, size: 10 } }

      await store.cachedGet(requestFn, '/api/test', config)

      expect(requestFn).toHaveBeenCalledWith('/api/test', config)
      expect(store.get('/api/test', { page: 1, size: 10 })).toEqual(data)
    })
  })

  describe('generateKey 方法', () => {
    it('应该为没有参数的 URL 生成键', () => {
      const store = useCacheStore()

      const key = store.generateKey('/api/test', {})
      expect(key).toBe('/api/test')
    })

    it('应该为带参数的 URL 生成键', () => {
      const store = useCacheStore()

      const key = store.generateKey('/api/test', { page: 1, size: 10 })
      expect(key).toContain('/api/test?')
      expect(key).toContain('page=1')
      expect(key).toContain('size=10')
    })

    it('应该对参数键进行排序', () => {
      const store = useCacheStore()

      const key1 = store.generateKey('/api/test', { b: 2, a: 1 })
      const key2 = store.generateKey('/api/test', { a: 1, b: 2 })

      expect(key1).toBe(key2)
    })
  })
})
