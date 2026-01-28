import request from '../../utils/request'

// 获取平台列表
export const getPlatforms = (params) => {
  return request({
    url: '/platforms/',
    method: 'get',
    params
  })
}

// 获取平台详情
export const getPlatform = (id) => {
  return request({
    url: `/platforms/${id}`,
    method: 'get'
  })
}

// 创建平台
export const createPlatform = (data) => {
  return request({
    url: '/platforms/',
    method: 'post',
    data
  })
}

// 更新平台
export const updatePlatform = (id, data) => {
  return request({
    url: `/platforms/${id}`,
    method: 'put',
    data
  })
}

// 删除平台
export const deletePlatform = (id) => {
  return request({
    url: `/platforms/${id}`,
    method: 'delete'
  })
}

// 获取平台配置
export const getPlatformConfig = (id) => {
  return request({
    url: `/platforms/${id}/config`,
    method: 'get'
  })
}
