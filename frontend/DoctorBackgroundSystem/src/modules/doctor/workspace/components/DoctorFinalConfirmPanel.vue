<script setup>
import { computed, reactive, watch } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  patient: {
    type: Object,
    default: () => ({})
  },
  plan: {
    type: Object,
    default: () => ({})
  },
  submitting: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['save', 'finish'])

const NONE_TEXT = '无'

const form = reactive({
  syndrome: NONE_TEXT,
  therapy: NONE_TEXT,
  formula: NONE_TEXT,
  herbsText: NONE_TEXT,
  advice: NONE_TEXT,
  precautions: NONE_TEXT
})

function normalizeList(value) {
  if (!value) {
    return []
  }

  if (Array.isArray(value)) {
    return value.filter(Boolean)
  }

  return [value].filter(Boolean)
}

function splitTextList(text) {
  return text
    .split(/[、，,\n]/)
    .map((item) => item.trim())
    .filter((item) => item && item !== NONE_TEXT)
}

function cleanField(value) {
  const text = String(value || '').trim()
  return text === NONE_TEXT ? '' : text
}

function extractSyndromeName(value) {
  const text = String(value || '').trim()
  return text.split(/[，、；;\n]/)[0]?.trim() || ''
}

const systemDefaults = computed(() => {
  const diagnosisResult = props.patient?.agentResult?.diagnosisResult || {}
  const confirmation = props.patient?.doctorConfirmation || {}
  const plan = props.plan || {}
  const treatmentPlan = props.patient?.treatmentPlan || {}
  const herbs = normalizeList(diagnosisResult.herbs).length
    ? normalizeList(diagnosisResult.herbs)
    : normalizeList(plan.recommendations?.herbs?.map((item) => item.name))

  return {
    syndrome: confirmation.syndrome || extractSyndromeName(diagnosisResult.syndrome || plan.syndrome) || NONE_TEXT,
    therapy: confirmation.treatment || diagnosisResult.therapy || diagnosisResult.treatment || plan.therapy || NONE_TEXT,
    formula: confirmation.prescription || diagnosisResult.formula || plan.formula || treatmentPlan.formula || NONE_TEXT,
    herbsText: Array.isArray(confirmation.herbs)
      ? confirmation.herbs.join('、') || NONE_TEXT
      : herbs.length
        ? herbs.join('、')
        : NONE_TEXT,
    advice: confirmation.advice || treatmentPlan.followUp || NONE_TEXT,
    precautions: confirmation.precautions || treatmentPlan.precautions || NONE_TEXT
  }
})

function syncForm() {
  form.syndrome = systemDefaults.value.syndrome
  form.therapy = systemDefaults.value.therapy
  form.formula = systemDefaults.value.formula
  form.herbsText = systemDefaults.value.herbsText
  form.advice = systemDefaults.value.advice
  form.precautions = systemDefaults.value.precautions
}

watch(
  systemDefaults,
  () => {
    syncForm()
  },
  { immediate: true }
)

function buildPayload(completeVisit) {
  const formula = cleanField(form.formula)
  const advice = cleanField(form.advice)
  const precautions = cleanField(form.precautions)

  return {
    treatmentPlan: {
      formula,
      followUp: advice,
      precautions
    },
    aiAdjustment: cleanField(form.syndrome),
    therapy: cleanField(form.therapy),
    doctorConfirmation: {
      syndrome: cleanField(form.syndrome),
      treatment: cleanField(form.therapy),
      prescription: formula,
      herbs: splitTextList(form.herbsText),
      advice,
      precautions
    },
    completeVisit
  }
}
</script>

<template>
  <BaseCard title="医生最终确认">
    <div class="final-confirm">
      <div class="final-confirm__grid">
        <label class="final-confirm__field">
          <span>证型</span>
          <input v-model="form.syndrome" class="field" type="text" :disabled="submitting" />
        </label>

        <label class="final-confirm__field final-confirm__field--wide">
          <span>疗法</span>
          <textarea v-model="form.therapy" class="textarea" :disabled="submitting" />
        </label>

        <label class="final-confirm__field">
          <span>方剂</span>
          <input v-model="form.formula" class="field" type="text" :disabled="submitting" />
        </label>

        <label class="final-confirm__field">
          <span>药材</span>
          <input v-model="form.herbsText" class="field" type="text" :disabled="submitting" />
        </label>

        <label class="final-confirm__field final-confirm__field--wide">
          <span>医嘱</span>
          <textarea v-model="form.advice" class="textarea" :disabled="submitting" />
        </label>

        <label class="final-confirm__field final-confirm__field--wide">
          <span>注意事项</span>
          <textarea v-model="form.precautions" class="textarea" :disabled="submitting" />
        </label>
      </div>

      <div class="final-confirm__actions">
        <button type="button" class="secondary-button" :disabled="submitting" @click="emit('save', buildPayload(false))">
          {{ submitting ? '提交中...' : '暂存' }}
        </button>
        <button type="button" class="primary-button" :disabled="submitting" @click="emit('finish', buildPayload(true))">
          {{ submitting ? '提交中...' : '完成接诊' }}
        </button>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.final-confirm {
  display: grid;
  gap: 10px;
}

.final-confirm__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.final-confirm__field {
  display: grid;
  gap: 4px;
}

.final-confirm__field--wide {
  grid-column: 1 / -1;
}

.final-confirm__field span {
  color: var(--text-subtle);
  font-size: 12px;
}

.final-confirm :deep(.field) {
  min-height: 34px;
  border-radius: 10px;
  padding: 7px 10px;
  font-size: 14px;
}

.final-confirm :deep(.textarea) {
  min-height: 50px;
  border-radius: 10px;
  padding: 7px 10px;
  font-size: 14px;
}

.final-confirm__actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  flex-wrap: wrap;
}

@media (max-width: 760px) {
  .final-confirm__grid {
    grid-template-columns: 1fr;
  }
}
</style>
