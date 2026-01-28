import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAppStore = defineStore(
  'app',
  () => {
    // 侧边栏状态
    const sidebarOpened = ref(true)

    // 设备类型
    const device = ref('desktop')

    // 主题
    const theme = ref('light')

    // 语言
    const language = ref('zh-CN')

    // 页面加载状态
    const loading = ref(false)

    // 切换侧边栏
    const toggleSidebar = () => {
      sidebarOpened.value = !sidebarOpened.value
    }

    // 关闭侧边栏
    const closeSidebar = () => {
      sidebarOpened.value = false
    }

    // 打开侧边栏
    const openSidebar = () => {
      sidebarOpened.value = true
    }

    // 设置设备类型
    const setDevice = (deviceType) => {
      device.value = deviceType
    }

    // 设置主题
    const setTheme = (themeValue) => {
      theme.value = themeValue
      document.documentElement.setAttribute('data-theme', themeValue)
    }

    // 设置语言
    const setLanguage = (lang) => {
      language.value = lang
    }

    // 设置加载状态
    const setLoading = (status) => {
      loading.value = status
    }

    return {
      // 状态
      sidebarOpened,
      device,
      theme,
      language,
      loading,
      // 方法
      toggleSidebar,
      closeSidebar,
      openSidebar,
      setDevice,
      setTheme,
      setLanguage,
      setLoading
    }
  },
  {
    persist: {
      key: 'app-store',
      storage: localStorage,
      paths: ['sidebarOpened', 'theme', 'language']
    }
  }
)
