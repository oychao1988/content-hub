# ContentHub 前端 Bug 报告

## Bug #1: 用户数据结构错误导致权限系统失效

### 严重程度
**高** - 阻断性问题

### 影响范围
- 所有需要权限的页面无法访问
- 影响所有非管理员用户

### 问题描述
用户登录后，`userStore.user` 存储的是完整的 API 响应对象，而不是用户数据对象。

**当前数据结构**:
```javascript
{
  user: {
    success: true,
    data: {
      username: "admin",
      role: "admin",
      permissions: [...]
    },
    error: null,
    meta: null
  }
}
```

**期望数据结构**:
```javascript
{
  user: {
    username: "admin",
    role: "admin",
    permissions: [...]
  }
}
```

### 根本原因
在 `src/frontend/src/stores/modules/user.js:47-56` 的 `getUserInfo` 函数中：

```javascript
const getUserInfo = async () => {
  try {
    const response = await authApi.getCurrentUser()
    user.value = response  // ❌ 错误：存储了整个响应
    permissions.value = response.permissions || []  // ❌ 错误：permissions 未定义
    return response
  } catch (error) {
    console.error('获取用户信息失败:', error)
    throw error
  }
}
```

应该改为：
```javascript
const getUserInfo = async () => {
  try {
    const response = await authApi.getCurrentUser()
    user.value = response.data  // ✅ 正确：只存储用户数据
    permissions.value = response.data.permissions || []
    return response
  } catch (error) {
    console.error('获取用户信息失败:', error)
    throw error
  }
}
```

### 症状
1. `userStore.user?.role` 返回 `undefined`
2. `isAdmin` 计算属性返回 `false`（即使 admin 用户）
3. `hasPermission` 和 `hasAnyPermission` 方法检查失败
4. 所有需要权限的页面显示 403 错误

### 复现步骤
1. 使用任意账号登录
2. 尝试访问任何需要权限的页面（如 /accounts, /content, /platforms 等）
3. 页面重定向到 403

### 受影响的路由
- `/accounts` - 账号管理
- `/content` - 内容管理
- `/content/:id` - 内容详情
- `/publisher` - 发布管理
- `/scheduler` - 定时任务
- `/publish-pool` - 发布池
- `/users` - 用户管理
- `/customers` - 客户管理
- `/platforms` - 平台管理
- `/config` - 系统配置
- `/writing-styles` - 写作风格管理
- `/content-themes` - 内容主题管理

### 修复方案
修改 `src/frontend/src/stores/modules/user.js` 中的 `getUserInfo` 函数：

**文件**: `src/frontend/src/stores/modules/user.js:47-56`

```javascript
// 获取用户信息
const getUserInfo = async () => {
  try {
    const response = await authApi.getCurrentUser()
    user.value = response.data  // 修改这里
    permissions.value = response.data.permissions || []  // 修改这里
    return response
  } catch (error) {
    console.error('获取用户信息失败:', error)
    throw error
  }
}
```

### 验证方法
修复后：
1. 清除浏览器 localStorage
2. 重新登录
3. 访问需要权限的页面（如 /accounts）
4. 确认页面正常显示

### 发现时间
2026-01-29

### 发现者
Claude Code 自动化测试
