/**
 * 菜单配置文件
 *
 * 菜单结构说明:
 * - 顶级菜单项: 直接展示的菜单项（如仪表盘）
 * - 分组菜单: 包含多个子菜单项的可折叠菜单（使用 items 属性）
 *
 * 权限控制:
 * - permissions: 需要的权限数组（满足任意一个即可）
 * - role: 需要的角色（可选，用于管理员专属菜单）
 *
 * 使用方式:
 * 1. 在 MainLayout.vue 中导入此配置
 * 2. 根据用户权限过滤菜单项
 * 3. 渲染分组菜单和子菜单
 */

export const menuConfig = [
  // ==================== 顶级菜单（仪表盘）====================
  {
    title: '仪表盘',
    icon: 'DataBoard',
    path: '/'
    // 注意: 仪表盘对所有已登录用户可见，无需权限控制
  },

  // ==================== 内容运营分组 ====================
  {
    title: '内容运营',
    icon: 'Document',
    isSubmenu: true, // 标识为分组菜单
    items: [
      {
        title: '账号管理',
        icon: 'User',
        path: '/accounts',
        permissions: ['account:read'],
        visibleRoles: ['operator', 'customer'] // operator 和 customer 可见
      },
      {
        title: '内容管理',
        icon: 'Document',
        path: '/content',
        permissions: ['content:read'],
        visibleRoles: ['operator', 'editor', 'viewer'] // operator、editor 和 viewer 可见
      },
      {
        title: '发布管理',
        icon: 'Promotion',
        path: '/publisher',
        permissions: ['publisher:read'],
        visibleRoles: ['operator', 'customer'] // operator 和 customer 可见
      },
      {
        title: '发布池',
        icon: 'Box',
        path: '/publish-pool',
        permissions: ['publish-pool:read'],
        visibleRoles: ['operator'] // 仅 operator 可见
      }
    ]
  },

  // ==================== 任务调度分组 ====================
  {
    title: '任务调度',
    icon: 'Timer',
    isSubmenu: true,
    items: [
      {
        title: '定时任务',
        icon: 'Timer',
        path: '/scheduler',
        permissions: ['scheduler:read'],
        visibleRoles: ['operator'] // 仅 operator 可见
      }
    ]
  },

  // ==================== 系统管理分组 ====================
  {
    title: '系统管理',
    icon: 'Setting',
    isSubmenu: true,
    role: 'admin', // 整个分组仅管理员可见
    items: [
      {
        title: '用户管理',
        icon: 'UserFilled',
        path: '/users',
        permissions: ['user:read'],
        role: 'admin'
      },
      {
        title: '客户管理',
        icon: 'OfficeBuilding',
        path: '/customers',
        permissions: ['customer:read'],
        role: 'admin'
      },
      {
        title: '平台管理',
        icon: 'Monitor', // 使用 Monitor 替代 Platform（Element Plus 没有 Platform 图标）
        path: '/platforms',
        permissions: ['platform:read'],
        role: 'admin'
      },
      {
        title: '写作风格管理',
        icon: 'EditPen',
        path: '/writing-styles',
        permissions: ['writing-style:read'],
        role: 'admin'
      },
      {
        title: '内容主题管理',
        icon: 'CollectionTag',
        path: '/content-themes',
        permissions: ['content-theme:read'],
        role: 'admin'
      },
      {
        title: '系统配置',
        icon: 'Setting',
        path: '/config',
        permissions: ['config:read'],
        role: 'admin'
      }
    ]
  }
]

/**
 * 菜单配置说明
 *
 * 数据结构:
 * - MenuGroup: 分组菜单（包含子菜单）
 *   - title: 分组标题
 *   - icon: Element Plus 图标名
 *   - isSubmenu: true（标识为分组）
 *   - items: 子菜单项数组
 *   - permissions: 可选，访问该分组的权限
 *   - role: 可选，访问该分组的角色要求
 *
 * - MenuItem: 子菜单项
 *   - title: 菜单标题
 *   - icon: Element Plus 图标名
 *   - path: 路由路径
 *   - permissions: 需要的权限数组
 *   - role: 可选，角色要求
 *   - visibleRoles: 可选，指定哪些角色可见此菜单项
 *
 * - TopLevelMenuItem: 顶级菜单项（如仪表盘）
 *   - title: 菜单标题
 *   - icon: Element Plus 图标名
 *   - path: 路由路径
 *
 * 权限说明:
 * - operator: 运营人员，可访问内容运营、任务调度
 * - editor: 编辑，仅可访问内容管理
 * - viewer: 查看者，仅可查看仪表盘和内容管理
 * - customer: 客户，可查看账号、内容、发布管理
 * - admin: 管理员，拥有所有权限
 *
 * 使用示例:
 * ```javascript
 * import { menuConfig } from '@/router/menu.config'
 *
 * // 根据用户权限过滤菜单
 * const filteredMenu = filterMenuByUser(menuConfig, user)
 * ```
 */

export default menuConfig
