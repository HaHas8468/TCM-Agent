<script setup>
import { onBeforeUnmount, reactive, watch } from 'vue'
import BaseCard from '../../../components/ui/BaseCard.vue'

const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  detailLoading: {
    type: Boolean,
    default: false
  },
  records: {
    type: Array,
    default: () => []
  },
  selectedRecord: {
    type: Object,
    default: () => null
  }
})

const emit = defineEmits(['search-records', 'select-record'])

const filters = reactive({
  patientName: '',
  patientId: '',
  syndrome: '',
  date: ''
})

let searchTimer = null

function triggerSearch() {
  emit('search-records', { ...filters })
}

watch(
  filters,
  () => {
    if (searchTimer) {
      clearTimeout(searchTimer)
    }

    searchTimer = setTimeout(() => {
      triggerSearch()
    }, 260)
  },
  {
    deep: true,
    immediate: true
  }
)

onBeforeUnmount(() => {
  if (searchTimer) {
    clearTimeout(searchTimer)
  }
})
</script>

<template>
  <div class="records page-stack">
    <BaseCard
      title="病历检索管理"
      subtitle="支持按姓名、患者ID、证型和就诊时间多条件检索，查看单次门诊完整病历。"
    >
      <div class="records__filters">
        <input v-model="filters.patientName" class="field" type="text" placeholder="姓名" />
        <input v-model="filters.patientId" class="field" type="text" placeholder="患者ID" />
        <input v-model="filters.syndrome" class="field" type="text" placeholder="证型" />
        <input v-model="filters.date" class="field" type="text" placeholder="就诊时间（如 2026-07-17）" />
      </div>
    </BaseCard>

    <div class="records__layout">
      <BaseCard title="病历列表" subtitle="点击行可在右侧查看完整病历摘要。">
        <div v-if="error" class="records__notice records__notice--error">{{ error }}</div>
        <div v-else-if="loading" class="records__notice">病历列表同步中...</div>

        <div v-if="records.length" class="records__table-wrap">
          <table class="data-table">
            <thead>
              <tr>
                <th>患者</th>
                <th>证型</th>
                <th>方剂</th>
                <th>时间</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="record in records"
                :key="record.recordId"
                class="records__row"
                :class="{ 'records__row--active': selectedRecord && selectedRecord.recordId === record.recordId }"
                @click="emit('select-record', record.recordId)"
              >
                <td>
                  <div class="records__name">{{ record.patientName }}</div>
                  <div class="records__sub">{{ record.patientId }}</div>
                </td>
                <td>{{ record.syndrome }}</td>
                <td>{{ record.formula }}</td>
                <td>{{ record.visitTime }}</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-else-if="loading" class="empty-state">正在同步病历列表...</div>
        <div v-else class="empty-state">没有检索到匹配病历。</div>
      </BaseCard>

      <BaseCard
        v-if="selectedRecord"
        title="单次门诊病历"
        :subtitle="`${selectedRecord.patientName} · ${selectedRecord.visitTime}`"
      >
        <div class="records__detail">
          <div v-if="detailLoading" class="records__notice">病历详情同步中...</div>

          <div class="records__detail-block">
            <strong>诊断信息</strong>
            <p>主诉：{{ selectedRecord.fourDiagnosis?.chiefComplaint || '暂无' }}</p>
            <p>现病史：{{ selectedRecord.fourDiagnosis?.presentIllness || '暂无' }}</p>
          </div>

          <div class="records__detail-block">
            <strong>辨证与治疗</strong>
            <p>辨证：{{ selectedRecord.syndrome || '暂无' }}</p>
            <p>疗法：{{ selectedRecord.therapy || '暂无' }}</p>
            <p>方剂：{{ selectedRecord.formula || '暂无' }}</p>
            <p>药材：{{ selectedRecord.ingredients?.length ? selectedRecord.ingredients.join('、') : '暂无' }}</p>
          </div>

          <div class="records__detail-block">
            <strong>门诊补充信息</strong>
            <p>就诊医生：{{ selectedRecord.doctorName || '暂无' }}</p>
            <p>医嘱：{{ selectedRecord.advice || '暂无' }}</p>
            <p>注意事项：{{ selectedRecord.precautions || '暂无' }}</p>
          </div>
        </div>
      </BaseCard>
    </div>
  </div>
</template>

<style scoped>
.records__filters {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.records__layout {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(360px, 0.9fr);
  gap: 18px;
}

.records__table-wrap {
  overflow-x: auto;
}

.records__notice {
  margin-bottom: 14px;
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(232, 245, 233, 0.78);
  color: var(--brand-deep);
  font-size: 13px;
  font-weight: 600;
}

.records__notice--error {
  background: rgba(193, 87, 79, 0.12);
  color: #b14f47;
}

.records__row {
  cursor: pointer;
}

.records__row--active {
  background: rgba(225, 239, 247, 0.5);
}

.records__name {
  font-weight: 700;
}

.records__sub {
  margin-top: 4px;
  color: #8095aa;
  font-size: 12px;
}

.records__detail {
  display: grid;
  gap: 18px;
}

.records__detail-block {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  background: #f7fafc;
}

.records__detail-block p,
.records__detail-block strong {
  margin: 0;
  line-height: 1.8;
}

@media (max-width: 1280px) {
  .records__filters,
  .records__layout {
    grid-template-columns: 1fr;
  }
}
</style>
