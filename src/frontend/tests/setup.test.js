import { describe, it, expect } from 'vitest'

describe('测试环境配置', () => {
  it('应该能运行测试', () => {
    expect(true).toBe(true)
  })

  it('应该能进行基本计算', () => {
    expect(1 + 1).toBe(2)
  })

  it('应该能处理字符串', () => {
    const str = 'Hello, Vitest!'
    expect(str).toContain('Vitest')
  })
})
