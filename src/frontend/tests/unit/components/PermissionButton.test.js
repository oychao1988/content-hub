import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import PermissionButton from '@/components/PermissionButton.vue'

// Mock user store - must be defined inline for vi.mock hoisting
vi.mock('@/stores/modules/user', () => ({
  useUserStore: vi.fn()
}))

// Import the mocked function
import { useUserStore } from '@/stores/modules/user'

describe('PermissionButton.vue', () => {
  let wrapper
  let mockUserStore

  beforeEach(() => {
    // 创建 pinia 实例
    setActivePinia(createPinia())

    // Mock user store
    mockUserStore = {
      hasAnyPermission: vi.fn(),
      hasAllPermissions: vi.fn()
    }

    // 设置 mock 返回值
    useUserStore.mockReturnValue(mockUserStore)
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  it('应该渲染按钮当用户有权限', () => {
    mockUserStore.hasAnyPermission.mockReturnValue(true)

    wrapper = mount(PermissionButton, {
      props: {
        permission: 'account:create'
      },
      global: {
        stubs: {
          'el-button': true
        }
      }
    })

    expect(mockUserStore.hasAnyPermission).toHaveBeenCalledWith(['account:create'])
    expect(wrapper.find('el-button-stub').exists()).toBe(true)
  })

  it('不应该渲染按钮当用户没有权限', () => {
    mockUserStore.hasAnyPermission.mockReturnValue(false)

    wrapper = mount(PermissionButton, {
      props: {
        permission: 'account:create'
      },
      global: {
        stubs: {
          'el-button': true
        }
      }
    })

    expect(wrapper.find('el-button-stub').exists()).toBe(false)
  })

  it('应该支持数组权限（满足任意一个）', () => {
    mockUserStore.hasAnyPermission.mockReturnValue(true)

    wrapper = mount(PermissionButton, {
      props: {
        permission: ['account:create', 'account:update']
      },
      global: {
        stubs: {
          'el-button': true
        }
      }
    })

    expect(mockUserStore.hasAnyPermission).toHaveBeenCalledWith(['account:create', 'account:update'])
  })

  it('应该支持 requireAll 模式（需要所有权限）', () => {
    mockUserStore.hasAllPermissions.mockReturnValue(true)

    wrapper = mount(PermissionButton, {
      props: {
        permission: ['account:create', 'account:update'],
        requireAll: true
      },
      global: {
        stubs: {
          'el-button': true
        }
      }
    })

    expect(mockUserStore.hasAllPermissions).toHaveBeenCalledWith(['account:create', 'account:update'])
  })

  it('应该在 requireAll 模式下检查所有权限', () => {
    mockUserStore.hasAllPermissions.mockReturnValue(false)

    wrapper = mount(PermissionButton, {
      props: {
        permission: ['account:create', 'account:update'],
        requireAll: true
      },
      global: {
        stubs: {
          'el-button': true
        }
      }
    })

    expect(wrapper.find('el-button-stub').exists()).toBe(false)
  })

  it('应该传递所有属性到 el-button', () => {
    mockUserStore.hasAnyPermission.mockReturnValue(true)

    wrapper = mount(PermissionButton, {
      props: {
        permission: 'account:create',
        type: 'primary',
        size: 'small'
      },
      global: {
        stubs: {
          'el-button': true
        }
      }
    })

    const button = wrapper.find('el-button-stub')
    expect(button.attributes('type')).toBe('primary')
    expect(button.attributes('size')).toBe('small')
  })

  it('应该正确触发点击事件', async () => {
    mockUserStore.hasAnyPermission.mockReturnValue(true)

    wrapper = mount(PermissionButton, {
      props: {
        permission: 'account:create'
      },
      global: {
        stubs: {
          'el-button': true
        }
      }
    })

    await wrapper.find('el-button-stub').trigger('click')
    expect(wrapper.emitted('click')).toBeTruthy()
    expect(wrapper.emitted('click').length).toBe(1)
  })

  it('应该渲染插槽内容', () => {
    mockUserStore.hasAnyPermission.mockReturnValue(true)

    wrapper = mount(PermissionButton, {
      props: {
        permission: 'account:create'
      },
      slots: {
        default: '创建账号'
      },
      global: {
        stubs: {
          'el-button': {
            template: '<button><slot /></button>'
          }
        }
      }
    })

    expect(wrapper.find('button').text()).toBe('创建账号')
  })
})
