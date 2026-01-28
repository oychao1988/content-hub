import request from '../../utils/request'

// 获取账号列表
export const getAccounts = (params) => {
  return request({
    url: '/accounts/',
    method: 'get',
    params
  })
}

// 获取账号详情
export const getAccount = (id) => {
  return request({
    url: `/accounts/${id}`,
    method: 'get'
  })
}

// 创建账号
export const createAccount = (data) => {
  return request({
    url: '/accounts/',
    method: 'post',
    data
  })
}

// 更新账号
export const updateAccount = (id, data) => {
  return request({
    url: `/accounts/${id}`,
    method: 'put',
    data
  })
}

// 删除账号
export const deleteAccount = (id) => {
  return request({
    url: `/accounts/${id}`,
    method: 'delete'
  })
}

// 批量删除账号
export const batchDeleteAccounts = (ids) => {
  return request({
    url: '/accounts/batch',
    method: 'delete',
    data: { ids }
  })
}

// 同步账号状态
export const syncAccount = (id) => {
  return request({
    url: `/accounts/${id}/sync`,
    method: 'post'
  })
}
