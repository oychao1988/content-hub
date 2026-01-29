# ContentHub 权限控制系统使用指南

## 概述

ContentHub 使用基于角色的访问控制（RBAC）系统，支持三个角色：
- **admin**: 系统管理员，拥有所有权限
- **operator**: 运营人员，拥有内容和发布管理权限
- **customer**: 客户，只有只读权限

## 后端权限使用

### 1. 权限枚举

在 `app/core/permissions.py` 中定义了所有权限：

```python
class Permission(str, Enum):
    # 账号管理
    ACCOUNT_READ = "account:read"
    ACCOUNT_CREATE = "account:create"
    ACCOUNT_UPDATE = "account:update"
    ACCOUNT_DELETE = "account:delete"

    # 内容管理
    CONTENT_READ = "content:read"
    CONTENT_CREATE = "content:create"
    CONTENT_UPDATE = "content:update"
    CONTENT_DELETE = "content:delete"
    CONTENT_PUBLISH = "content:publish"

    # ... 更多权限
```

### 2. 使用权限装饰器

```python
from app.core.permissions import require_permission, Permission
from app.modules.shared.deps import get_current_user

@router.get("/accounts")
@require_permission(Permission.ACCOUNT_READ)
async def get_accounts(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """获取账号列表 - 需要 account:read 权限"""
    return account_service.get_account_list(db)

@router.post("/accounts")
@require_permission(Permission.ACCOUNT_CREATE)
async def create_account(
    account: AccountCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """创建账号 - 需要 account:create 权限"""
    return account_service.create_account(db, account.dict())
```

### 3. 使用角色装饰器

```python
from app.core.permissions import require_role

@router.delete("/accounts/{id}")
@require_role("admin")
async def delete_account(
    id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """删除账号 - 仅管理员可操作"""
    return account_service.delete_account(db, id)
```

### 4. 多权限检查（满足任意一个）

```python
@require_permission(Permission.ACCOUNT_CREATE, Permission.ACCOUNT_UPDATE)
async def operation():
    """需要拥有 account:create 或 account:update 其中一个权限"""
    pass
```

### 5. 多权限检查（必须满足所有）

```python
from app.core.permissions import require_all_permissions

@require_all_permissions(Permission.ACCOUNT_CREATE, Permission.ACCOUNT_UPDATE)
async def operation():
    """必须同时拥有 account:create 和 account:update 权限"""
    pass
```

## 前端权限使用

### 1. 使用权限指令 - v-permission

```vue
<template>
  <!-- 单个权限 -->
  <el-button v-permission="'account:create'">创建账号</el-button>

  <!-- 多个权限（满足任意一个） -->
  <el-button v-permission="['account:create', 'account:update']">
    操作
  </el-button>
</template>
```

### 2. 使用角色指令 - v-role

```vue
<template>
  <!-- 单个角色 -->
  <el-button v-role="'admin'">管理员操作</el-button>

  <!-- 多个角色（满足任意一个） -->
  <el-button v-role="['admin', 'operator']">
    管理员或运营人员操作
  </el-button>
</template>
```

### 3. 使用 PermissionButton 组件

```vue
<template>
  <!-- 基础用法 -->
  <PermissionButton permission="account:create" type="primary" @click="handleCreate">
    创建账号
  </PermissionButton>

  <!-- 多个权限（满足任意一个） -->
  <PermissionButton
    :permission="['account:create', 'account:update']"
    type="primary"
    @click="handleOperation"
  >
    操作
  </PermissionButton>

  <!-- 多个权限（必须满足所有） -->
  <PermissionButton
    :permission="['account:create', 'account:update']"
    :require-all="true"
    type="primary"
    @click="handleOperation"
  >
    高级操作
  </PermissionButton>
</template>

<script setup>
import PermissionButton from '@/components/PermissionButton.vue'

const handleCreate = () => {
  // 处理创建逻辑
}

const handleOperation = () => {
  // 处理操作逻辑
}
</script>
```

### 4. 在脚本中检查权限

```javascript
import { useUserStore } from '@/stores/modules/user'

const userStore = useUserStore()

// 检查单个权限
if (userStore.hasPermission('account:create')) {
  // 有权限
}

// 检查多个权限（满足任意一个）
if (userStore.hasAnyPermission(['account:create', 'account:update'])) {
  // 有权限
}

// 检查多个权限（必须满足所有）
if (userStore.hasAllPermissions(['account:create', 'account:update'])) {
  // 有权限
}

// 检查角色
if (userStore.isAdmin) {
  // 是管理员
}
```

### 5. 路由权限配置

```javascript
{
  path: 'accounts',
  name: 'Accounts',
  component: () => import('../pages/AccountManage.vue'),
  meta: {
    title: '账号管理',
    icon: 'User',
    permissions: ['account:read']  // 需要的权限
  }
}

// 管理员专属路由
{
  path: 'users',
  name: 'Users',
  component: () => import('../pages/UserManage.vue'),
  meta: {
    title: '用户管理',
    icon: 'UserFilled',
    permissions: ['user:read'],
    role: 'admin'  // 需要的角色
  }
}
```

## 权限列表

### 账号管理权限
- `account:read` - 查看账号
- `account:create` - 创建账号
- `account:update` - 更新账号
- `account:delete` - 删除账号

### 内容管理权限
- `content:read` - 查看内容
- `content:create` - 创建内容
- `content:update` - 更新内容
- `content:delete` - 删除内容
- `content:publish` - 发布内容

### 发布管理权限
- `publisher:read` - 查看发布配置
- `publisher:execute` - 执行发布
- `publisher:config` - 配置发布参数

### 定时任务权限
- `scheduler:read` - 查看定时任务
- `scheduler:create` - 创建定时任务
- `scheduler:update` - 更新定时任务
- `scheduler:delete` - 删除定时任务
- `scheduler:execute` - 执行定时任务

### 发布池权限
- `publish-pool:read` - 查看发布池
- `publish-pool:execute` - 执行发布池任务

### 用户管理权限（仅管理员）
- `user:read` - 查看用户
- `user:create` - 创建用户
- `user:update` - 更新用户
- `user:delete` - 删除用户

### 客户管理权限（仅管理员）
- `customer:read` - 查看客户
- `customer:create` - 创建客户
- `customer:update` - 更新客户
- `customer:delete` - 删除客户

### 平台管理权限（仅管理员）
- `platform:read` - 查看平台
- `platform:create` - 创建平台
- `platform:update` - 更新平台
- `platform:delete` - 删除平台

### 系统配置权限（仅管理员）
- `config:read` - 查看配置
- `config:update` - 更新配置
- `writing-style:read` - 查看写作风格
- `writing-style:create` - 创建写作风格
- `writing-style:update` - 更新写作风格
- `writing-style:delete` - 删除写作风格
- `content-theme:read` - 查看内容主题
- `content-theme:create` - 创建内容主题
- `content-theme:update` - 更新内容主题
- `content-theme:delete` - 删除内容主题

## 角色权限对照表

| 权限 | admin | operator | customer |
|------|-------|----------|----------|
| account:read | ✅ | ✅ | ✅ |
| account:create | ✅ | ✅ | ❌ |
| account:update | ✅ | ✅ | ❌ |
| account:delete | ✅ | ❌ | ❌ |
| content:read | ✅ | ✅ | ✅ |
| content:create | ✅ | ✅ | ❌ |
| content:update | ✅ | ✅ | ❌ |
| content:delete | ✅ | ✅ | ❌ |
| content:publish | ✅ | ✅ | ❌ |
| publisher:read | ✅ | ✅ | ✅ |
| publisher:execute | ✅ | ✅ | ❌ |
| publisher:config | ✅ | ✅ | ❌ |
| scheduler:read | ✅ | ✅ | ✅ |
| scheduler:create | ✅ | ✅ | ❌ |
| scheduler:update | ✅ | ✅ | ❌ |
| scheduler:delete | ✅ | ✅ | ❌ |
| scheduler:execute | ✅ | ✅ | ❌ |
| publish-pool:read | ✅ | ✅ | ✅ |
| publish-pool:execute | ✅ | ✅ | ❌ |
| user:read | ✅ | ❌ | ❌ |
| user:create | ✅ | ❌ | ❌ |
| user:update | ✅ | ❌ | ❌ |
| user:delete | ✅ | ❌ | ❌ |
| customer:read | ✅ | ❌ | ❌ |
| customer:create | ✅ | ❌ | ❌ |
| customer:update | ✅ | ❌ | ❌ |
| customer:delete | ✅ | ❌ | ❌ |
| platform:read | ✅ | ❌ | ❌ |
| platform:create | ✅ | ❌ | ❌ |
| platform:update | ✅ | ❌ | ❌ |
| platform:delete | ✅ | ❌ | ❌ |
| config:read | ✅ | ❌ | ❌ |
| config:update | ✅ | ❌ | ❌ |
| writing-style:read | ✅ | ❌ | ❌ |
| writing-style:create | ✅ | ❌ | ❌ |
| writing-style:update | ✅ | ❌ | ❌ |
| writing-style:delete | ✅ | ❌ | ❌ |
| content-theme:read | ✅ | ❌ | ❌ |
| content-theme:create | ✅ | ❌ | ❌ |
| content-theme:update | ✅ | ❌ | ❌ |
| content-theme:delete | ✅ | ❌ | ❌ |

## 最佳实践

1. **后端优先**: 始终在后端验证权限，前端权限控制仅用于 UI 优化
2. **最小权限原则**: 只授予用户完成工作所需的最小权限
3. **权限命名**: 使用 `resource:operation` 格式，保持一致性
4. **错误处理**: 当用户权限不足时，返回友好的错误提示
5. **测试覆盖**: 为权限控制编写单元测试和集成测试

## 示例：完整的 CRUD 页面

```vue
<template>
  <div class="account-manage">
    <page-header title="账号管理" icon="User">
      <!-- 创建按钮 - admin 和 operator -->
      <el-button
        v-permission="['account:create']"
        type="primary"
        :icon="Plus"
        @click="handleCreate"
      >
        新建账号
      </el-button>
    </page-header>

    <!-- 数据表格 -->
    <data-table :data="tableData" :loading="loading">
      <el-table-column prop="name" label="账号名称" />
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <!-- 查看按钮 - 所有角色 -->
          <el-button link type="primary" @click="handleView(row)">
            查看
          </el-button>

          <!-- 编辑按钮 - admin 和 operator -->
          <el-button
            v-permission="['account:update']"
            link
            type="primary"
            @click="handleEdit(row)"
          >
            编辑
          </el-button>

          <!-- 删除按钮 - 仅 admin -->
          <el-button
            v-role="'admin'"
            link
            type="danger"
            @click="handleDelete(row)"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </data-table>

    <!-- 或者使用 PermissionButton 组件 -->
    <PermissionButton
      permission="account:create"
      type="primary"
      @click="handleCreate"
    >
      新建账号
    </PermissionButton>
  </div>
</template>

<script setup>
import { useUserStore } from '@/stores/modules/user'
import PermissionButton from '@/components/PermissionButton.vue'

const userStore = useUserStore()

const handleCreate = () => {
  // 检查权限的另一种方式
  if (!userStore.hasPermission('account:create')) {
    ElMessage.error('您没有创建账号的权限')
    return
  }
  // 执行创建逻辑
}
</script>
```
