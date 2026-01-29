# 表单验证系统使用指南

ContentHub 前端项目使用了一套完整的表单验证系统，基于 Element Plus 的验证机制，提供了可复用的验证规则和工具函数。

## 目录结构

```
src/frontend/src/
├── utils/
│   └── validate.js           # 通用验证函数模块
├── composables/
│   └── useFormValidation.js  # 表单验证 Hook 和预设规则
└── pages/
    ├── WritingStyleManage.vue    # 写作风格管理
    ├── ContentThemeManage.vue    # 内容主题管理
    ├── AccountManage.vue         # 账号管理
    ├── UserManage.vue            # 用户管理
    ├── CustomerManage.vue        # 客户管理
    └── PlatformManage.vue        # 平台管理
```

## 核心模块

### 1. validate.js - 通用验证函数

提供基础验证规则生成器，所有规则都与 Element Plus Form 组件兼容。

#### 基础验证函数

```javascript
import * as validators from '@/utils/validate'

// 必填验证
validators.required('请输入用户名')

// 邮箱验证
validators.email()

// 手机号验证（中国大陆）
validators.phone()

// URL 验证
validators.url()

// 长度验证
validators.minLength(2)
validators.maxLength(100)
validators.lengthRange(2, 100)

// 数值范围验证
validators.range(100, 10000)

// 正则表达式验证
validators.pattern(/^[a-zA-Z0-9_]+$/, '只能包含字母、数字和下划线')

// 代码格式验证（字母、数字、下划线）
validators.codeFormat()

// 目录名格式验证（字母、数字、下划线、中划线）
validators.dirNameFormat()

// 密码强度验证（必须包含大小写字母和数字）
validators.passwordStrength()

// 异步唯一性验证
validators.asyncUnique(async (value) => {
  const result = await checkUnique(value)
  return result.isUnique
}, '该用户名已存在')
```

#### 预设规则组合

```javascript
import { presets } from '@/utils/validate'

// 用户名：4-50字符，字母数字下划线
presets.username()

// 邮箱
presets.emailAddress()

// 密码：8-50字符，包含大小写字母和数字
presets.password()

// 手机号
presets.phoneNumber()

// 通用名称：2-100字符
presets.name()

// 通用代码：4-50字符，字母数字下划线
presets.code()

// URL地址
presets.website()
```

### 2. useFormValidation.js - 表单验证 Hook

提供表单验证的通用逻辑和业务预设规则。

#### 使用 Hook

```javascript
import { useFormValidation } from '@/composables/useFormValidation'

const formData = reactive({
  username: '',
  email: '',
  password: ''
})

const {
  formRef,              // 表单引用
  isValidating,         // 是否正在验证
  isValid,              // 验证是否通过
  validateForm,         // 验证整个表单
  validateField,        // 验证单个字段
  resetForm,            // 重置表单
  setFieldValue,        // 设置字段值
  clearFieldValidation  // 清除字段验证
} = useFormValidation(formData, validationRules)

// 验证表单
const handleSubmit = async () => {
  const valid = await validateForm()
  if (valid) {
    // 提交数据
  }
}
```

#### 业务预设规则

```javascript
import { commonRules } from '@/composables/useFormValidation'

// 写作风格相关
const rules = {
  name: commonRules.writingStyleName(),
  code: commonRules.writingStyleCode(),
  tone: commonRules.writingStyleTone(),
  min_words: commonRules.writingStyleWordRange().min_words,
  max_words: commonRules.writingStyleWordRange().max_words
}

// 内容主题相关
const rules = {
  name: commonRules.contentThemeName(),
  code: commonRules.contentThemeCode(),
  type: commonRules.contentThemeType()
}

// 账号相关
const rules = {
  name: commonRules.accountName(),
  platform_id: commonRules.accountPlatformId()
}

// 用户相关
const rules = {
  username: commonRules.username(),
  email: commonRules.userEmail(),
  password: commonRules.userPassword()
}

// 客户相关
const rules = {
  name: commonRules.customerName(),
  email: commonRules.customerEmail(),
  phone: commonRules.customerPhone()
}

// 平台相关
const rules = {
  name: commonRules.platformName(),
  code: commonRules.platformCode(),
  callback_url: commonRules.platformApiUrl()
}
```

## 页面实现示例

### 完整示例：WritingStyleManage.vue

```vue
<template>
  <el-dialog v-model="dialogVisible" title="写作风格" width="700px">
    <el-form ref="formRef" :model="formData" :rules="formRules" label-width="120px">
      <el-form-item label="风格名称" prop="name">
        <el-input v-model="formData.name" placeholder="请输入风格名称" />
      </el-form-item>

      <el-form-item label="风格代码" prop="code">
        <el-input v-model="formData.code" placeholder="请输入风格代码" />
      </el-form-item>

      <el-form-item label="最小字数" prop="min_words">
        <el-input-number v-model="formData.min_words" :min="100" :max="10000" />
      </el-form-item>

      <el-form-item label="最大字数" prop="max_words">
        <el-input-number v-model="formData.max_words" :min="100" :max="10000" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="submitLoading" @click="handleSubmit">
        确定
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { commonRules } from '@/composables/useFormValidation'

const formRef = ref(null)
const submitLoading = ref(false)

const formData = reactive({
  name: '',
  code: '',
  min_words: 800,
  max_words: 1500
})

const formRules = {
  name: commonRules.writingStyleName(),
  code: commonRules.writingStyleCode(),
  min_words: commonRules.writingStyleWordRange().min_words,
  max_words: commonRules.writingStyleWordRange().max_words
}

const handleSubmit = async () => {
  try {
    // 验证表单
    await formRef.value.validate()

    submitLoading.value = true

    // 提交数据
    await createWritingStyle(formData)

    ElMessage.success('创建成功')
    dialogVisible.value = false
  } catch (error) {
    if (error !== false) {
      console.error('提交失败:', error)
      ElMessage.error(error.response?.data?.detail || '提交失败')
    }
  } finally {
    submitLoading.value = false
  }
}
</script>
```

## 验证规则说明

### WritingStyleManage.vue

| 字段 | 规则 | 说明 |
|------|------|------|
| name | 必填，2-100 字符 | 风格名称 |
| code | 必填，4-50 字符，字母数字下划线 | 风格代码 |
| tone | 必填，不超过 50 字符 | 语气 |
| min_words | 必填，100-10000，不能大于 max_words | 最小字数 |
| max_words | 必填，100-10000，不能小于 min_words | 最大字数 |

### ContentThemeManage.vue

| 字段 | 规则 | 说明 |
|------|------|------|
| name | 必填，2-100 字符 | 主题名称 |
| code | 必填，4-50 字符，字母数字下划线 | 主题代码 |
| type | 必填 | 主题类型 |

### AccountManage.vue

| 字段 | 规则 | 说明 |
|------|------|------|
| name | 必填，2-100 字符 | 账号名称 |
| platform_id | 必填 | 所属平台 |
| account_id | 必填 | 账号ID |
| credentials | 必填 | 认证信息 |

### UserManage.vue

| 字段 | 规则 | 说明 |
|------|------|------|
| username | 必填，4-50 字符，字母数字下划线 | 用户名 |
| email | 必填，邮箱格式 | 邮箱 |
| password | 必填，8-50 字符，包含大小写字母和数字 | 密码（仅创建时） |

### CustomerManage.vue

| 字段 | 规则 | 说明 |
|------|------|------|
| name | 必填，2-100 字符 | 客户名称 |
| contact | 必填 | 联系人 |
| email | 邮箱格式（可选） | 邮箱 |
| phone | 手机号格式（可选） | 电话 |

### PlatformManage.vue

| 字段 | 规则 | 说明 |
|------|------|------|
| name | 必填，2-100 字符 | 平台名称 |
| platform_type | 必填 | 平台类型 |
| app_id | 必填 | App ID |
| app_secret | 必填 | App Secret |
| callback_url | URL 格式（可选） | 回调地址 |

## 自定义验证规则

### 1. 基础自定义验证

```javascript
const customRules = {
  field: [
    { required: true, message: '此项为必填项', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: '只能包含字母、数字和下划线',
      trigger: 'blur'
    }
  ]
}
```

### 2. 自定义验证器函数

```javascript
const customRules = {
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (!value) {
          callback()
          return
        }
        const hasUpperCase = /[A-Z]/.test(value)
        const hasLowerCase = /[a-z]/.test(value)
        const hasNumber = /[0-9]/.test(value)

        if (hasUpperCase && hasLowerCase && hasNumber) {
          callback()
        } else {
          callback(new Error('密码必须包含大小写字母和数字'))
        }
      },
      trigger: 'blur'
    }
  ]
}
```

### 3. 跨字段验证

```javascript
const customRules = {
  max_words: [
    { required: true, message: '请输入最大字数', trigger: 'blur' },
    {
      validator: (rule, value, callback, source) => {
        if (value && source.min_words && value < source.min_words) {
          callback(new Error('最大字数不能小于最小字数'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}
```

### 4. 异步唯一性验证

```javascript
const checkCodeUnique = async (code) => {
  try {
    const response = await api.checkCodeExists(code)
    return !response.exists
  } catch (error) {
    return true // 验证失败时不阻塞用户
  }
}

const customRules = {
  code: [
    { required: true, message: '请输入代码', trigger: 'blur' },
    validators.asyncUnique(checkCodeUnique, '该代码已存在')
  ]
}
```

## 最佳实践

### 1. 使用预设规则

优先使用 `commonRules` 中的预设规则，确保全项目验证规则一致。

```javascript
// 推荐
const rules = {
  name: commonRules.writingStyleName()
}

// 不推荐（除非有特殊需求）
const rules = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' },
    { min: 2, max: 100, message: '长度在 2 到 100 个字符', trigger: 'blur' }
  ]
}
```

### 2. 适当的验证时机

- **blur**: 适合大多数验证（失焦时验证）
- **change**: 适合下拉框等选择器
- 避免使用 `input` 触发（会频繁验证影响用户体验）

### 3. 友好的错误提示

```javascript
// 好的错误提示
{ message: '风格代码只能包含字母、数字和下划线' }

// 不好的错误提示
{ message: '格式错误' }
```

### 4. 必填项 vs 可选项

```javascript
// 必填项
{ required: true, message: '请输入邮箱', trigger: 'blur' }

// 可选项但需要格式验证
{ type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
```

### 5. 防御性验证

对于可选字段，只在有值时验证格式：

```javascript
email: [
  {
    validator: (rule, value, callback) => {
      if (!value) {
        callback() // 允许为空
        return
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
        callback(new Error('请输入正确的邮箱格式'))
      } else {
        callback()
      }
    },
    trigger: 'blur'
  }
]
```

## 扩展指南

### 添加新的预设规则

在 `composables/useFormValidation.js` 的 `commonRules` 对象中添加：

```javascript
export const commonRules = {
  // ... 现有规则

  // 新增规则
  myNewField: () => [
    validators.required('请输入字段'),
    validators.lengthRange(2, 50),
    validators.pattern(/^[a-z]+$/, '只能包含小写字母')
  ]
}
```

### 添加新的验证器函数

在 `utils/validate.js` 中添加新的验证器：

```javascript
/**
 * 自定义验证器
 */
export function myValidator(message = '验证失败', trigger = 'blur') {
  return {
    pattern: /my-regex/,
    message,
    trigger
  }
}
```

## 测试验证规则

### 手动测试

1. 打开表单页面
2. 尝试提交空表单（应显示必填错误）
3. 输入错误格式的数据（应显示格式错误）
4. 输入正确数据（错误提示应消失）
5. 提交表单（应成功）

### 自动化测试

```javascript
import { describe, it, expect } from 'vitest'
import { validators } from '@/utils/validate'

describe('Validation Rules', () => {
  it('should validate email format', () => {
    const rule = validators.email()
    expect(rule.type).toBe('email')
    expect(rule.message).toContain('邮箱')
  })

  it('should validate phone format', () => {
    const rule = validators.phone()
    expect(rule.pattern).toBe(/^1[3-9]\d{9}$/)
  })
})
```

## 故障排除

### 问题 1: 验证规则不生效

**解决方案:**
- 确保在 `el-form` 上添加了 `:rules="formRules"`
- 确保在 `el-form-item` 上添加了正确的 `prop` 属性
- 确保在提交时调用了 `formRef.value.validate()`

### 问题 2: 跨字段验证失败

**解决方案:**
- 使用 `validator` 函数而不是简单的 `pattern`
- 通过 `source` 参数访问其他字段的值

### 问题 3: 异步验证阻塞用户

**解决方案:**
- 在异步验证的 catch 块中调用 `callback()` 而不是 `callback(new Error())`
- 添加防抖逻辑（`asyncUnique` 已内置）

## 总结

ContentHub 的表单验证系统提供了：

1. **可复用的验证规则** - 避免重复代码
2. **统一的验证逻辑** - 确保全项目一致
3. **类型安全** - 基于 TypeScript 风格的注释
4. **灵活的扩展性** - 易于添加新规则
5. **良好的用户体验** - 清晰的错误提示

通过合理使用这个系统，可以快速构建功能完善、用户友好的表单页面。
