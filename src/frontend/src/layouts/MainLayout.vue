<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="sidebarWidth" class="layout-aside">
      <div class="logo">
        <img src="/logo.svg" alt="ContentHub" />
        <span v-show="appStore.sidebarOpened">ContentHub</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="!appStore.sidebarOpened"
        :unique-opened="true"
        router
        class="sidebar-menu"
      >
        <template v-for="menu in filteredMenus" :key="menu.path || menu.title">
          <!-- 顶级菜单项（如仪表盘） -->
          <el-menu-item
            v-if="!menu.isSubmenu"
            :index="menu.path"
            :route="menu.path"
          >
            <el-icon>
              <component :is="menu.icon" />
            </el-icon>
            <template #title>{{ menu.title }}</template>
          </el-menu-item>

          <!-- 分组菜单 -->
          <el-sub-menu v-else :index="menu.title">
            <template #title>
              <el-icon>
                <component :is="menu.icon" />
              </el-icon>
              <span>{{ menu.title }}</span>
            </template>
            <el-menu-item
              v-for="item in menu.items"
              :key="item.path"
              :index="item.path"
              :route="item.path"
            >
              <el-icon>
                <component :is="item.icon" />
              </el-icon>
              <template #title>{{ item.title }}</template>
            </el-menu-item>
          </el-sub-menu>
        </template>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container class="layout-main">
      <!-- 顶栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-button
            link
            @click="appStore.toggleSidebar"
            class="sidebar-toggle"
          >
            <el-icon :size="20">
              <Fold v-if="appStore.sidebarOpened" />
              <Expand v-else />
            </el-icon>
          </el-button>
          <el-breadcrumb separator="/">
            <el-breadcrumb-item
              v-for="item in breadcrumbs"
              :key="item.path"
              :to="item.path"
            >
              {{ item.meta?.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-dropdown @command="handleCommand">
            <span class="user-dropdown">
              <el-avatar :size="32" :icon="UserFilled" />
              <span class="username">{{ userStore.userName }}</span>
              <el-icon class="el-icon--right">
                <ArrowDown />
              </el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  个人资料
                </el-dropdown-item>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided command="logout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="layout-content">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAppStore } from '../stores/modules/app'
import { useUserStore } from '../stores/modules/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Fold,
  Expand,
  UserFilled,
  User,
  Setting,
  SwitchButton,
  ArrowDown,
  DataBoard,
  Document,
  Promotion,
  Box,
  Timer,
  OfficeBuilding,
  Monitor,
  EditPen,
  CollectionTag
} from '@element-plus/icons-vue'
import menuConfig from '../router/menu.config.js'

const route = useRoute()
const router = useRouter()
const appStore = useAppStore()
const userStore = useUserStore()

// 侧边栏宽度
const sidebarWidth = computed(() => {
  return appStore.sidebarOpened ? '200px' : '64px'
})

// 当前激活的菜单
const activeMenu = computed(() => {
  return route.path
})

/**
 * 检查单个菜单项是否有权限访问
 * @param {Object} menu - 菜单项配置
 * @returns {Boolean} - 是否有权限
 */
const checkMenuPermission = (menu) => {
  // 检查 role 属性
  if (menu.role && menu.role !== userStore.user?.role) {
    return false
  }

  // 检查 permissions 属性（满足任意一个即可）
  if (menu.permissions && menu.permissions.length > 0) {
    return userStore.hasAnyPermission(menu.permissions)
  }

  // 检查 visibleRoles 属性（当前角色是否在可见角色列表中）
  if (menu.visibleRoles && menu.visibleRoles.length > 0) {
    return menu.visibleRoles.includes(userStore.user?.role)
  }

  // 没有权限限制，默认可见
  return true
}

/**
 * 过滤后的菜单配置
 * - 对顶级菜单项进行权限检查
 * - 对分组菜单进行权限检查，并过滤其子菜单项
 * - 如果分组菜单的所有子菜单都无权限，则不显示该分组
 */
const filteredMenus = computed(() => {
  return menuConfig.filter(menu => {
    // 顶级菜单项（如仪表盘）
    if (!menu.isSubmenu) {
      return checkMenuPermission(menu)
    }

    // 分组菜单：需要检查分组本身的权限
    if (!checkMenuPermission(menu)) {
      return false
    }

    // 过滤分组下的子菜单项
    const filteredItems = menu.items.filter(item => checkMenuPermission(item))

    // 如果分组下没有任何有权限的子菜单，则不显示该分组
    if (filteredItems.length === 0) {
      return false
    }

    // 更新菜单的子菜单项为过滤后的结果
    menu.items = filteredItems
    return true
  })
})

// 面包屑导航
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta?.title)
  return matched
})

// 处理下拉菜单命令
const handleCommand = async (command) => {
  switch (command) {
    case 'profile':
      // 跳转到个人资料页面
      router.push('/profile')
      break
    case 'settings':
      // 跳转到系统设置页面
      if (userStore.isAdmin) {
        router.push('/config')
      } else {
        ElMessage.warning('只有管理员可以访问系统设置')
      }
      break
    case 'logout':
      try {
        await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
        await userStore.logout()
        router.push('/login')
        ElMessage.success('已退出登录')
      } catch (error) {
        // 用户取消
      }
      break
  }
}
</script>

<style scoped>
.main-layout {
  height: 100vh;
}

.layout-aside {
  background: #304156;
  transition: width 0.3s;
  overflow-x: hidden;
}

.logo {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.logo img {
  width: 32px;
  height: 32px;
}

.sidebar-menu {
  border-right: none;
  background: #304156;
}

.sidebar-menu:not(.el-menu--collapse) {
  width: 200px;
}

.layout-main {
  display: flex;
  flex-direction: column;
}

.layout-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 20px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 20px;
}

.sidebar-toggle {
  font-size: 20px;
  color: #606266;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}

.user-dropdown {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.user-dropdown:hover {
  background: #f5f7fa;
}

.username {
  font-size: 14px;
  color: #606266;
}

.layout-content {
  background: #f0f2f5;
  padding: 20px;
  overflow-y: auto;
}

/* 页面切换动画 */
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>
