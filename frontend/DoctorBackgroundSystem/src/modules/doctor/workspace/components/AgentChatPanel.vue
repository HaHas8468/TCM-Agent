<script setup>
import { ref } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

defineProps({
  messages: {
    type: Array,
    default: () => []
  },
  patient: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['send'])

const draft = ref('')

const quickPrompts = [
  '请总结当前补采缺口',
  '请给出辨证与治法建议',
  '请概括既往病历重点',
  '请核对当前方剂与用法'
]

function submit(message = draft.value) {
  if (!message || !message.trim()) {
    return
  }

  emit('send', message)
  draft.value = ''
}
</script>

<template>
  <BaseCard
    title="智能助手对话窗口"
    subtitle="医生可直接向智能助手追问补采重点、辨证思路、方剂建议和既往病历摘要。"
  >
    <div class="agent-chat">
      <div class="agent-chat__context">
        <span class="pill">当前患者：{{ patient.name }}</span>
        <span class="pill">当前证型：{{ patient.aiPlan.syndrome }}</span>
      </div>

      <div class="agent-chat__quick-prompts">
        <button
          v-for="item in quickPrompts"
          :key="item"
          type="button"
          class="ghost-button"
          @click="submit(item)"
        >
          {{ item }}
        </button>
      </div>

      <div class="agent-chat__messages">
        <article
          v-for="message in messages"
          :key="message.id"
          class="agent-chat__message"
          :class="`agent-chat__message--${message.sender}`"
        >
          <div class="agent-chat__meta">
            <strong>{{ message.roleLabel }}</strong>
            <span>{{ message.time }}</span>
          </div>
          <p>{{ message.text }}</p>
        </article>
      </div>

      <div class="agent-chat__composer">
        <textarea
          v-model="draft"
          class="textarea"
          placeholder="例如：请说明为什么判断为肝胃不和夹湿？"
        />
        <button type="button" class="primary-button" @click="submit()">发送给智能助手</button>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.agent-chat {
  display: grid;
  gap: 16px;
}

.agent-chat__context,
.agent-chat__quick-prompts {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.agent-chat__messages {
  display: grid;
  gap: 12px;
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.agent-chat__message {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  line-height: 1.8;
}

.agent-chat__message--agent {
  background: linear-gradient(180deg, rgba(232, 245, 233, 0.78), rgba(248, 251, 248, 0.95));
}

.agent-chat__message--doctor {
  background: var(--bg-soft);
}

.agent-chat__meta,
.agent-chat__composer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.agent-chat__meta span,
.agent-chat__message p {
  margin: 0;
  color: var(--text-subtle);
}

.agent-chat__composer {
  flex-direction: column;
}
</style>
