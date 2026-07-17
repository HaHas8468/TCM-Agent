<script setup>
import BaseCard from '../../../../components/ui/BaseCard.vue'
import StatusBadge from '../../../../components/ui/StatusBadge.vue'

defineProps({
  integrations: {
    type: Array,
    default: () => []
  },
  activity: {
    type: Array,
    default: () => []
  }
})
</script>

<template>
  <div class="integration-grid">
    <BaseCard title="系统集成状态" subtitle="展示医生端依赖的 Agent、知识图谱、消息网关与登录安全服务状态。">
      <div class="integration-table">
        <table class="data-table">
          <thead>
            <tr>
              <th>服务</th>
              <th>状态</th>
              <th>详情</th>
              <th>负责人</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in integrations" :key="item.name">
              <td>{{ item.name }}</td>
              <td><StatusBadge :value="item.status" /></td>
              <td>{{ item.detail }}</td>
              <td>{{ item.owner }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </BaseCard>

    <BaseCard title="最近设置操作" subtitle="记录最近的设置修改动作，便于后续接入审计日志。">
      <div class="activity-list">
        <article v-for="item in activity" :key="`${item.time}-${item.action}`" class="activity-list__item">
          <div class="activity-list__head">
            <strong>{{ item.action }}</strong>
            <span>{{ item.time }}</span>
          </div>
          <p>操作人：{{ item.operator }}</p>
        </article>
      </div>
    </BaseCard>
  </div>
</template>

<style scoped>
.integration-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(320px, 0.85fr);
  gap: 18px;
}

.integration-table {
  overflow-x: auto;
}

.activity-list {
  display: grid;
  gap: 12px;
}

.activity-list__item {
  padding: 16px;
  border-radius: 18px;
  background: #f7fafc;
}

.activity-list__head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.activity-list__head strong,
.activity-list__item p {
  margin: 0;
}

.activity-list__head span,
.activity-list__item p {
  color: #59738f;
  line-height: 1.7;
}

@media (max-width: 1280px) {
  .integration-grid {
    grid-template-columns: 1fr;
  }
}
</style>
