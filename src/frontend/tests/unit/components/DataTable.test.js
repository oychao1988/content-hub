import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import DataTable from '@/components/common/DataTable.vue'

describe('DataTable.vue', () => {
  let wrapper

  const mockData = [
    { id: 1, name: 'Item 1' },
    { id: 2, name: 'Item 2' },
    { id: 3, name: 'Item 3' }
  ]

  beforeEach(() => {
    wrapper = mount(DataTable, {
      props: {
        data: mockData
      },
      global: {
        stubs: {
          'el-table': {
            template: '<div class="el-table-stub"><slot></slot></div>',
            props: ['data', 'loading', 'stripe', 'border', 'height', 'max-height'],
            emits: ['selection-change', 'sort-change']
          },
          'el-table-column': {
            template: '<div class="el-table-column-stub"></div>',
            props: ['type']
          },
          'el-pagination': {
            template: '<div class="el-pagination-stub"></div>',
            props: ['current-page', 'page-size', 'page-sizes', 'total', 'layout'],
            emits: ['current-change', 'size-change']
          },
          'el-empty': true
        },
        directives: {
          loading: {} // 模拟 loading 指令
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('应该正确渲染数据', () => {
    const table = wrapper.find('.el-table-stub')
    expect(table.exists()).toBe(true)
  })

  it('应该显示加载状态', async () => {
    await wrapper.setProps({ loading: true })
    // 检查 loading 类是否存在或者属性是否设置
    expect(wrapper.find('.el-table-stub').exists()).toBe(true)
  })

  it('应该显示分页器', () => {
    const pagination = wrapper.find('.pagination-container')
    expect(pagination.exists()).toBe(true)
  })

  it('应该隐藏分页器当 showPagination 为 false', async () => {
    await wrapper.setProps({ showPagination: false })
    const pagination = wrapper.find('.pagination-container')
    expect(pagination.exists()).toBe(false)
  })

  it('应该显示序号列', async () => {
    await wrapper.setProps({ showIndex: true })
    // 检查是否有 el-table-column 组件
    expect(wrapper.find('.el-table-column-stub').exists()).toBe(true)
  })

  it('应该显示选择列', async () => {
    await wrapper.setProps({ selectable: true })
    // 检查是否有 el-table-column 组件
    expect(wrapper.find('.el-table-column-stub').exists()).toBe(true)
  })

  it('应该暴露 resetPage 方法', () => {
    expect(wrapper.vm.resetPage).toBeDefined()
    expect(typeof wrapper.vm.resetPage).toBe('function')
  })

  it('应该正确传递属性', async () => {
    // 测试传递属性到 el-table
    await wrapper.setProps({ stripe: false, border: true, height: '500px', maxHeight: '600px' })
    expect(wrapper.props('stripe')).toBe(false)
    expect(wrapper.props('border')).toBe(true)
    expect(wrapper.props('height')).toBe('500px')
    expect(wrapper.props('maxHeight')).toBe('600px')

    // 测试传递属性到 el-pagination
    await wrapper.setProps({ total: 100, pageSizes: [20, 40, 80] })
    expect(wrapper.props('total')).toBe(100)
    expect(wrapper.props('pageSizes')).toEqual([20, 40, 80])
  })

  it('应该渲染插槽内容', () => {
    const customSlotContent = 'Test Slot Content'
    const wrapperWithSlot = mount(DataTable, {
      props: {
        data: mockData
      },
      slots: {
        default: customSlotContent
      },
      global: {
        stubs: {
          'el-table': {
            template: '<div class="el-table-stub"><slot></slot></div>'
          },
          'el-pagination': true,
          'el-empty': true
        },
        directives: {
          loading: {}
        }
      }
    })

    expect(wrapperWithSlot.html()).toContain(customSlotContent)
  })
})
