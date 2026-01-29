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
          'el-table': true,
          'el-table-column': true,
          'el-pagination': true,
          'el-empty': true
        }
      }
    })
  })

  afterEach(() => {
    wrapper?.unmount()
  })

  it('应该正确渲染数据', () => {
    const table = wrapper.find('el-table-stub')
    expect(table.exists()).toBe(true)
    expect(table.attributes('data')).toBeDefined()
  })

  it('应该显示加载状态', async () => {
    await wrapper.setProps({ loading: true })
    const table = wrapper.find('el-table-stub')
    expect(table.attributes('loading')).toBeDefined()
  })

  it('应该显示分页器', () => {
    const pagination = wrapper.find('.pagination-container el-pagination-stub')
    expect(pagination.exists()).toBe(true)
  })

  it('应该隐藏分页器当 showPagination 为 false', async () => {
    await wrapper.setProps({ showPagination: false })
    const pagination = wrapper.find('.pagination-container')
    expect(pagination.exists()).toBe(false)
  })

  it('应该显示序号列', async () => {
    await wrapper.setProps({ showIndex: true })
    const indexColumn = wrapper.findAll('el-table-column-stub').find(
      col => col.attributes('type') === 'index'
    )
    expect(indexColumn).toBeDefined()
  })

  it('应该显示选择列', async () => {
    await wrapper.setProps({ selectable: true })
    const selectionColumn = wrapper.findAll('el-table-column-stub').find(
      col => col.attributes('type') === 'selection'
    )
    expect(selectionColumn).toBeDefined()
  })

  it('应该触发选择变化事件', async () => {
    const selection = [mockData[0]]
    await wrapper.find('el-table-stub').vm.$emit('selection-change', selection)

    expect(wrapper.emitted('selection-change')).toBeTruthy()
    expect(wrapper.emitted('selection-change')[0]).toEqual([selection])
  })

  it('应该触发排序变化事件', async () => {
    const sort = { prop: 'name', order: 'ascending' }
    await wrapper.find('el-table-stub').vm.$emit('sort-change', sort)

    expect(wrapper.emitted('sort-change')).toBeTruthy()
    expect(wrapper.emitted('sort-change')[0]).toEqual([sort])
  })

  it('应该触发页码变化事件', async () => {
    const pagination = wrapper.find('.pagination-container el-pagination-stub')
    await pagination.vm.$emit('update:current-page', 2)

    expect(wrapper.emitted('page-change')).toBeTruthy()
    expect(wrapper.emitted('page-change')[0]).toEqual([2])
  })

  it('应该触发每页数量变化事件', async () => {
    const pagination = wrapper.find('.pagination-container el-pagination-stub')
    await pagination.vm.$emit('update:page-size', 50)

    expect(wrapper.emitted('size-change')).toBeTruthy()
    expect(wrapper.emitted('size-change')[0]).toEqual([50])
  })

  it('应该正确传递 total 属性', async () => {
    await wrapper.setProps({ total: 100 })
    const pagination = wrapper.find('.pagination-container el-pagination-stub')
    expect(pagination.attributes('total')).toBe('100')
  })

  it('应该支持自定义 pageSizes', async () => {
    const customSizes = [20, 40, 80]
    await wrapper.setProps({ pageSizes: customSizes })

    // 检查是否正确传递
    expect(wrapper.props('pageSizes')).toEqual(customSizes)
  })

  it('应该正确传递 stripe 属性', async () => {
    await wrapper.setProps({ stripe: false })
    const table = wrapper.find('el-table-stub')
    expect(table.attributes('stripe')).toBeUndefined()
  })

  it('应该正确传递 border 属性', async () => {
    await wrapper.setProps({ border: true })
    const table = wrapper.find('el-table-stub')
    expect(table.attributes('border')).toBeDefined()
  })

  it('应该支持设置高度', async () => {
    await wrapper.setProps({ height: '500px' })
    const table = wrapper.find('el-table-stub')
    expect(table.attributes('height')).toBe('500px')
  })

  it('应该支持设置最大高度', async () => {
    await wrapper.setProps({ maxHeight: '600px' })
    const table = wrapper.find('el-table-stub')
    expect(table.attributes('max-height')).toBe('600px')
  })

  it('应该暴露 resetPage 方法', () => {
    expect(wrapper.vm.resetPage).toBeDefined()
    expect(typeof wrapper.vm.resetPage).toBe('function')
  })

  it('应该渲染插槽内容', () => {
    const wrapperWithSlot = mount(DataTable, {
      props: {
        data: mockData
      },
      slots: {
        default: '<el-table-column prop="name" label="Name" />'
      },
      global: {
        stubs: {
          'el-table': true,
          'el-table-column': true,
          'el-pagination': true,
          'el-empty': true
        }
      }
    })

    expect(wrapperWithSlot.html()).toContain('el-table-column')
  })
})
