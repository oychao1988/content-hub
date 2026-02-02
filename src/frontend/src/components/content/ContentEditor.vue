<template>
  <div class="content-editor">
    <!-- 工具栏 -->
    <div class="editor-toolbar">
      <el-button-group>
        <el-button size="small" @click="insertText('**', '**')" title="加粗">
          <el-icon><EditPen /></el-icon>
        </el-button>
        <el-button size="small" @click="insertText('*', '*')" title="斜体">
          <el-icon><CopyDocument /></el-icon>
        </el-button>
        <el-button size="small" @click="insertText('`', '`')" title="代码">
          <el-icon><Document /></el-icon>
        </el-button>
      </el-button-group>

      <el-button-group>
        <el-button size="small" @click="insertText('- ', '')" title="无序列表">
          <el-icon><List /></el-icon>
        </el-button>
        <el-button size="small" @click="insertText('1. ', '')" title="有序列表">
          <el-icon><Reading /></el-icon>
        </el-button>
      </el-button-group>

      <el-button-group>
        <el-button size="small" @click="insertText('![图片描述](', ')')" title="插入图片">
          <el-icon><Picture /></el-icon>
        </el-button>
        <el-button size="small" @click="insertText('[链接文本](', ')')" title="插入链接">
          <el-icon><Link /></el-icon>
        </el-button>
      </el-button-group>

      <el-button-group>
        <el-button size="small" @click="insertText('```', '```')" title="代码块">
          <el-icon><MessageBox /></el-icon>
        </el-button>
        <el-button size="small" @click="insertText('> ', '')" title="引用">
          <el-icon><Message /></el-icon>
        </el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button-group>
        <el-button
          size="small"
          :type="previewMode === 'edit' ? 'primary' : ''"
          @click="previewMode = 'edit'"
          title="编辑模式"
        >
          <el-icon><Edit /></el-icon>
          编辑
        </el-button>
        <el-button
          size="small"
          :type="previewMode === 'preview' ? 'primary' : ''"
          @click="previewMode = 'preview'"
          title="预览模式"
        >
          <el-icon><View /></el-icon>
          预览
        </el-button>
        <el-button
          size="small"
          :type="previewMode === 'split' ? 'primary' : ''"
          @click="previewMode = 'split'"
          title="分屏模式"
        >
          <el-icon><Monitor /></el-icon>
          分屏
        </el-button>
      </el-button-group>

      <div class="toolbar-divider"></div>

      <el-button size="small" @click="toggleFullScreen" title="全屏编辑">
        <el-icon><FullScreen /></el-icon>
      </el-button>
    </div>

    <!-- 编辑区域 -->
    <div class="editor-content">
      <!-- 编辑模式 -->
      <div v-if="previewMode === 'edit' || previewMode === 'split'" class="editor-panel">
        <textarea
          ref="editorRef"
          v-model="localContent"
          class="editor-textarea"
          :placeholder="placeholder"
          @input="handleInput"
          @keydown.ctrl.enter="handleCtrlEnter"
        ></textarea>
      </div>

      <!-- 预览模式 -->
      <div v-if="previewMode === 'preview' || previewMode === 'split'" class="preview-panel">
        <MarkdownPreview
          :content="localContent"
          @image-click="handleImageClick"
        />
      </div>
    </div>

    <!-- 图片预览 -->
    <ImagePreview
      v-if="showImagePreview"
      :image-src="previewImageSrc"
      @close="showImagePreview = false"
    />
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import MarkdownPreview from './MarkdownPreview.vue'
import ImagePreview from './ImagePreview.vue'
import {
  EditPen,
  CopyDocument,
  Document,
  List,
  Reading,
  Picture,
  Link,
  MessageBox,
  Message,
  Edit,
  View,
  Monitor,
  FullScreen
} from '@element-plus/icons-vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  placeholder: {
    type: String,
    default: '请输入内容...'
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

// 本地内容
const localContent = ref(props.modelValue)

// 编辑器引用
const editorRef = ref(null)

// 预览模式：edit, preview, split
const previewMode = ref('edit')

// 图片预览
const showImagePreview = ref(false)
const previewImageSrc = ref('')

// 全屏模式
const isFullScreen = ref(false)

// 监听属性变化
watch(() => props.modelValue, (newValue) => {
  localContent.value = newValue
})

// 监听本地内容变化
watch(localContent, (newValue) => {
  emit('update:modelValue', newValue)
})

// 插入文本
const insertText = (prefix, suffix) => {
  const textarea = editorRef.value
  if (!textarea) return

  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = localContent.value.substring(start, end)
  const beforeText = localContent.value.substring(0, start)
  const afterText = localContent.value.substring(end)

  localContent.value = beforeText + prefix + selectedText + suffix + afterText
  textarea.focus()
  textarea.setSelectionRange(
    start + prefix.length,
    end + prefix.length
  )
}

// 处理输入
const handleInput = () => {
  emit('update:modelValue', localContent.value)
}

// 处理 Ctrl+Enter 提交
const handleCtrlEnter = () => {
  emit('submit', localContent.value)
}

// 处理图片点击
const handleImageClick = (src) => {
  previewImageSrc.value = src
  showImagePreview.value = true
}

// 切换全屏
const toggleFullScreen = () => {
  isFullScreen.value = !isFullScreen.value

  if (isFullScreen.value) {
    document.documentElement.requestFullscreen()
  } else {
    document.exitFullscreen()
  }
}

// 监听全屏变化
document.addEventListener('fullscreenchange', () => {
  isFullScreen.value = !!document.fullscreenElement
})
</script>

<style scoped>
.content-editor {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  overflow: hidden;
  background-color: #fff;
}

.editor-toolbar {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #dcdfe6;
  flex-wrap: wrap;
  gap: 4px;
}

.toolbar-divider {
  width: 1px;
  height: 24px;
  background-color: #dcdfe6;
  margin: 0 8px;
}

.editor-content {
  display: flex;
  min-height: 400px;
}

.editor-panel,
.preview-panel {
  flex: 1;
  min-height: 400px;
  overflow: hidden;
}

.editor-panel {
  border-right: 1px solid #dcdfe6;
}

.editor-textarea {
  width: 100%;
  height: 100%;
  min-height: 400px;
  padding: 16px;
  border: none;
  outline: none;
  resize: none;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #303133;
}

.editor-textarea::placeholder {
  color: #c0c4cc;
}

.preview-panel {
  padding: 16px;
  overflow-y: auto;
}

/* 分屏模式 */
.editor-content:has(.editor-panel:only-child),
.editor-content:has(.preview-panel:only-child) {
  display: block;
}

.editor-content:has(.editor-panel:only-child) .editor-panel,
.editor-content:has(.preview-panel:only-child) .preview-panel {
  min-height: 500px;
}
</style>
