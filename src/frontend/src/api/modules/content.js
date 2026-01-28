import request from '../../utils/request'

// 获取内容列表
export const getContentList = (params) => {
  return request({
    url: '/content/',
    method: 'get',
    params
  })
}

// 获取内容详情
export const getContent = (id) => {
  return request({
    url: `/content/${id}`,
    method: 'get'
  })
}

// 创建内容
export const createContent = (data) => {
  return request({
    url: '/content/',
    method: 'post',
    data
  })
}

// 更新内容
export const updateContent = (id, data) => {
  return request({
    url: `/content/${id}`,
    method: 'put',
    data
  })
}

// 删除内容
export const deleteContent = (id) => {
  return request({
    url: `/content/${id}`,
    method: 'delete'
  })
}

// 批量删除内容
export const batchDeleteContent = (ids) => {
  return request({
    url: '/content/batch',
    method: 'delete',
    data: { ids }
  })
}

// 生成内容
export const generateContent = (data) => {
  return request({
    url: '/content/generate',
    method: 'post',
    data,
    timeout: 120000 // 内容生成可能需要较长时间
  })
}

// 获取内容统计
export const getContentStats = () => {
  return request({
    url: '/content/stats',
    method: 'get'
  })
}
