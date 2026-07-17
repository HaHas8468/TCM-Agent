<script setup>
import { computed } from 'vue'

const props = defineProps({
  value: {
    type: String,
    default: ''
  }
})

const toneClass = computed(() => {
  if (props.value === '待接诊' || props.value === '待审核') {
    return 'status-badge--warning'
  }

  if (props.value === '问诊中' || props.value === '进行中') {
    return 'status-badge--info'
  }

  if (props.value === '已结束' || props.value === '已启用' || props.value === '运行正常') {
    return 'status-badge--success'
  }

  if (props.value === '待处理' || props.value === '需关注') {
    return 'status-badge--warning'
  }

  return 'status-badge--default'
})
</script>

<template>
  <span class="status-badge" :class="toneClass">{{ value }}</span>
</template>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 76px;
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 12px;
  font-weight: 700;
}

.status-badge--warning {
  background: rgba(201, 138, 27, 0.14);
  color: #a66f10;
}

.status-badge--info {
  background: rgba(45, 106, 79, 0.12);
  color: #2d6a4f;
}

.status-badge--success {
  background: rgba(45, 143, 96, 0.12);
  color: #2d8f60;
}

.status-badge--default {
  background: rgba(103, 122, 113, 0.12);
  color: #677a71;
}
</style>
