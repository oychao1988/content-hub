<template>
  <div class="data-table">
    <el-table
      v-loading="loading"
      :data="data"
      :stripe="stripe"
      :border="border"
      :height="height"
      :max-height="maxHeight"
      @selection-change="handleSelectionChange"
      @sort-change="handleSortChange"
    >
      <el-table-column v-if="selectable" type="selection" width="55" />
      <el-table-column v-if="showIndex" type="index" label="序号" width="60" />
      <slot></slot>
      <template #empty>
        <el-empty description="暂无数据" />
      </template>
    </el-table>

    <div v-if="showPagination" class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="pageSizes"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  data: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  total: {
    type: Number,
    default: 0
  },
  stripe: {
    type: Boolean,
    default: true
  },
  border: {
    type: Boolean,
    default: false
  },
  selectable: {
    type: Boolean,
    default: false
  },
  showIndex: {
    type: Boolean,
    default: false
  },
  showPagination: {
    type: Boolean,
    default: true
  },
  height: {
    type: [String, Number],
    default: null
  },
  maxHeight: {
    type: [String, Number],
    default: null
  },
  pageSizes: {
    type: Array,
    default: () => [10, 20, 50, 100]
  }
})

const emit = defineEmits(['selection-change', 'sort-change', 'page-change', 'size-change'])

const currentPage = ref(1)
const pageSize = ref(20)

const handleSelectionChange = (selection) => {
  emit('selection-change', selection)
}

const handleSortChange = (sort) => {
  emit('sort-change', sort)
}

const handleSizeChange = (size) => {
  pageSize.value = size
  emit('size-change', size)
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  emit('page-change', page)
}

// 重置页码
const resetPage = () => {
  currentPage.value = 1
}

defineExpose({
  resetPage
})
</script>

<style scoped>
.data-table {
  background: #fff;
  border-radius: 4px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 16px;
  border-top: 1px solid #ebeef5;
}
</style>
