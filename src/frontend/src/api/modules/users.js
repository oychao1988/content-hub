import request from '../../utils/request'

// 获取用户列表
export const getUsers = (params) => {
  return request({
    url: '/users/',
    method: 'get',
    params
  })
}

// 获取用户详情
export const getUser = (id) => {
  return request({
    url: `/users/${id}`,
    method: 'get'
  })
}

// 创建用户
export const createUser = (data) => {
  return request({
    url: '/users/',
    method: 'post',
    data
  })
}

// 更新用户
export const updateUser = (id, data) => {
  return request({
    url: `/users/${id}`,
    method: 'put',
    data
  })
}

// 删除用户
export const deleteUser = (id) => {
  return request({
    url: `/users/${id}`,
    method: 'delete'
  })
}

// 重置用户密码
export const resetUserPassword = (id, data) => {
  return request({
    url: `/users/${id}/reset-password`,
    method: 'post',
    data
  })
}

// 更新用户状态
export const updateUserStatus = (id, status) => {
  return request({
    url: `/users/${id}/status`,
    method: 'patch',
    data: { status }
  })
}
