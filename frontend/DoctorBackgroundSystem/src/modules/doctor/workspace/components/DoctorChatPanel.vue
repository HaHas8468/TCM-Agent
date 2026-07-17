<script setup>
import { ref } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

defineProps({
  messages: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['send'])

const draft = ref('')

function submit() {
  if (!draft.value.trim()) {
    return
  }

  emit('send', draft.value)
  draft.value = ''
}
</script>

<template>
  <BaseCard title="医患图文聊天框" subtitle="右下区域保留医生输入框与患者消息展示区。">
    <div class="chat-panel">
      <div class="chat-panel__messages">
        <article
          v-for="message in messages"
          :key="message.id"
          class="chat-panel__message"
          :class="`chat-panel__message--${message.sender}`"
        >
          <div class="chat-panel__meta">
            <strong>{{ message.roleLabel }}</strong>
            <span>{{ message.time }}</span>
          </div>
          <p>{{ message.text }}</p>
        </article>
      </div>

      <div class="chat-panel__composer">
        <textarea
          v-model="draft"
          class="textarea"
          placeholder="输入医生回复内容，原型会追加到当前聊天记录。"
        />
        <button type="button" class="primary-button" @click="submit">发送并归档</button>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.chat-panel {
  display: grid;
  gap: 16px;
}

.chat-panel__messages {
  display: grid;
  gap: 12px;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 4px;
}

.chat-panel__message {
  display: grid;
  gap: 8px;
  padding: 16px;
  border-radius: 18px;
  line-height: 1.8;
}

.chat-panel__message--patient {
  background: var(--bg-soft);
}

.chat-panel__message--doctor {
  background: rgba(232, 245, 233, 0.7);
}

.chat-panel__meta,
.chat-panel__composer {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.chat-panel__meta span,
.chat-panel__message p {
  margin: 0;
  color: var(--text-subtle);
}

.chat-panel__composer {
  flex-direction: column;
}
</style>
