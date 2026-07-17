<script setup>
import { computed } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  patient: {
    type: Object,
    default: () => ({})
  }
})

function joinList(list) {
  return Array.isArray(list) ? list.join(' / ') : ''
}

const display = computed(() => ({
  name: props.patient?.name || '',
  gender: props.patient?.gender || '',
  age: props.patient?.age != null && props.patient?.age !== '' ? String(props.patient.age) : '',
  allergies: joinList(props.patient?.basicInfo?.allergies),
  historySyndromes: joinList(props.patient?.basicInfo?.historySyndromes),
  historyPrescriptions: joinList(props.patient?.basicInfo?.historyPrescriptions)
}))
</script>

<template>
  <BaseCard title="患者基本信息">
    <div class="patient-info">
      <div class="patient-info__grid">
        <div class="patient-info__field">
          <span class="patient-info__label">姓名</span>
          <span class="patient-info__value">{{ display.name || '-' }}</span>
        </div>

        <div class="patient-info__field">
          <span class="patient-info__label">性别</span>
          <span class="patient-info__value">{{ display.gender || '-' }}</span>
        </div>

        <div class="patient-info__field">
          <span class="patient-info__label">年龄</span>
          <span class="patient-info__value">{{ display.age || '-' }}</span>
        </div>

        <div class="patient-info__field">
          <span class="patient-info__label">过敏史</span>
          <span class="patient-info__value">{{ display.allergies || '-' }}</span>
        </div>

        <div class="patient-info__field">
          <span class="patient-info__label">历史辨证</span>
          <span class="patient-info__value">{{ display.historySyndromes || '-' }}</span>
        </div>

        <div class="patient-info__field">
          <span class="patient-info__label">历史处方</span>
          <span class="patient-info__value">{{ display.historyPrescriptions || '-' }}</span>
        </div>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.patient-info {
  display: block;
}

.patient-info__grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.patient-info__field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.patient-info__label {
  color: var(--text-subtle);
  font-size: 12px;
}

.patient-info__value {
  color: var(--text-primary);
  font-size: 14px;
  min-height: 20px;
}

@media (max-width: 760px) {
  .patient-info__grid {
    grid-template-columns: 1fr;
  }
}
</style>
