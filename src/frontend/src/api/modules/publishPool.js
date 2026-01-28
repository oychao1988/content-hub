import request from '../../utils/request'

// 获取发布池列表
export const getPublishPool = (params) => {
  return request({
    url: '/publish-pool/',
    method: 'get',
    params
  })
}

// 获取发布池项详情
export const getPublishPoolItem = (id) => {
  return request({
    url: `/publish-pool/${id}`,
    method: 'get'
  })
}

// 添加到发布池
export const addToPublishPool = (data) => {
  return request({
    url: '/publish-pool/',
    method: 'post',
    data
  })
}

// 更新发布池项
export const updatePublishPoolItem = (id, data) => {
  return request({
    url: `/publish-pool/${id}`,
    method: 'put',
    data
  })
}

// 删除发布池项
export const deletePublishPoolItem = (id) => {
  return request({
    url: `/publish-pool/${id}`,
    method: 'delete'
  })
}

// 批量删除发布池项
export const batchDeletePublishPoolItems = (ids) => {
  return request({
    url: '/publish-pool/batch',
    method: 'delete',
    data: { ids }
  })
}

// 批量发布
export const batchPublish = (data) => {
  return request({
    url: '/publish-pool/publish',
    method: 'post',
    data
  })
}

// 清空已发布项
export const clearPublished = () => {
  return request({
    url: '/publish-pool/clear',
    method: 'post'
  })
}
