import request from '../../utils/request'

// 获取发布记录列表
export const getPublishRecords = (params) => {
  return request({
    url: '/publisher/records',
    method: 'get',
    params
  })
}

// 获取发布记录详情
export const getPublishRecord = (id) => {
  return request({
    url: `/publisher/records/${id}`,
    method: 'get'
  })
}

// 创建发布任务
export const createPublishTask = (data) => {
  return request({
    url: '/publisher/publish',
    method: 'post',
    data
  })
}

// 重试发布
export const retryPublish = (id) => {
  return request({
    url: `/publisher/records/${id}/retry`,
    method: 'post'
  })
}

// 取消发布
export const cancelPublish = (id) => {
  return request({
    url: `/publisher/records/${id}/cancel`,
    method: 'post'
  })
}

// 获取发布统计
export const getPublishStats = (params) => {
  return request({
    url: '/publisher/stats',
    method: 'get',
    params
  })
}
