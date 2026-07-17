<script setup>
import { reactive, watch } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  settings: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['save'])

const form = reactive({
  queueReminder: false,
  followUpReminder: false,
  urgentAlert: false,
  aiCompletionNotice: false,
  emailDigest: false,
  smsFallback: false,
  digestTime: '18:00'
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
  emit('save', { ...form })
}
</script>

<template>
  <BaseCard title="消息提醒" subtitle="为挂号队列、复诊提醒、AI 输出和日报消息设置独立开关。">
    <div class="notify-card">
      <label class="notify-card__toggle">
        <input v-model="form.queueReminder" type="checkbox" />
        <div>
          <strong>接诊队列提醒</strong>
          <p>有新挂号患者进入队列时即时提醒。</p>
        </div>
      </label>

      <label class="notify-card__toggle">
        <input v-model="form.followUpReminder" type="checkbox" />
        <div>
          <strong>复诊提醒</strong>
          <p>在患者达到复诊节点时提醒医生跟进。</p>
        </div>
      </label>

      <label class="notify-card__toggle">
        <input v-model="form.urgentAlert" type="checkbox" />
        <div>
          <strong>高优先级预警</strong>
          <p>症状异常、风险字段缺失或紧急挂号时优先提醒。</p>
        </div>
      </label>

      <label class="notify-card__toggle">
        <input v-model="form.aiCompletionNotice" type="checkbox" />
        <div>
          <strong>AI 输出完成提醒</strong>
          <p>Agent 完成辨证与推荐后给出工作台提示。</p>
        </div>
      </label>

      <label class="notify-card__toggle">
        <input v-model="form.emailDigest" type="checkbox" />
        <div>
          <strong>邮箱日报</strong>
          <p>每天固定时间推送问诊量、证型和方剂摘要。</p>
        </div>
      </label>

      <label class="notify-card__toggle">
        <input v-model="form.smsFallback" type="checkbox" />
        <div>
          <strong>短信兜底</strong>
          <p>站内通知失败时自动走短信兜底。</p>
        </div>
      </label>

      <label class="notify-card__field">
        <span>日报推送时间</span>
        <input v-model="form.digestTime" class="field" type="time" />
      </label>

      <button type="button" class="primary-button" @click="submit">保存提醒策略</button>
    </div>
  </BaseCard>
</template>

<style scoped>
.notify-card {
  display: grid;
  gap: 14px;
}

.notify-card__toggle {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  padding: 16px;
  border-radius: 18px;
  background: #f7fafc;
}

.notify-card__toggle strong,
.notify-card__toggle p {
  margin: 0;
}

.notify-card__toggle p {
  margin-top: 6px;
  color: #59738f;
  line-height: 1.7;
}

.notify-card__field {
  display: grid;
  gap: 8px;
}

.notify-card__field span {
  color: #59738f;
  font-size: 13px;
}
</style>
