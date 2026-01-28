import request from '../../utils/request'

// 获取仪表盘统计数据
export const getDashboardStats = () => {
  return request({
    url: '/dashboard/stats',
    method: 'get'
  })
}

// 获取最近活动
export const getRecentActivities = (params) => {
  return request({
    url: '/dashboard/activities',
    method: 'get',
    params
  })
}

// 获取内容趋势数据
export const getContentTrend = (params) => {
  return request({
    url: '/dashboard/content-trend',
    method: 'get',
    params
  })
}

// 获取发布统计
export const getPublishTrend = (params) => {
  return request({
    url: '/dashboard/publish-trend',
    method: 'get',
    params
  })
}
