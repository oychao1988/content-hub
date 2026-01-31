import request from '../../utils/request'
import { silentRequest } from '../../utils/request'

// 登录
export const login = (data) => {
  return request({
    url: '/auth/login',
    method: 'post',
    data
  })
}

// 登出 - 使用静默模式，避免触发响应拦截器的错误提示
export const logout = () => {
  return silentRequest.post('/auth/logout')
}

// 获取当前用户信息
export const getCurrentUser = () => {
  return request({
    url: '/auth/me',
    method: 'get'
  })
}

// 刷新令牌
export const refreshToken = () => {
  return request({
    url: '/auth/refresh',
    method: 'post'
  })
}
