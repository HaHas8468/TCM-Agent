<script setup>
import BaseCard from '../../../../components/ui/BaseCard.vue'

defineProps({
  patient: {
    type: Object,
    default: () => ({})
  }
})
</script>

<template>
  <BaseCard title="病历侧边栏" subtitle="固定展示基础信息、过敏史、历史辨证和历史处方。">
    <div class="sidebar-panel">
      <div class="sidebar-panel__block">
        <strong>基础信息</strong>
        <p>姓名：{{ patient.name }} / {{ patient.gender }} / {{ patient.age }} 岁</p>
        <p>电话：{{ patient.basicInfo.phone }}</p>
        <p>血压：{{ patient.basicInfo.bloodPressure }}</p>
      </div>

      <div class="sidebar-panel__block">
        <strong>过敏史</strong>
        <div class="sidebar-panel__pills">
          <span v-for="item in patient.basicInfo.allergies" :key="item" class="pill">{{ item }}</span>
        </div>
      </div>

      <div class="sidebar-panel__block">
        <strong>历史辨证</strong>
        <div class="sidebar-panel__pills">
          <span v-for="item in patient.basicInfo.historySyndromes" :key="item" class="pill">{{ item }}</span>
        </div>
      </div>

      <div class="sidebar-panel__block">
        <strong>历史处方</strong>
        <ul class="sidebar-panel__list">
          <li v-for="item in patient.basicInfo.historyPrescriptions" :key="item">{{ item }}</li>
        </ul>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.sidebar-panel {
  display: grid;
  gap: 16px;
}

.sidebar-panel__block {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: var(--bg-soft);
}

.sidebar-panel__block p,
.sidebar-panel__block strong,
.sidebar-panel__list {
  margin: 0;
  line-height: 1.8;
}

.sidebar-panel__pills {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.sidebar-panel__list {
  padding-left: 18px;
  color: var(--text-subtle);
}
</style>
