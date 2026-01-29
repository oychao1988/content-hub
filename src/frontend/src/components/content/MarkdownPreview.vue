<template>
  <div class="markdown-preview">
    <div
      v-if="htmlContent"
      class="markdown-content"
      v-html="htmlContent"
      @click="handleImageClick"
    ></div>
    <div v-else class="empty-state">
      <el-empty description="暂无内容" />
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'
import 'highlight.js/styles/github.css'

const props = defineProps({
  content: {
    type: String,
    default: ''
  },
  highlight: {
    type: Boolean,
    default: true
  },
  linkify: {
    type: Boolean,
    default: true
  }
})

// 初始化 MarkdownIt
const md = new MarkdownIt({
  html: true,
  breaks: true,
  linkify: props.linkify,
  highlight: props.highlight ? (str, lang) => {
    if (lang && hljs.getLanguage(lang)) {
      try {
        return `<pre class="hljs"><code>${hljs.highlight(str, { language: lang, ignoreIllegals: true }).value}</code></pre>`
      } catch (__) {}
    }
    return `<pre class="hljs"><code>${md.utils.escapeHtml(str)}</code></pre>`
  }
})

// 渲染 HTML 内容
const htmlContent = computed(() => {
  if (!props.content) return ''
  return md.render(props.content)
})

// 处理图片点击事件
const emit = defineEmits(['image-click'])
const handleImageClick = (event) => {
  if (event.target.tagName === 'IMG') {
    emit('image-click', event.target.src)
  }
}
</script>

<style scoped>
.markdown-preview {
  min-height: 100px;
  padding: 16px;
  background-color: #fff;
  border-radius: 4px;
  overflow: hidden;
}

.markdown-content {
  line-height: 1.6;
  color: #303133;
}

.markdown-content >>> h1,
.markdown-content >>> h2,
.markdown-content >>> h3,
.markdown-content >>> h4,
.markdown-content >>> h5,
.markdown-content >>> h6 {
  margin: 16px 0 12px 0;
  font-weight: 600;
  color: #303133;
}

.markdown-content >>> h1 {
  font-size: 28px;
  border-bottom: 2px solid #ebeef5;
  padding-bottom: 8px;
}

.markdown-content >>> h2 {
  font-size: 24px;
}

.markdown-content >>> h3 {
  font-size: 20px;
}

.markdown-content >>> p {
  margin: 12px 0;
}

.markdown-content >>> ul,
.markdown-content >>> ol {
  margin: 12px 0;
  padding-left: 28px;
}

.markdown-content >>> li {
  margin: 4px 0;
}

.markdown-content >>> blockquote {
  margin: 16px 0;
  padding: 8px 16px;
  border-left: 4px solid #409eff;
  background-color: #f5f7fa;
  color: #606266;
}

.markdown-content >>> code {
  background-color: #f4f4f4;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 14px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.markdown-content >>> pre {
  margin: 16px 0;
  padding: 12px;
  background-color: #f4f4f4;
  border-radius: 4px;
  overflow-x: auto;
}

.markdown-content >>> pre code {
  padding: 0;
  background-color: transparent;
}

.markdown-content >>> img {
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  cursor: pointer;
  transition: transform 0.2s ease;
}

.markdown-content >>> img:hover {
  transform: scale(1.02);
}

.markdown-content >>> a {
  color: #409eff;
  text-decoration: none;
}

.markdown-content >>> a:hover {
  text-decoration: underline;
}

.markdown-content >>> table {
  width: 100%;
  margin: 16px 0;
  border-collapse: collapse;
  border-spacing: 0;
}

.markdown-content >>> th,
.markdown-content >>> td {
  padding: 8px 12px;
  border: 1px solid #ebeef5;
  text-align: left;
}

.markdown-content >>> th {
  background-color: #f5f7fa;
  font-weight: 600;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style>
