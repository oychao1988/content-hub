import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ImagePreview from '@/components/content/ImagePreview.vue'

// Mock Element Plus message
vi.mock('element-plus', () => ({
  ElMessage: {
    success: vi.fn(),
    error: vi.fn()
  }
}))

// Mock fetch
global.fetch = vi.fn()

describe('ImagePreview.vue', () => {
  let wrapper

  const mockImageSrc = 'https://example.com/test-image.jpg'

  beforeEach(() => {
    // Mock fetch 成功响应
    global.fetch.mockResolvedValue({
      headers: {
        get: vi.fn((key) => {
          if (key === 'content-length') return '12345'
          return null
        })
      },
      blob: vi.fn().mockResolvedValue(new Blob(['image data'], { type: 'image/jpeg' }))
    })

    wrapper = mount(ImagePreview, {
      props: {
        imageSrc: mockImageSrc,
        modelValue: true
      },
      global: {
        stubs: {
          'el-dialog': true,
          'el-button': true,
          'el-button-group': true,
          'el-icon': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
    vi.clearAllMocks()
  })

  it('应该渲染对话框', () => {
    const dialog = wrapper.find('el-dialog-stub')
    expect(dialog.exists()).toBe(true)
  })

  it('应该显示图片', () => {
    const img = wrapper.find('img.preview-image')
    expect(img.exists()).toBe(true)
    expect(img.attributes('src')).toBe(mockImageSrc)
  })

  it('应该显示控制工具栏', () => {
    const toolbar = wrapper.find('.control-toolbar')
    expect(toolbar.exists()).toBe(true)
  })

  it('应该显示缩放级别', () => {
    const zoomLevel = wrapper.find('.zoom-level')
    expect(zoomLevel.exists()).toBe(true)
    expect(zoomLevel.text()).toContain('100%')
  })

  it('应该有 zoomIn 方法', () => {
    expect(typeof wrapper.vm.zoomIn).toBe('function')
  })

  it('应该有 zoomOut 方法', () => {
    expect(typeof wrapper.vm.zoomOut).toBe('function')
  })

  it('应该有 reset 方法', () => {
    expect(typeof wrapper.vm.reset).toBe('function')
  })

  it('应该增加缩放级别', () => {
    const initialScale = wrapper.vm.scale
    wrapper.vm.zoomIn()
    expect(wrapper.vm.scale).toBe(initialScale + 0.1)
  })

  it('应该减少缩放级别', () => {
    const initialScale = wrapper.vm.scale
    wrapper.vm.zoomOut()
    expect(wrapper.vm.scale).toBe(initialScale - 0.1)
  })

  it('应该限制最小缩放级别', () => {
    wrapper.vm.scale = 0.5
    wrapper.vm.zoomOut()
    expect(wrapper.vm.scale).toBe(0.5)
  })

  it('应该限制最大缩放级别', () => {
    wrapper.vm.scale = 3
    wrapper.vm.zoomIn()
    expect(wrapper.vm.scale).toBe(3)
  })

  it('应该重置所有变换', () => {
    wrapper.vm.scale = 2
    wrapper.vm.rotation = 90
    wrapper.vm.flipH = -1
    wrapper.vm.flipV = -1

    wrapper.vm.reset()

    expect(wrapper.vm.scale).toBe(1)
    expect(wrapper.vm.rotation).toBe(0)
    expect(wrapper.vm.flipH).toBe(1)
    expect(wrapper.vm.flipV).toBe(1)
  })

  it('应该向右旋转', () => {
    wrapper.vm.rotation = 0
    wrapper.vm.rotateRight()
    expect(wrapper.vm.rotation).toBe(90)
  })

  it('应该向左旋转', () => {
    wrapper.vm.rotation = 0
    wrapper.vm.rotateLeft()
    expect(wrapper.vm.rotation).toBe(270)
  })

  it('应该水平翻转', () => {
    const initialFlipH = wrapper.vm.flipH
    wrapper.vm.flipHorizontal()
    expect(wrapper.vm.flipH).toBe(initialFlipH * -1)
  })

  it('应该垂直翻转', () => {
    const initialFlipV = wrapper.vm.flipV
    wrapper.vm.flipVertical()
    expect(wrapper.vm.flipV).toBe(initialFlipV * -1)
  })

  it('应该处理滚轮缩放', () => {
    const initialScale = wrapper.vm.scale

    // 模拟滚轮向上（放大）
    const event1 = { deltaY: -100, preventDefault: vi.fn() }
    wrapper.vm.handleWheel(event1)
    expect(wrapper.vm.scale).toBe(initialScale + 0.1)

    // 模拟滚轮向下（缩小）
    const event2 = { deltaY: 100, preventDefault: vi.fn() }
    wrapper.vm.handleWheel(event2)
    expect(wrapper.vm.scale).toBe(initialScale)
  })

  it('应该有 downloadImage 方法', () => {
    expect(typeof wrapper.vm.downloadImage).toBe('function')
  })

  it('应该有 copyImage 方法', () => {
    expect(typeof wrapper.vm.copyImage).toBe('function')
  })

  it('应该计算图片变换样式', () => {
    wrapper.vm.scale = 1.5
    wrapper.vm.rotation = 90
    wrapper.vm.flipH = -1
    wrapper.vm.flipV = 1

    const transform = wrapper.vm.imageTransform
    expect(transform).toContain('scale(1.5)')
    expect(transform).toContain('rotate(90deg)')
    expect(transform).toContain('scaleX(-1)')
    expect(transform).toContain('scaleY(1)')
  })

  it('应该关闭对话框', async () => {
    await wrapper.vm.handleBeforeClose()
    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
  })

  it('应该支持 v-model', async () => {
    expect(wrapper.props('modelValue')).toBe(true)

    await wrapper.setProps({ modelValue: false })
    expect(wrapper.vm.visible).toBe(false)
  })
})
