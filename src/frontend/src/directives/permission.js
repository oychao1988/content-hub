/**
 * 权限控制指令
 * 提供 v-permission 和 v-role 指令用于控制元素显示
 */
import { useUserStore } from '../stores/modules/user'

/**
 * 权限指令 - v-permission
 * 用法: v-permission="'account:create'" 或 v-permission="['account:create', 'account:update']"
 */
export const permissionDirective = {
  mounted(el, binding) {
    const { value } = binding
    const userStore = useUserStore()

    if (value) {
      const permissions = Array.isArray(value) ? value : [value]
      const hasPermission = userStore.hasAnyPermission(permissions)

      if (!hasPermission) {
        // 移除元素
        el.parentNode && el.parentNode.removeChild(el)
      }
    } else {
      throw new Error('v-permission 需要指定权限，如 v-permission="\'account:create\'"')
    }
  }
}

/**
 * 角色指令 - v-role
 * 用法: v-role="'admin'" 或 v-role="['admin', 'operator']"
 */
export const roleDirective = {
  mounted(el, binding) {
    const { value } = binding
    const userStore = useUserStore()

    if (value) {
      const roles = Array.isArray(value) ? value : [value]
      const hasRole = roles.includes(userStore.user?.role)

      if (!hasRole) {
        // 移除元素
        el.parentNode && el.parentNode.removeChild(el)
      }
    } else {
      throw new Error('v-role 需要指定角色，如 v-role="\'admin\'"')
    }
  }
}

/**
 * 注册所有权限指令
 */
export function setupPermissionDirectives(app) {
  app.directive('permission', permissionDirective)
  app.directive('role', roleDirective)
}
