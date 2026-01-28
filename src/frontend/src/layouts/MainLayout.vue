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
        <template v-for="route in menuRoutes" :key="route.path">
          <el-menu-item
            v-if="!route.meta?.role || userStore.isAdmin"
            :index="route.path"
            :route="route.path"
          >
            <el-icon>
              <component :is="route.meta?.icon" />
            </el-icon>
            <template #title>{{ route.meta?.title }}</template>
          </el-menu-item>
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
  ArrowDown
} from '@element-plus/icons-vue'

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

// 菜单路由（从路由配置中提取）
const menuRoutes = computed(() => {
  return router.getRoutes().filter(route => {
    return route.meta?.title && !route.meta?.requiresAuth === false && route.path !== '/'
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
