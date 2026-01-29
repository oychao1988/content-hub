import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import MarkdownPreview from '@/components/content/MarkdownPreview.vue'

// Mock highlight.js
vi.mock('highlight.js', () => ({
  default: {
    getLanguage: vi.fn(() => true),
    highlight: vi.fn((str, options) => ({
      value: str
    }))
  }
}))

describe('MarkdownPreview.vue', () => {
  let wrapper

  beforeEach(() => {
    wrapper = mount(MarkdownPreview, {
      global: {
        stubs: {
          'el-empty': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('应该渲染空状态当没有内容', () => {
    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.markdown-content').exists()).toBe(false)
  })

  it('应该渲染 markdown 内容', async () => {
    const markdown = '# Hello World\n\nThis is a test.'
    await wrapper.setProps({ content: markdown })

    expect(wrapper.find('.markdown-content').exists()).toBe(true)
    expect(wrapper.find('.empty-state').exists()).toBe(false)
  })

  it('应该正确转换 markdown 为 HTML', async () => {
    const markdown = '# Hello World'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<h1>')
    expect(html).toContain('Hello World')
  })

  it('应该渲染列表', async () => {
    const markdown = '- Item 1\n- Item 2\n- Item 3'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<ul>')
    expect(html).toContain('Item 1')
    expect(html).toContain('Item 2')
  })

  it('应该渲染链接', async () => {
    const markdown = '[Link](https://example.com)'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<a')
    expect(html).toContain('https://example.com')
  })

  it('应该渲染图片', async () => {
    const markdown = '![Alt text](https://example.com/image.jpg)'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<img')
    expect(html).toContain('https://example.com/image.jpg')
  })

  it('应该渲染代码块', async () => {
    const markdown = '```javascript\nconst x = 1;\n```'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<pre')
    expect(html).toContain('<code')
  })

  it('应该渲染引用', async () => {
    const markdown = '> This is a quote'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<blockquote>')
  })

  it('应该触发图片点击事件', async () => {
    const markdown = '![Image](https://example.com/image.jpg)'
    await wrapper.setProps({ content: markdown })

    const img = wrapper.find('.markdown-content img')
    expect(img.exists()).toBe(true)

    await img.trigger('click')
    expect(wrapper.emitted('image-click')).toBeTruthy()
    expect(wrapper.emitted('image-click')[0]).toEqual(['https://example.com/image.jpg'])
  })

  it('应该不触发点击事件当点击的不是图片', async () => {
    const markdown = '# Title'
    await wrapper.setProps({ content: markdown })

    const content = wrapper.find('.markdown-content')
    await content.trigger('click')

    expect(wrapper.emitted('image-click')).toBeFalsy()
  })

  it('应该支持 linkify 选项', async () => {
    const markdown = 'https://example.com'
    await wrapper.setProps({ content: markdown, linkify: true })

    const html = wrapper.find('.markdown-content').html()
    // markdown-it 应该将纯链接转换为可点击链接
    expect(html).toContain('example.com')
  })

  it('应该支持 highlight 选项', async () => {
    const markdown = '```javascript\nconst x = 1;\n```'
    await wrapper.setProps({ content: markdown, highlight: true })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<pre')
    expect(html).toContain('<code')
  })

  it('应该渲染表格', async () => {
    const markdown = '| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('<table>')
  })

  it('应该正确处理空字符串', async () => {
    await wrapper.setProps({ content: '' })

    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.markdown-content').exists()).toBe(false)
  })

  it('应该正确处理特殊字符', async () => {
    const markdown = '# Test & < > "'
    await wrapper.setProps({ content: markdown })

    const html = wrapper.find('.markdown-content').html()
    expect(html).toContain('Test')
  })
})
