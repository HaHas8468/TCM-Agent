<script setup>
import { computed } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  patient: {
    type: Object,
    default: () => ({})
  },
  plan: {
    type: Object,
    default: () => ({})
  }
})

const EMPTY_TEXT = '待生成'
const NONE_TEXT = '无'

function normalizeList(value) {
  if (!value) {
    return []
  }

  if (Array.isArray(value)) {
    return value.filter(Boolean)
  }

  return [value].filter(Boolean)
}

const analysis = computed(() => {
  const diagnosisResult = props.patient?.agentResult?.diagnosisResult || {}
  const doctorConfirmation = props.patient?.doctorConfirmation || {}
  const treatmentPlan = props.patient?.treatmentPlan || {}
  const plan = props.plan || {}
  const allergies = normalizeList(props.patient?.basicInfo?.allergies).filter((item) => item !== NONE_TEXT)
  const herbs = normalizeList(diagnosisResult.herbs).length
    ? normalizeList(diagnosisResult.herbs)
    : normalizeList(plan.recommendations?.herbs?.map((item) => item.name))
  const allergyWarnings = normalizeList(diagnosisResult.allergyWarnings)
  const precautions = String(
    doctorConfirmation.precautions || treatmentPlan.precautions || diagnosisResult.precautions || ''
  ).trim()

  return {
    syndromeName: diagnosisResult.syndrome || plan.syndrome || EMPTY_TEXT,
    syndromeDescription:
      diagnosisResult.syndromeDescription || diagnosisResult.description || normalizeList(plan.evidence).join('；') || EMPTY_TEXT,
    therapy: diagnosisResult.therapy || diagnosisResult.treatment || doctorConfirmation.treatment || plan.therapy || EMPTY_TEXT,
    formula: diagnosisResult.formula || doctorConfirmation.prescription || plan.formula || treatmentPlan.formula || EMPTY_TEXT,
    herbs: herbs.length ? herbs.join('、') : NONE_TEXT,
    attention: precautions
      ? precautions
      : allergyWarnings.length
        ? allergyWarnings.join('、')
        : allergies.length
          ? `患者过敏：${allergies.join('、')}，开方需复核。`
          : NONE_TEXT
  }
})
</script>

<template>
  <BaseCard title="系统分析">
    <div class="analysis-panel">
      <div class="analysis-panel__syndrome">
        <span>证型</span>
        <strong>{{ analysis.syndromeName }}</strong>
        <p>{{ analysis.syndromeDescription }}</p>
      </div>

      <div class="analysis-panel__grid">
        <div class="analysis-panel__item">
          <span>疗法</span>
          <strong>{{ analysis.therapy }}</strong>
        </div>

        <div class="analysis-panel__item">
          <span>方剂</span>
          <strong>{{ analysis.formula }}</strong>
        </div>

        <div class="analysis-panel__item">
          <span>药材</span>
          <strong>{{ analysis.herbs }}</strong>
        </div>

        <div class="analysis-panel__item">
          <span>注意事项</span>
          <strong>{{ analysis.attention }}</strong>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.analysis-panel {
  display: grid;
  gap: 10px;
}

.analysis-panel__syndrome,
.analysis-panel__item {
  padding: 10px 12px;
  border: 1px solid var(--border-soft);
  border-radius: 12px;
  background: var(--bg-soft);
}

.analysis-panel__syndrome {
  display: grid;
  gap: 5px;
}

.analysis-panel__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.analysis-panel__item {
  display: grid;
  gap: 6px;
}

.analysis-panel span {
  color: var(--text-subtle);
  font-size: 12px;
}

.analysis-panel strong {
  color: var(--text-main);
  font-size: 14px;
  line-height: 1.5;
}

.analysis-panel p {
  margin: 0;
  color: var(--text-subtle);
  font-size: 13px;
  line-height: 1.6;
}

@media (max-width: 760px) {
  .analysis-panel__grid {
    grid-template-columns: 1fr;
  }
}
</style>
