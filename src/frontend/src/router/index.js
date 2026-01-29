import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '../stores/modules/user'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../pages/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: () => import('../pages/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'Dashboard' }
      },
      {
        path: 'accounts',
        name: 'Accounts',
        component: () => import('../pages/AccountManage.vue'),
        meta: { title: '账号管理', icon: 'User', permissions: ['accounts:read'] }
      },
      {
        path: 'content',
        name: 'Content',
        component: () => import('../pages/ContentManage.vue'),
        meta: { title: '内容管理', icon: 'Document', permissions: ['content:read'] }
      },
      {
        path: 'publisher',
        name: 'Publisher',
        component: () => import('../pages/PublishManage.vue'),
        meta: { title: '发布管理', icon: 'Promotion', permissions: ['publisher:read'] }
      },
      {
        path: 'scheduler',
        name: 'Scheduler',
        component: () => import('../pages/SchedulerManage.vue'),
        meta: { title: '定时任务', icon: 'Timer', permissions: ['scheduler:read'] }
      },
      {
        path: 'publish-pool',
        name: 'PublishPool',
        component: () => import('../pages/PublishPool.vue'),
        meta: { title: '发布池', icon: 'Box', permissions: ['publish-pool:read'] }
      },
      // 管理员专属路由
      {
        path: 'users',
        name: 'Users',
        component: () => import('../pages/UserManage.vue'),
        meta: { title: '用户管理', icon: 'UserFilled', permissions: ['users:read'], role: 'admin' }
      },
      {
        path: 'customers',
        name: 'Customers',
        component: () => import('../pages/CustomerManage.vue'),
        meta: { title: '客户管理', icon: 'OfficeBuilding', permissions: ['customers:read'], role: 'admin' }
      },
      {
        path: 'platforms',
        name: 'Platforms',
        component: () => import('../pages/PlatformManage.vue'),
        meta: { title: '平台管理', icon: 'Platform', permissions: ['platforms:read'], role: 'admin' }
      },
      {
        path: 'config',
        name: 'Config',
        component: () => import('../pages/SystemConfig.vue'),
        meta: { title: '系统配置', icon: 'Setting', permissions: ['config:read'], role: 'admin' }
      },
      {
        path: 'writing-styles',
        name: 'WritingStyles',
        component: () => import('../pages/WritingStyleManage.vue'),
        meta: { title: '写作风格管理', icon: 'EditPen', permissions: ['config:read'], role: 'admin' }
      },
      {
        path: 'content-themes',
        name: 'ContentThemes',
        component: () => import('../pages/ContentThemeManage.vue'),
        meta: { title: '内容主题管理', icon: 'CollectionTag', permissions: ['config:read'], role: 'admin' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const userStore = useUserStore()

  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - ContentHub` : 'ContentHub'

  // 检查是否需要认证
  if (to.meta.requiresAuth && !userStore.isAuthenticated) {
    next({
      name: 'Login',
      query: { redirect: to.fullPath }
    })
    return
  }

  // 检查权限
  if (to.meta.permissions) {
    const hasPermission = to.meta.permissions.some(permission =>
      userStore.user?.permissions?.includes(permission)
    )
    if (!hasPermission) {
      next({ name: 'Dashboard' })
      return
    }
  }

  // 检查角色
  if (to.meta.role && userStore.user?.role !== to.meta.role) {
    next({ name: 'Dashboard' })
    return
  }

  next()
})

export default router
