/**
 * 表单验证组合式函数
 * 提供表单验证的通用逻辑和工具
 */
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import * as validators from '../utils/validate'

/**
 * 表单验证 Hook
 * @param {Object} formData - 表单数据对象
 * @param {Object} validationRules - 验证规则对象
 * @param {Object} options - 配置选项
 * @returns {Object} 验证相关的状态和方法
 */
export function useFormValidation(formData, validationRules = {}, options = {}) {
  const {
    // 是否在输入时实时验证（默认 false，只在失焦时验证）
    validateOnInput = false,
    // 防抖延迟时间（毫秒）
    debounceTime = 500,
    // 验证成功后是否显示提示（默认 false）
    showSuccessMessage = false
  } = options

  // 表单引用
  const formRef = ref(null)

  // 验证状态
  const isValidating = ref(false)
  const isValid = ref(false)

  // 字段验证状态映射
  const fieldValidationStatus = ref({})

  // 清除字段验证状态
  const clearFieldValidation = (field) => {
    if (fieldValidationStatus.value[field]) {
      delete fieldValidationStatus.value[field]
    }
    formRef.value?.clearValidate(field)
  }

  // 清除所有验证状态
  const clearAllValidation = () => {
    fieldValidationStatus.value = {}
    formRef.value?.clearValidate()
  }

  // 验证单个字段
  const validateField = async (field) => {
    if (!formRef.value) return false

    try {
      await formRef.value.validateField(field)
      clearFieldValidation(field)
      return true
    } catch (error) {
      fieldValidationStatus.value[field] = {
        valid: false,
        message: error.message || '验证失败'
      }
      return false
    }
  }

  // 验证整个表单
  const validateForm = async () => {
    if (!formRef.value) return false

    isValidating.value = true

    try {
      await formRef.value.validate()
      isValid.value = true
      clearAllValidation()

      if (showSuccessMessage) {
        ElMessage.success('验证通过')
      }

      return true
    } catch (error) {
      isValid.value = false
      console.error('表单验证失败:', error)
      return false
    } finally {
      isValidating.value = false
    }
  }

  // 重置表单
  const resetForm = () => {
    formRef.value?.resetFields()
    clearAllValidation()
    isValid.value = false
  }

  // 设置字段值
  const setFieldValue = (field, value) => {
    if (formData && typeof formData[field] !== 'undefined') {
      formData[field] = value
      // 清除该字段的验证状态
      clearFieldValidation(field)
    }
  }

  // 批量设置字段值
  const setFieldsValue = (values) => {
    if (formData && typeof values === 'object') {
      Object.keys(values).forEach(field => {
        setFieldValue(field, values[field])
      })
    }
  }

  // 监听表单数据变化（如果启用了实时验证）
  if (validateOnInput && formData) {
    let debounceTimer = null

    watch(
      formData,
      () => {
        if (debounceTimer) {
          clearTimeout(debounceTimer)
        }

        debounceTimer = setTimeout(() => {
          if (formRef.value) {
            formRef.value.validate((valid) => {
              isValid.value = valid
            })
          }
        }, debounceTime)
      },
      { deep: true }
    )
  }

  return {
    formRef,
    isValidating,
    isValid,
    fieldValidationStatus,
    validateField,
    validateForm,
    resetForm,
    setFieldValue,
    setFieldsValue,
    clearFieldValidation,
    clearAllValidation
  }
}

/**
 * 创建异步唯一性验证器
 * @param {Function} apiCall - API 调用函数
 * @param {string} errorMessage - 错误提示
 * @returns {Function} 验证函数
 */
export function createUniqueValidator(apiCall, errorMessage = '该值已存在') {
  return async (rule, value, callback) => {
    if (!value) {
      callback()
      return
    }

    try {
      const result = await apiCall(value)
      if (result && result.exists) {
        callback(new Error(errorMessage))
      } else {
        callback()
      }
    } catch (error) {
      console.error('唯一性验证失败:', error)
      // 验证失败时不阻塞用户，只记录错误
      callback()
    }
  }
}

/**
 * 创建确认匹配验证器
 * @param {string} targetField - 目标字段名
 * @param {string} errorMessage - 错误提示
 * @returns {Function} 验证函数
 */
export function createConfirmValidator(targetField, errorMessage = '两次输入不一致') {
  return (rule, value, callback) => {
    if (!value) {
      callback()
      return
    }

    const formData = rule.source || {}
    if (value !== formData[targetField]) {
      callback(new Error(errorMessage))
    } else {
      callback()
    }
  }
}

/**
 * 常用表单验证规则预设
 */
export const commonRules = {
  // 写作风格相关
  writingStyleName: () => [
    validators.required('请输入风格名称'),
    validators.minLength(2, '风格名称不能少于 2 个字符'),
    validators.maxLength(100, '风格名称不能超过 100 个字符')
  ],

  writingStyleCode: () => [
    validators.required('请输入风格代码'),
    validators.lengthRange(4, 50),
    validators.codeFormat()
  ],

  writingStyleTone: () => [
    validators.required('请选择语气'),
    validators.maxLength(50, '语气不能超过 50 个字符')
  ],

  writingStyleWordRange: (minField = 'min_words', maxField = 'max_words') => ({
    [minField]: [
      validators.required('请输入最小字数'),
      {
        validator: (rule, value, callback, source) => {
          if (value && source[maxField] && value > source[maxField]) {
            callback(new Error('最小字数不能大于最大字数'))
          } else if (value < 100) {
            callback(new Error('最小字数不能少于 100'))
          } else if (value > 10000) {
            callback(new Error('最小字数不能超过 10000'))
          } else {
            callback()
          }
        },
        trigger: 'blur'
      }
    ],
    [maxField]: [
      validators.required('请输入最大字数'),
      {
        validator: (rule, value, callback, source) => {
          if (value && source[minField] && value < source[minField]) {
            callback(new Error('最大字数不能小于最小字数'))
          } else if (value < 100) {
            callback(new Error('最大字数不能少于 100'))
          } else if (value > 10000) {
            callback(new Error('最大字数不能超过 10000'))
          } else {
            callback()
          }
        },
        trigger: 'blur'
      }
    ]
  }),

  // 内容主题相关
  contentThemeName: () => [
    validators.required('请输入主题名称'),
    validators.lengthRange(2, 100)
  ],

  contentThemeCode: () => [
    validators.required('请输入主题代码'),
    validators.lengthRange(4, 50),
    validators.codeFormat()
  ],

  contentThemeType: () => [
    validators.required('请选择主题类型')
  ],

  // 账号相关
  accountName: () => [
    validators.required('请输入账号名称'),
    validators.lengthRange(2, 100)
  ],

  accountPlatformId: () => [
    validators.required('请选择平台')
  ],

  accountDirName: () => [
    validators.required('请输入目录名'),
    validators.dirNameFormat()
  ],

  // 用户相关
  username: () => [
    validators.required('请输入用户名'),
    validators.lengthRange(4, 50),
    validators.codeFormat('用户名只能包含字母、数字和下划线')
  ],

  userEmail: () => [
    validators.required('请输入邮箱'),
    validators.email()
  ],

  userPassword: () => [
    validators.required('请输入密码'),
    validators.lengthRange(8, 50),
    validators.passwordStrength()
  ],

  userPasswordConfirm: (passwordField = 'password') => [
    validators.required('请确认密码'),
    {
      validator: (rule, value, callback, source) => {
        if (value !== source[passwordField]) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ],

  // 客户相关
  customerName: () => [
    validators.required('请输入客户名称'),
    validators.lengthRange(2, 100)
  ],

  customerEmail: () => [
    validators.email('请输入正确的邮箱格式')
  ],

  customerPhone: () => [
    validators.phone()
  ],

  // 平台相关
  platformName: () => [
    validators.required('请输入平台名称'),
    validators.lengthRange(2, 100)
  ],

  platformCode: () => [
    validators.required('请输入平台代码'),
    validators.lengthRange(4, 50),
    validators.codeFormat()
  ],

  platformApiUrl: () => [
    validators.url()
  ]
}

export default useFormValidation
