import request from '../../utils/request'

// ============= 写作风格相关 API =============

// 获取写作风格列表
export const getWritingStyles = (params) => {
  return request({
    url: '/config/writing-styles',
    method: 'get',
    params
  })
}

// 获取写作风格详情
export const getWritingStyle = (id) => {
  return request({
    url: `/config/writing-styles/${id}`,
    method: 'get'
  })
}

// 创建写作风格
export const createWritingStyle = (data) => {
  return request({
    url: '/config/writing-styles',
    method: 'post',
    data
  })
}

// 更新写作风格
export const updateWritingStyle = (id, data) => {
  return request({
    url: `/config/writing-styles/${id}`,
    method: 'put',
    data
  })
}

// 删除写作风格
export const deleteWritingStyle = (id) => {
  return request({
    url: `/config/writing-styles/${id}`,
    method: 'delete'
  })
}

// ============= 内容主题相关 API =============

// 获取内容主题列表
export const getContentThemes = (params) => {
  return request({
    url: '/config/content-themes',
    method: 'get',
    params
  })
}

// 获取内容主题详情
export const getContentTheme = (id) => {
  return request({
    url: `/config/content-themes/${id}`,
    method: 'get'
  })
}

// 创建内容主题
export const createContentTheme = (data) => {
  return request({
    url: '/config/content-themes',
    method: 'post',
    data
  })
}

// 更新内容主题
export const updateContentTheme = (id, data) => {
  return request({
    url: `/config/content-themes/${id}`,
    method: 'put',
    data
  })
}

// 删除内容主题
export const deleteContentTheme = (id) => {
  return request({
    url: `/config/content-themes/${id}`,
    method: 'delete'
  })
}
