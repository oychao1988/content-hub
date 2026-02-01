/**
 * E2E 测试数据
 *
 * 提供测试用的用户、内容、任务等数据
 */

/**
 * 测试用户数据
 */
export const testUsers = {
  admin: {
    username: 'admin',
    password: 'admin123',
    email: 'admin@example.com',
    role: 'admin',
    expectedName: '系统管理员'
  },
  operator: {
    username: 'operator1',
    password: 'operator123',
    email: 'operator1@example.com',
    role: 'operator',
    expectedName: '测试运营员'
  },
  viewer: {
    username: 'viewer1',
    password: 'viewer123',
    email: 'viewer1@example.com',
    role: 'viewer',
    expectedName: '测试查看员'
  }
}

/**
 * 测试内容数据
 */
export const testContent = {
  draft: {
    title: 'E2E测试内容 - 草稿',
    type: 'article',
    platform_id: 1,
    theme_id: 1,
    writing_style_id: 1,
    content: '# E2E测试内容\n\n这是一个用于E2E测试的内容草稿。\n\n## 测试要点\n\n- 验证内容创建\n- 验证内容编辑\n- 验证内容提交流程'
  },
  publishable: {
    title: 'E2E测试内容 - 可发布',
    type: 'article',
    platform_id: 1,
    theme_id: 1,
    writing_style_id: 1,
    content: '# E2E测试内容 - 可发布\n\n这是一个可以发布的内容。\n\n已经过审核，准备发布。'
  },
  scheduled: {
    title: 'E2E测试内容 - 定时发布',
    type: 'article',
    platform_id: 1,
    theme_id: 1,
    writing_style_id: 1,
    content: '# E2E测试内容 - 定时发布\n\n这是一个定时发布的内容。'
  }
}

/**
 * 测试定时任务数据
 */
export const testTasks = {
  basic: {
    name: 'E2E测试任务',
    description: 'E2E测试任务描述',
    task_type: 'content_generation',
    interval: 30,
    interval_unit: 'minutes',
    config: {
      platform_id: 1,
      theme_id: 1,
      writing_style_id: 1,
      content_count: 1
    }
  },
  complex: {
    name: 'E2E测试任务 - 复杂配置',
    description: '包含完整配置的测试任务',
    task_type: 'content_generation',
    interval: 1,
    interval_unit: 'hours',
    config: {
      platform_id: 1,
      theme_id: 1,
      writing_style_id: 1,
      content_count: 5,
      auto_publish: false,
      require_review: true
    }
  }
}

/**
 * 测试账号数据
 */
export const testAccounts = {
  wechat: {
    name: 'E2E测试微信公众号',
    platform_id: 1,
    account_id: 'e2e_test_wechat',
    config: {
      app_id: 'test_app_id',
      app_secret: 'test_app_secret'
    }
  }
}

/**
 * API URL 配置
 */
export const apiUrls = {
  base: 'http://localhost:8010/api/v1',
  login: '/auth/login',
  logout: '/auth/logout',
  content: '/content',
  scheduler: '/scheduler',
  publishPool: '/publish-pool',
  accounts: '/accounts'
}
