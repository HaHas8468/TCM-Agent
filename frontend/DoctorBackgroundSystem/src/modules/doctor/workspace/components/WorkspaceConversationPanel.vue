<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  patient: {
    type: Object,
    default: () => ({})
  },
  sending: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: ''
  },
  agentMessages: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['send-agent-message'])
const draft = ref('')
const messagesRef = ref(null)
const showThinking = computed(() => {
  return props.sending && !props.patient?.agentLastResponse
})

function escapeHtml(value = '') {
  return String(value || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function renderInlineMarkdown(value = '') {
  return escapeHtml(value)
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer">$1</a>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/__([^_]+)__/g, '<strong>$1</strong>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*([^*\n]+)\*/g, '<em>$1</em>')
    .replace(/_([^_\n]+)_/g, '<em>$1</em>')
    .replace(/\n/g, '<br />')
}

function normalizeMarkdownSource(value = '') {
  return String(value || '')
    .replace(/\r\n/g, '\n')
    .replace(/\r/g, '\n')
    .replace(/\\n/g, '\n')
}

function renderMarkdown(value = '') {
  const source = normalizeMarkdownSource(value)
  const codeBlocks = []
  const placeholderPrefix = '@@CODE_BLOCK_'
  const withPlaceholders = source.replace(/```([\w-]+)?\n([\s\S]*?)```/g, (_, language = '', code = '') => {
    const index = codeBlocks.length
    const normalizedLanguage = String(language || '').trim()
    const normalizedCode = escapeHtml(String(code || '').replace(/\n$/, ''))

    codeBlocks.push(
      `<pre><code${normalizedLanguage ? ` class="language-${escapeHtml(normalizedLanguage)}"` : ''}>${normalizedCode}</code></pre>`
    )

    return `${placeholderPrefix}${index}@@`
  })

  const lines = withPlaceholders.split('\n')
  const blocks = []
  let paragraphLines = []
  let listType = ''
  let listItems = []
  let blockquoteLines = []

  function flushParagraph() {
    if (!paragraphLines.length) {
      return
    }

    const paragraph = paragraphLines
      .map((line) => {
        if (line.startsWith(placeholderPrefix) && line.endsWith('@@')) {
          const match = line.match(/@@CODE_BLOCK_(\d+)@@/)
          return match ? codeBlocks[Number(match[1])] || '' : line
        }

        return renderInlineMarkdown(line)
      })
      .filter(Boolean)
      .join('<br />')

    if (paragraph) {
      blocks.push(`<p>${paragraph}</p>`)
    }

    paragraphLines = []
  }

  function flushList() {
    if (!listItems.length || !listType) {
      listItems = []
      listType = ''
      return
    }

    const items = listItems.map((item) => `<li>${renderInlineMarkdown(item)}</li>`).join('')
    blocks.push(`<${listType}>${items}</${listType}>`)
    listItems = []
    listType = ''
  }

  function flushBlockquote() {
    if (!blockquoteLines.length) {
      return
    }

    const quoteContent = blockquoteLines.map((line) => renderInlineMarkdown(line)).join('<br />')
    if (quoteContent) {
      blocks.push(`<blockquote><p>${quoteContent}</p></blockquote>`)
    }

    blockquoteLines = []
  }

  function flushAll() {
    flushParagraph()
    flushList()
    flushBlockquote()
  }

  lines.forEach((rawLine) => {
    const line = rawLine.trimEnd()
    const trimmedLine = line.trim()
    const normalizedHeadingLine = trimmedLine.replace(/^(#{1,6})([^#\s].*)$/, '$1 $2')

    if (!trimmedLine) {
      flushAll()
      return
    }

    const headingMatch = normalizedHeadingLine.match(/^(#{1,6})\s+(.*)$/)
    if (headingMatch) {
      flushAll()
      const level = headingMatch[1].length
      blocks.push(`<h${level}>${renderInlineMarkdown(headingMatch[2])}</h${level}>`)
      return
    }

    const unorderedListMatch = trimmedLine.match(/^[-*+]\s+(.*)$/)
    if (unorderedListMatch) {
      flushParagraph()
      flushBlockquote()
      if (listType && listType !== 'ul') {
        flushList()
      }
      listType = 'ul'
      listItems.push(unorderedListMatch[1])
      return
    }

    const orderedListMatch = trimmedLine.match(/^\d+\.\s+(.*)$/)
    if (orderedListMatch) {
      flushParagraph()
      flushBlockquote()
      if (listType && listType !== 'ol') {
        flushList()
      }
      listType = 'ol'
      listItems.push(orderedListMatch[1])
      return
    }

    const quoteMatch = trimmedLine.match(/^>\s?(.*)$/)
    if (quoteMatch) {
      flushParagraph()
      flushList()
      blockquoteLines.push(quoteMatch[1])
      return
    }

    if (trimmedLine.startsWith(placeholderPrefix) && trimmedLine.endsWith('@@')) {
      flushAll()
      const match = trimmedLine.match(/@@CODE_BLOCK_(\d+)@@/)
      if (match) {
        blocks.push(codeBlocks[Number(match[1])] || '')
      }
      return
    }

    if (blockquoteLines.length) {
      flushBlockquote()
    }

    paragraphLines.push(trimmedLine)
  })

  flushAll()

  return blocks
    .join('')
    .replace(new RegExp(`${placeholderPrefix}(\\d+)@@`, 'g'), (_, index) => codeBlocks[Number(index)] || '')
}

function submit() {
  if (!draft.value || !draft.value.trim()) {
    return
  }

  emit('send-agent-message', draft.value.trim())
  draft.value = ''
}

function scrollToBottom() {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

watch(
  () => [props.agentMessages.length, props.patient?.agentLastResponse, props.sending, showThinking.value],
  () => {
    scrollToBottom()
  }
)
</script>

<template>
  <BaseCard title="智能助手对话">
    <div class="conversation">
      <div class="conversation__head">
        <div class="conversation__patient">
          <strong>{{ patient.name }}</strong>
          <span>{{ patient.department }} · {{ patient.schedule }}</span>
        </div>

        <div class="pill">{{ patient.status }}</div>
      </div>

      <div v-if="patient.agentConversationStatus === 'asking'" class="conversation__notice">
        智能助手正在第 {{ patient.agentAskRound || 1 }} 轮追问，请继续补充问诊信息。
      </div>
      <div v-else-if="patient.agentConversationStatus === 'diagnosed'" class="conversation__notice">
        智能助手已生成诊断建议，可在系统分析和医生最终确认中继续复核。
      </div>

      <div ref="messagesRef" class="conversation__messages">
        <article
          v-for="message in agentMessages"
          :key="message.id"
          class="conversation__message"
          :class="`conversation__message--${message.sender}`"
        >
          <div class="conversation__meta">
            <strong>{{ message.sender === 'agent' ? '智能助手' : message.roleLabel }}</strong>
            <span>{{ message.time }}</span>
          </div>
          <div
      v-if="message.sender === 'agent'"
      class="conversation__content conversation__content--markdown"
      v-html="renderMarkdown(message.text)"
    />
          <p v-else class="conversation__plain" v-html="renderMarkdown(message.text)" />
        </article>

        <article v-if="showThinking" class="conversation__message conversation__message--thinking">
          <div class="conversation__meta">
            <strong>智能助手</strong>
            <span>思考中</span>
          </div>
          <div class="conversation__thinking">
            <span>thinking</span>
            <span class="conversation__dots">
              <i />
              <i />
              <i />
            </span>
          </div>
        </article>
      </div>

      <div class="conversation__composer">
        <div v-if="error" class="conversation__notice conversation__notice--error">{{ error }}</div>

        <textarea
          v-model="draft"
          class="textarea"
          placeholder="向智能助手输入问题或补充信息"
          :disabled="sending"
        />
        <button type="button" class="primary-button" :disabled="sending" @click="submit">
          {{ sending ? '发送中...' : '发送给智能助手' }}
        </button>
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.conversation {
  display: grid;
  gap: 12px;
  min-height: calc(100vh - 136px);
}

.conversation__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.conversation__patient {
  display: grid;
  gap: 4px;
}

.conversation__patient strong {
  font-size: 18px;
}

.conversation__patient span {
  color: var(--text-subtle);
  font-size: 13px;
}

.conversation__messages {
  display: grid;
  gap: 10px;
  align-content: start;
  min-height: 480px;
  max-height: calc(100vh - 260px);
  overflow-y: auto;
  padding-right: 4px;
}

.conversation__message {
  display: grid;
  gap: 8px;
  padding: 14px;
  border-radius: 12px;
  line-height: 1.7;
}

.conversation__message--doctor {
  background: var(--bg-soft);
}

.conversation__message--agent {
  background: rgba(232, 245, 233, 0.78);
}

.conversation__message--thinking {
  background: rgba(232, 245, 233, 0.78);
}

.conversation__meta {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.conversation__meta span {
  margin: 0;
  color: var(--text-subtle);
}

.conversation__plain,
.conversation__content {
  margin: 0;
  color: var(--text-subtle);
  white-space: pre-wrap;
  word-break: break-word;
}

.conversation__content {
  display: grid;
  gap: 10px;
  white-space: normal;
}

.conversation__content :deep(*) {
  margin: 0;
}

.conversation__content :deep(p),
.conversation__content :deep(li),
.conversation__content :deep(blockquote) {
  color: var(--text-subtle);
  line-height: 1.8;
}

.conversation__content :deep(h1),
.conversation__content :deep(h2),
.conversation__content :deep(h3),
.conversation__content :deep(h4),
.conversation__content :deep(h5),
.conversation__content :deep(h6) {
  color: var(--text-main);
  font-size: 15px;
  font-weight: 700;
}

.conversation__content :deep(ul),
.conversation__content :deep(ol) {
  padding-left: 20px;
}

.conversation__content :deep(blockquote) {
  border-left: 3px solid rgba(45, 106, 79, 0.22);
  padding-left: 12px;
}

.conversation__content :deep(code) {
  border-radius: 6px;
  background: rgba(27, 67, 50, 0.08);
  padding: 2px 6px;
  color: var(--brand-deep);
  font-family: Consolas, "Courier New", monospace;
  font-size: 13px;
}

.conversation__content :deep(pre) {
  overflow-x: auto;
  border-radius: 10px;
  background: rgba(27, 67, 50, 0.08);
  padding: 12px;
}

.conversation__content :deep(pre code) {
  display: block;
  padding: 0;
  background: transparent;
  color: var(--text-main);
}

.conversation__content :deep(a) {
  color: var(--brand);
  text-decoration: none;
}

.conversation__content :deep(a:hover) {
  text-decoration: underline;
}

.conversation__composer {
  display: grid;
  gap: 10px;
}

.conversation__thinking {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  color: var(--text-subtle);
  font-size: 15px;
  font-weight: 600;
}

.conversation__dots {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.conversation__dots i {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(45, 106, 79, 0.48);
  animation: thinking-bounce 1.2s ease-in-out infinite;
}

.conversation__dots i:nth-child(2) {
  animation-delay: 0.16s;
}

.conversation__dots i:nth-child(3) {
  animation-delay: 0.32s;
}

.conversation__notice {
  border-radius: 12px;
  padding: 12px 14px;
  background: rgba(232, 245, 233, 0.78);
  color: var(--brand-deep);
  font-size: 13px;
  font-weight: 600;
}

.conversation__notice--error {
  background: rgba(193, 87, 79, 0.12);
  color: #b14f47;
}

.conversation__composer :deep(.textarea) {
  min-height: 84px;
}

@keyframes thinking-bounce {
  0%,
  80%,
  100% {
    opacity: 0.32;
    transform: translateY(0);
  }

  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}
</style>
