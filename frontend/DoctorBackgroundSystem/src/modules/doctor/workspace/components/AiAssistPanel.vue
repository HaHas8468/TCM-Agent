<script setup>
import BaseCard from '../../../../components/ui/BaseCard.vue'

defineProps({
  plan: {
    type: Object,
    default: () => ({})
  },
  showEvidence: {
    type: Boolean,
    default: true
  }
})

defineEmits(['open-recommendation'])
</script>

<template>
  <BaseCard title="返回建议" subtitle="集中查看智能助手返回的补采建议、辨证结果和推荐项。">
    <div class="ai-panel">
      <div class="ai-panel__section">
        <strong>分步补采建议</strong>
        <ul v-if="plan.gaps && plan.gaps.length" class="ai-panel__list">
          <li v-for="item in plan.gaps" :key="item">{{ item }}</li>
        </ul>
        <p v-else class="ai-panel__empty">当前信息已较完整，可直接确认方案。</p>
      </div>

      <div class="ai-panel__summary">
        <article class="ai-panel__summary-card">
          <span>辨证结论</span>
          <strong>{{ plan.syndrome }}</strong>
        </article>
        <article class="ai-panel__summary-card">
          <span>治法</span>
          <strong>{{ plan.therapy }}</strong>
        </article>
        <article class="ai-panel__summary-card">
          <span>推荐方剂</span>
          <strong>{{ plan.formula }}</strong>
        </article>
      </div>

      <div v-if="showEvidence" class="ai-panel__section">
        <strong>图谱依据</strong>
        <ul class="ai-panel__list">
          <li v-for="item in plan.evidence" :key="item">{{ item }}</li>
        </ul>
      </div>

      <div class="ai-panel__recommendations">
        <div class="ai-panel__recommend-block">
          <strong>相似药材推荐</strong>
          <div v-if="plan.recommendations && plan.recommendations.herbs.length" class="ai-panel__cards">
            <button
              v-for="item in plan.recommendations.herbs"
              :key="item.name"
              type="button"
              class="ai-panel__recommend-card"
              @click="$emit('open-recommendation', '药材', item)"
            >
              <span>{{ item.name }}</span>
              <small>{{ item.summary }}</small>
            </button>
          </div>
          <p v-else class="ai-panel__empty">暂无药材推荐。</p>
        </div>

        <div class="ai-panel__recommend-block">
          <strong>经典医案推荐</strong>
          <div v-if="plan.recommendations && plan.recommendations.cases.length" class="ai-panel__cards">
            <button
              v-for="item in plan.recommendations.cases"
              :key="item.name"
              type="button"
              class="ai-panel__recommend-card ai-panel__recommend-card--case"
              @click="$emit('open-recommendation', '医案', item)"
            >
              <span>{{ item.name }}</span>
              <small>{{ item.summary }}</small>
            </button>
          </div>
          <p v-else class="ai-panel__empty">暂无经典医案推荐。</p>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.ai-panel {
  display: grid;
  gap: 18px;
}

.ai-panel__section {
  display: grid;
  gap: 10px;
}

.ai-panel__list {
  margin: 0;
  padding-left: 18px;
  color: var(--text-subtle);
  line-height: 1.9;
}

.ai-panel__summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.ai-panel__summary-card {
  display: grid;
  gap: 10px;
  padding: 18px;
  border-radius: 18px;
  background: linear-gradient(180deg, rgba(232, 245, 233, 0.78), rgba(255, 255, 255, 0.95));
}

.ai-panel__summary-card span,
.ai-panel__recommend-card small,
.ai-panel__empty {
  color: var(--text-subtle);
}

.ai-panel__recommendations {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.ai-panel__recommend-block {
  display: grid;
  gap: 12px;
}

.ai-panel__cards {
  display: grid;
  gap: 10px;
}

.ai-panel__recommend-card {
  display: grid;
  gap: 6px;
  padding: 16px;
  border-radius: 18px;
  border: 1px solid var(--border-soft);
  background: rgba(255, 255, 255, 0.78);
  text-align: left;
}

.ai-panel__recommend-card--case {
  background: rgba(252, 246, 232, 0.7);
}

@media (max-width: 1280px) {
  .ai-panel__summary,
  .ai-panel__recommendations {
    grid-template-columns: 1fr;
  }
}
</style>
