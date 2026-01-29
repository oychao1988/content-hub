import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ContentEditor from '@/components/content/ContentEditor.vue'

// Mock 子组件
vi.mock('@/components/content/MarkdownPreview.vue', () => ({
  default: {
    name: 'MarkdownPreview',
    template: '<div class="markdown-preview-mock"><slot /></div>'
  }
}))

vi.mock('@/components/content/ImagePreview.vue', () => ({
  default: {
    name: 'ImagePreview',
    props: ['imageSrc', 'modelValue'],
    template: '<div v-if="modelValue" class="image-preview-mock">Image Preview</div>'
  }
}))

describe('ContentEditor.vue', () => {
  let wrapper

  beforeEach(() => {
    // Mock requestFullscreen
    document.documentElement.requestFullscreen = vi.fn()
    document.exitFullscreen = vi.fn()

    wrapper = mount(ContentEditor, {
      props: {
        modelValue: ''
      },
      global: {
        stubs: {
          'el-button': true,
          'el-button-group': true,
          'el-icon': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('应该渲染编辑器', () => {
    expect(wrapper.find('.content-editor').exists()).toBe(true)
    expect(wrapper.find('.editor-toolbar').exists()).toBe(true)
    expect(wrapper.find('.editor-content').exists()).toBe(true)
  })

  it('应该显示工具栏按钮', () => {
    const buttons = wrapper.findAll('.editor-toolbar el-button-stub')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('应该在编辑模式下显示 textarea', () => {
    wrapper.vm.previewMode = 'edit'
    expect(wrapper.find('.editor-textarea').exists()).toBe(true)
  })

  it('应该支持 v-model', async () => {
    await wrapper.setProps({ modelValue: 'Initial content' })
    expect(wrapper.vm.localContent).toBe('Initial content')
  })

  it('应该在内容变化时触发 update:modelValue 事件', async () => {
    wrapper.vm.localContent = 'New content'
    await wrapper.vm.$nextTick()

    expect(wrapper.emitted('update:modelValue')).toBeTruthy()
    expect(wrapper.emitted('update:modelValue')[0]).toEqual(['New content'])
  })

  it('应该切换预览模式', async () => {
    expect(wrapper.vm.previewMode).toBe('edit')

    wrapper.vm.previewMode = 'preview'
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.preview-panel').exists()).toBe(true)
  })

  it('应该切换分屏模式', async () => {
    wrapper.vm.previewMode = 'split'
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.editor-panel').exists()).toBe(true)
    expect(wrapper.find('.preview-panel').exists()).toBe(true)
  })

  it('应该有 insertText 方法', () => {
    expect(typeof wrapper.vm.insertText).toBe('function')
  })

  it('应该有 handleInput 方法', () => {
    expect(typeof wrapper.vm.handleInput).toBe('function')
  })

  it('应该有 handleCtrlEnter 方法', () => {
    expect(typeof wrapper.vm.handleCtrlEnter).toBe('function')
  })

  it('应该有 toggleFullScreen 方法', () => {
    expect(typeof wrapper.vm.toggleFullScreen).toBe('function')
  })

  it('应该在 Ctrl+Enter 时触发 submit 事件', () => {
    wrapper.vm.localContent = 'Test content'
    wrapper.vm.handleCtrlEnter()

    expect(wrapper.emitted('submit')).toBeTruthy()
    expect(wrapper.emitted('submit')[0]).toEqual(['Test content'])
  })

  it('应该处理图片点击事件', () => {
    wrapper.vm.handleImageClick('https://example.com/image.jpg')

    expect(wrapper.vm.showImagePreview).toBe(true)
    expect(wrapper.vm.previewImageSrc).toBe('https://example.com/image.jpg')
  })

  it('应该切换全屏模式', () => {
    expect(wrapper.vm.isFullScreen).toBe(false)

    wrapper.vm.toggleFullScreen()
    expect(wrapper.vm.isFullScreen).toBe(true)
    expect(document.documentElement.requestFullscreen).toHaveBeenCalled()

    wrapper.vm.toggleFullScreen()
    expect(wrapper.vm.isFullScreen).toBe(false)
    expect(document.exitFullscreen).toHaveBeenCalled()
  })

  it('应该使用自定义 placeholder', async () => {
    await wrapper.setProps({ placeholder: '请输入文章内容...' })

    const textarea = wrapper.find('.editor-textarea')
    expect(textarea.attributes('placeholder')).toBe('请输入文章内容...')
  })

  it('应该监听 modelValue 变化', async () => {
    await wrapper.setProps({ modelValue: 'Updated content' })

    // 等待 watch 触发
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.localContent).toBe('Updated content')
  })
})
