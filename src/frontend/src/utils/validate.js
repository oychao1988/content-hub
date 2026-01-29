/**
 * 通用表单验证规则模块
 * 提供可复用的验证函数和 Element Plus 兼容的验证规则生成器
 */

/**
 * 必填验证
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function required(message = '此项为必填项', trigger = 'blur') {
  return {
    required: true,
    message,
    trigger
  }
}

/**
 * 邮箱格式验证
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function email(message = '请输入正确的邮箱格式', trigger = 'blur') {
  return {
    type: 'email',
    message,
    trigger
  }
}

/**
 * 手机号验证（中国大陆）
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function phone(message = '请输入正确的手机号', trigger = 'blur') {
  return {
    pattern: /^1[3-9]\d{9}$/,
    message,
    trigger
  }
}

/**
 * URL 格式验证
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function url(message = '请输入正确的 URL 格式', trigger = 'blur') {
  return {
    pattern: /^(https?:\/\/)?([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w \.-]*)*\/?$/,
    message,
    trigger
  }
}

/**
 * 最小长度验证
 * @param {number} min - 最小长度
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function minLength(min, message, trigger = 'blur') {
  return {
    min,
    message: message || `长度不能少于 ${min} 个字符`,
    trigger
  }
}

/**
 * 最大长度验证
 * @param {number} max - 最大长度
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function maxLength(max, message, trigger = 'blur') {
  return {
    max,
    message: message || `长度不能超过 ${max} 个字符`,
    trigger
  }
}

/**
 * 长度范围验证
 * @param {number} min - 最小长度
 * @param {number} max - 最大长度
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function lengthRange(min, max, message, trigger = 'blur') {
  return {
    min,
    max,
    message: message || `长度在 ${min} 到 ${max} 个字符`,
    trigger
  }
}

/**
 * 数值范围验证
 * @param {number} min - 最小值
 * @param {number} max - 最大值
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function range(min, max, message, trigger = 'blur') {
  return {
    type: 'number',
    min,
    max,
    message: message || `数值在 ${min} 到 ${max} 之间`,
    trigger
  }
}

/**
 * 正则表达式验证
 * @param {RegExp} pattern - 正则表达式
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function pattern(pattern, message, trigger = 'blur') {
  return {
    pattern,
    message,
    trigger
  }
}

/**
 * 代码格式验证（字母、数字、下划线）
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function codeFormat(message = '只能包含字母、数字和下划线', trigger = 'blur') {
  return {
    pattern: /^[a-zA-Z0-9_]+$/,
    message,
    trigger
  }
}

/**
 * 目录名格式验证（字母、数字、下划线、中划线）
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function dirNameFormat(message = '只能包含字母、数字、下划线和中划线', trigger = 'blur') {
  return {
    pattern: /^[a-zA-Z0-9_-]+$/,
    message,
    trigger
  }
}

/**
 * 确认匹配验证（如密码确认）
 * @param {string} targetField - 目标字段名
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function confirm(targetField, message = '两次输入不一致', trigger = 'blur') {
  return {
    validator: (rule, value, callback, source, options) => {
      if (!value) {
        callback()
        return
      }
      if (value !== source[targetField]) {
        callback(new Error(message))
      } else {
        callback()
      }
    },
    trigger
  }
}

/**
 * 密码强度验证（必须包含大小写字母和数字）
 * @param {string} message - 错误提示信息
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function passwordStrength(message = '密码必须包含大小写字母和数字', trigger = 'blur') {
  return {
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
        return
      }
      // 检查是否包含大写字母、小写字母和数字
      const hasUpperCase = /[A-Z]/.test(value)
      const hasLowerCase = /[a-z]/.test(value)
      const hasNumber = /[0-9]/.test(value)

      if (hasUpperCase && hasLowerCase && hasNumber) {
        callback()
      } else {
        callback(new Error(message))
      }
    },
    trigger
  }
}

/**
 * 异步唯一性验证生成器
 * @param {Function} checkFn - 异步检查函数，返回 Promise<boolean>
 * @param {string} message - 错误提示信息
 * @param {number} debounceTime - 防抖时间（毫秒），默认 500
 * @returns {object} Element Plus 验证规则对象
 */
export function asyncUnique(checkFn, message = '该值已存在', debounceTime = 500) {
  let debounceTimer = null

  return {
    validator: (rule, value, callback) => {
      if (!value) {
        callback()
        return
      }

      // 清除之前的定时器
      if (debounceTimer) {
        clearTimeout(debounceTimer)
      }

      // 设置新的定时器
      debounceTimer = setTimeout(async () => {
        try {
          const isUnique = await checkFn(value)
          if (isUnique) {
            callback()
          } else {
            callback(new Error(message))
          }
        } catch (error) {
          console.error('唯一性验证失败:', error)
          // 验证失败时不阻塞用户，只记录错误
          callback()
        }
      }, debounceTime)
    },
    trigger: 'blur'
  }
}

/**
 * 自定义验证规则
 * @param {Function} validator - 自定义验证函数 (rule, value, callback) => void
 * @param {string} trigger - 触发方式，默认 'blur'
 * @returns {object} Element Plus 验证规则对象
 */
export function custom(validator, trigger = 'blur') {
  return {
    validator,
    trigger
  }
}

/**
 * 组合多个验证规则
 * @param {...object} rules - 验证规则对象
 * @returns {Array} 验证规则数组
 */
export function combine(...rules) {
  return rules
}

/**
 * 常用验证规则预设
 */
export const presets = {
  // 用户名：4-50字符，字母数字下划线
  username: () => combine(
    required('请输入用户名'),
    lengthRange(4, 50),
    codeFormat()
  ),

  // 邮箱
  emailAddress: () => combine(
    required('请输入邮箱'),
    email()
  ),

  // 密码：8-50字符，包含大小写字母和数字
  password: () => combine(
    required('请输入密码'),
    lengthRange(8, 50),
    passwordStrength()
  ),

  // 手机号
  phoneNumber: () => combine(
    required('请输入手机号'),
    phone()
  ),

  // 通用名称：2-100字符
  name: () => combine(
    required('请输入名称'),
    lengthRange(2, 100)
  ),

  // 通用代码：4-50字符，字母数字下划线
  code: () => combine(
    required('请输入代码'),
    lengthRange(4, 50),
    codeFormat()
  ),

  // URL地址
  website: () => combine(
    required('请输入网址'),
    url()
  )
}

export default {
  required,
  email,
  phone,
  url,
  minLength,
  maxLength,
  lengthRange,
  range,
  pattern,
  codeFormat,
  dirNameFormat,
  confirm,
  passwordStrength,
  asyncUnique,
  custom,
  combine,
  presets
}
