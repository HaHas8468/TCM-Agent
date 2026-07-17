<script setup>
import { reactive, watch } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  settings: {
    type: Object,
    default: () => ({})
  },
  moduleOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['save'])

const form = reactive({
  defaultLandingModule: 'queue',
  queueAutoRefresh: false,
  autoRefreshSeconds: 45,
  showAiEvidence: true,
  compactSidebar: false,
  openKnowledgeDrawer: true,
  autoArchiveFinished: false
})

function syncForm() {
  Object.assign(form, props.settings || {})
}

watch(
  () => props.settings,
  () => {
    syncForm()
  },
  { immediate: true, deep: true }
)

function submit() {
  emit('save', {
    ...form,
    autoRefreshSeconds: Number(form.autoRefreshSeconds)
  })
}
</script>

<template>
  <BaseCard title="工作台偏好" subtitle="设置默认进入模块、刷新节奏和医生端工作台的信息呈现方式。">
    <div class="workspace-card">
      <label class="workspace-card__field">
        <span>默认进入模块</span>
        <select v-model="form.defaultLandingModule" class="select">
          <option v-for="item in moduleOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
        </select>
      </label>

      <label class="workspace-card__field">
        <span>队列自动刷新间隔（秒）</span>
        <input v-model="form.autoRefreshSeconds" class="field" type="number" min="15" step="15" />
      </label>

      <div class="workspace-card__toggle-list">
        <label class="workspace-card__toggle">
          <input v-model="form.queueAutoRefresh" type="checkbox" />
          <span>启用接诊队列自动刷新</span>
        </label>
        <label class="workspace-card__toggle">
          <input v-model="form.showAiEvidence" type="checkbox" />
          <span>在工作台显示 AI 图谱依据</span>
        </label>
        <label class="workspace-card__toggle">
          <input v-model="form.compactSidebar" type="checkbox" />
          <span>使用紧凑侧边栏布局</span>
        </label>
        <label class="workspace-card__toggle">
          <input v-model="form.openKnowledgeDrawer" type="checkbox" />
          <span>默认展开手动知识检索区</span>
        </label>
        <label class="workspace-card__toggle">
          <input v-model="form.autoArchiveFinished" type="checkbox" />
          <span>问诊结束后自动归档</span>
        </label>
      </div>

      <button type="button" class="primary-button" @click="submit">保存工作台偏好</button>
    </div>
  </BaseCard>
</template>

<style scoped>
.workspace-card {
  display: grid;
  gap: 14px;
}

.workspace-card__field {
  display: grid;
  gap: 8px;
}

.workspace-card__field span {
  color: #59738f;
  font-size: 13px;
}

.workspace-card__toggle-list {
  display: grid;
  gap: 10px;
}

.workspace-card__toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #f7fafc;
  color: #16324f;
}
</style>
