<script setup>
import { ref, watch } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  queries: {
    type: Array,
    default: () => []
  },
  startExpanded: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['search'])

const draft = ref('')
const expanded = ref(props.startExpanded)

watch(
  () => props.startExpanded,
  (value) => {
    expanded.value = value
  }
)

function submit() {
  if (!draft.value.trim()) {
    return
  }

  emit('search', draft.value)
  draft.value = ''
}
</script>

<template>
  <BaseCard title="辅助检索" subtitle="需要时再展开，避免打断主接诊流程。">
    <div class="knowledge">
      <div class="knowledge__header">
        <span class="pill">{{ expanded ? '已展开' : '已折叠' }}</span>
        <button type="button" class="ghost-button" @click="expanded = !expanded">
          {{ expanded ? '收起检索区' : '展开检索区' }}
        </button>
      </div>

      <div v-if="expanded" class="knowledge__form">
        <textarea
          v-model="draft"
          class="textarea"
          placeholder="例如：麻黄的功效、配伍禁忌、相似药材"
        />
        <button type="button" class="secondary-button" @click="submit">独立检索 Neo4j</button>
      </div>

      <div v-if="expanded" class="knowledge__history">
        <article v-for="item in queries" :key="item.id" class="knowledge__entry">
          <strong>{{ item.query }}</strong>
          <p>{{ item.answer }}</p>
        </article>

        <div v-if="!queries.length" class="empty-state">当前还没有手动知识检索记录。</div>
      </div>

      <div v-else class="knowledge__collapsed-note">
        当前按个人偏好默认折叠，展开后可继续发起知识图谱检索。
      </div>
    </div>
  </BaseCard>
</template>

<style scoped>
.knowledge,
.knowledge__form,
.knowledge__history {
  display: grid;
  gap: 14px;
}

.knowledge__header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.knowledge__entry {
  padding: 16px;
  border-radius: 18px;
  background: var(--bg-soft);
}

.knowledge__entry strong,
.knowledge__entry p {
  margin: 0;
  line-height: 1.8;
}

.knowledge__entry p {
  margin-top: 8px;
  color: var(--text-subtle);
}

.knowledge__collapsed-note {
  padding: 16px;
  border-radius: 18px;
  background: var(--bg-soft);
  color: var(--text-subtle);
  line-height: 1.8;
}
</style>
