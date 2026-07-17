<script setup>
import BaseCard from '../../../components/ui/BaseCard.vue'
import StatusBadge from '../../../components/ui/StatusBadge.vue'
import queueNullImage from '../../../assets/empty-states/queueNull.png'

defineProps({
  summary: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  patients: {
    type: Array,
    default: () => []
  },
  filters: {
    type: Object,
    default: () => ({})
  },
  departmentOptions: {
    type: Array,
    default: () => []
  },
  periodOptions: {
    type: Array,
    default: () => []
  }
})

defineEmits(['update-filter', 'start-consultation'])
</script>

<template>
  <div class="page-stack">
    <section class="stat-strip">
      <article v-for="item in summary" :key="item.label" class="stat-card">
        <div class="stat-card__label">{{ item.label }}</div>
        <div class="stat-card__value">{{ item.value }}</div>
      </article>
    </section>

    <BaseCard title="今日接诊队列">
      <template #actions>
        <div class="queue__filters">
          <label class="queue__filter">
            <span>科室</span>
            <select
              class="select"
              :value="filters.department"
              :disabled="loading"
              @change="$emit('update-filter', 'department', $event.target.value)"
            >
              <option v-for="item in departmentOptions" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>

          <label class="queue__filter">
            <span>时段</span>
            <select
              class="select"
              :value="filters.period"
              :disabled="loading"
              @change="$emit('update-filter', 'period', $event.target.value)"
            >
              <option v-for="item in periodOptions" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>
        </div>
      </template>

      <div v-if="error" class="queue__notice queue__notice--error">{{ error }}</div>
      <div v-else-if="loading" class="queue__notice">接诊队列同步中...</div>

      <div v-if="patients.length" class="queue__table-wrap">
        <table class="data-table">
          <colgroup>
            <col class="queue__col queue__col--patient" />
            <col class="queue__col queue__col--department" />
            <col class="queue__col queue__col--time" />
            <col class="queue__col queue__col--status" />
            <col class="queue__col queue__col--actions" />
          </colgroup>
          <thead>
            <tr>
              <th>患者</th>
              <th>科室</th>
              <th>挂号时间</th>
              <th>状态</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="patient in patients" :key="patient.orderId || patient.id">
              <td>
                <div class="queue__name">{{ patient.name }}</div>
              </td>
              <td>{{ patient.department }}</td>
              <td>{{ patient.schedule }}</td>
              <td><StatusBadge :value="patient.status" /></td>
              <td>
                <div class="queue__actions">
                  <button
                    type="button"
                    class="primary-button"
                    :disabled="patient.status === '已结束' || patient.status === '已取消'"
                    @click="$emit('start-consultation', patient)"
                  >
                    {{ patient.status === '已结束' || patient.status === '已取消' ? '不可接诊' : '接诊' }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-else-if="loading" class="queue-empty empty-state">
        <img class="queue-empty__image" :src="queueNullImage" alt="接诊队列同步中" />
        <strong>正在同步接诊队列</strong>
        <span>已根据当前筛选条件拉取最新挂号数据</span>
      </div>

      <div v-else class="queue-empty empty-state">
        <img class="queue-empty__image" :src="queueNullImage" alt="暂无接诊队列" />
        <strong>当前筛选条件下暂无挂号患者</strong>
        <span>可调整科室或时段后再次查看</span>
      </div>
    </BaseCard>
  </div>
</template>

<style scoped>
.queue__filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.queue__filter {
  display: grid;
  gap: 5px;
}

.queue__filter span {
  color: var(--text-subtle);
  font-size: 12px;
  font-weight: 700;
}

.queue__filter :deep(.select) {
  width: 144px;
  min-height: 38px;
  border-radius: 12px;
  padding: 7px 34px 7px 12px;
  font-size: 15px;
}

.queue__table-wrap {
  overflow-x: auto;
}

.queue__notice {
  margin-bottom: 14px;
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(232, 245, 233, 0.78);
  color: var(--brand-deep);
  font-size: 13px;
  font-weight: 600;
}

.queue__notice--error {
  background: rgba(193, 87, 79, 0.12);
  color: #b14f47;
}

.queue__table-wrap :deep(.data-table) {
  table-layout: fixed;
  min-width: 760px;
}

.queue__table-wrap :deep(.data-table th),
.queue__table-wrap :deep(.data-table td) {
  padding-left: 8px;
  padding-right: 8px;
}

.queue__col--patient {
  width: 34%;
}

.queue__col--department {
  width: 20%;
}

.queue__col--time {
  width: 16%;
}

.queue__col--status {
  width: 18%;
}

.queue__col--actions {
  width: 12%;
}

.queue__name {
		font-weight: 700;
	}

.queue__actions {
  display: flex;
  gap: 10px;
  flex-wrap: nowrap;
}

.queue__actions :deep(.primary-button),
.queue__actions :deep(.ghost-button) {
  min-width: 86px;
  padding: 0 14px;
}

.queue-empty {
  display: grid;
  gap: 10px;
  place-items: center;
  padding: 42px 24px;
}

.queue-empty__image {
  width: min(300px, 72vw);
  height: auto;
}

.queue-empty strong {
  color: var(--text-main);
  font-size: 18px;
}

.queue-empty span {
  color: var(--text-subtle);
  font-size: 13px;
}

@media (max-width: 1280px) {
  .queue__actions {
    min-width: 86px;
  }
}
</style>
