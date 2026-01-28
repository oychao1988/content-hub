import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/modules/user'
import config from '../config'

// 创建 axios 实例
const request = axios.create({
  baseURL: config.apiBaseUrl + config.apiVersion,
  timeout: config.timeout,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const userStore = useUserStore()

    // 添加认证 token
    if (userStore.token) {
      config.headers.Authorization = `Bearer ${userStore.token}`
    }

    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    const userStore = useUserStore()

    if (error.response) {
      const { status, data } = error.response

      switch (status) {
        case 401:
          // 未授权，清除 token 并跳转登录
          ElMessage.error('登录已过期，请重新登录')
          userStore.logout()
          window.location.href = '/login'
          break

        case 403:
          ElMessage.error('没有权限访问此资源')
          break

        case 404:
          ElMessage.error('请求的资源不存在')
          break

        case 422:
          // 表单验证错误
          const errors = data.detail
          if (Array.isArray(errors)) {
            const errorMessages = errors.map(err => err.msg).join(', ')
            ElMessage.error(errorMessages)
          } else {
            ElMessage.error(data.message || '请求参数错误')
          }
          break

        case 500:
          ElMessage.error('服务器内部错误，请稍后重试')
          break

        default:
          ElMessage.error(data.message || '请求失败')
      }
    } else if (error.request) {
      // 请求已发送但没有收到响应
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      // 请求配置错误
      ElMessage.error('请求配置错误')
    }

    return Promise.reject(error)
  }
)

export default request
