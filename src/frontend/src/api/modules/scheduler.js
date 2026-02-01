import request from '../../utils/request'

// 获取定时任务列表
export const getSchedulerTasks = (params) => {
  return request({
    url: '/scheduler/tasks',
    method: 'get',
    params
  })
}

// 获取定时任务详情
export const getSchedulerTask = (id) => {
  return request({
    url: `/scheduler/tasks/${id}`,
    method: 'get'
  })
}

// 创建定时任务
export const createSchedulerTask = (data) => {
  return request({
    url: '/scheduler/tasks',
    method: 'post',
    data
  })
}

// 更新定时任务
export const updateSchedulerTask = (id, data) => {
  return request({
    url: `/scheduler/tasks/${id}`,
    method: 'put',
    data
  })
}

// 删除定时任务
export const deleteSchedulerTask = (id) => {
  return request({
    url: `/scheduler/tasks/${id}`,
    method: 'delete'
  })
}

// 启动定时任务
export const startTask = (id) => {
  return request({
    url: `/scheduler/tasks/${id}/start`,
    method: 'post'
  })
}

// 停止定时任务
export const stopTask = (id) => {
  return request({
    url: `/scheduler/tasks/${id}/stop`,
    method: 'post'
  })
}

// 暂停定时任务
export const pauseTask = (id) => {
  return request({
    url: `/scheduler/tasks/${id}/pause`,
    method: 'post'
  })
}

// 恢复定时任务
export const resumeTask = (id) => {
  return request({
    url: `/scheduler/tasks/${id}/resume`,
    method: 'post'
  })
}

// 立即执行任务
export const executeTask = (id) => {
  return request({
    url: `/scheduler/tasks/${id}/trigger`,
    method: 'post'
  })
}

// 获取任务执行历史
export const getTaskHistory = (id, params) => {
  return request({
    url: `/scheduler/tasks/${id}/history`,
    method: 'get',
    params
  })
}
