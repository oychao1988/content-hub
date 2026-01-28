import request from '../../utils/request'

// 获取客户列表
export const getCustomers = (params) => {
  return request({
    url: '/customers/',
    method: 'get',
    params
  })
}

// 获取客户详情
export const getCustomer = (id) => {
  return request({
    url: `/customers/${id}`,
    method: 'get'
  })
}

// 创建客户
export const createCustomer = (data) => {
  return request({
    url: '/customers/',
    method: 'post',
    data
  })
}

// 更新客户
export const updateCustomer = (id, data) => {
  return request({
    url: `/customers/${id}`,
    method: 'put',
    data
  })
}

// 删除客户
export const deleteCustomer = (id) => {
  return request({
    url: `/customers/${id}`,
    method: 'delete'
  })
}

// 批量删除客户
export const batchDeleteCustomers = (ids) => {
  return request({
    url: '/customers/batch',
    method: 'delete',
    data: { ids }
  })
}
