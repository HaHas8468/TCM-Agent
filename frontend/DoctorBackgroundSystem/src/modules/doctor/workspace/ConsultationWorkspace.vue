<script setup>
import { ref } from 'vue'
import WorkspacePatientInfoCard from './components/WorkspacePatientInfoCard.vue'
import SystemAnalysisPanel from './components/SystemAnalysisPanel.vue'
import DoctorFinalConfirmPanel from './components/DoctorFinalConfirmPanel.vue'
import WorkspaceConversationPanel from './components/WorkspaceConversationPanel.vue'
import RecommendationDialog from './components/RecommendationDialog.vue'
import workplaceNullImage from '../../../assets/empty-states/workplaceNull.png'

defineProps({
  patient: {
    type: Object,
    default: () => null
  },
  agentSending: {
    type: Boolean,
    default: false
  },
  agentError: {
    type: String,
    default: ''
  },
  workspaceLoading: {
    type: Boolean,
    default: false
  },
  workspaceError: {
    type: String,
    default: ''
  },
  workspaceActionPending: {
    type: Boolean,
    default: false
  },
  workspaceActionError: {
    type: String,
    default: ''
  },
  workspaceActionSuccess: {
    type: String,
    default: ''
  },
  workspaceSettings: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits([
  'send-agent-message',
  'save-diagnosis-and-back',
  'finish-consultation',
  'open-record',
  'back-to-queue'
])

const activeRecommendation = ref(null)

function openRecommendation(type, item) {
  activeRecommendation.value = {
    type,
    item
  }
}

function closeRecommendation() {
  activeRecommendation.value = null
}
</script>

<template>
  <div class="workspace-page">
    <header class="workspace-page__toolbar">
      <button type="button" class="workspace-page__back" aria-label="返回队列" @click="emit('back-to-queue')">&lt;</button>
      <h1 class="workspace-page__title">中医药智能诊疗工作台</h1>
    </header>

    <div v-if="patient" class="workspace">
      <div v-if="workspaceError" class="workspace-page__notice workspace-page__notice--error">{{ workspaceError }}</div>
      <div v-else-if="workspaceLoading" class="workspace-page__notice">工作台病历同步中...</div>

      <div v-if="workspaceActionError" class="workspace-page__notice workspace-page__notice--error">
        {{ workspaceActionError }}
      </div>
      <div v-else-if="workspaceActionPending" class="workspace-page__notice">工作台操作提交中...</div>
      <div v-else-if="workspaceActionSuccess" class="workspace-page__notice">
        {{ workspaceActionSuccess }}
      </div>

      <div class="workspace__chat">
        <WorkspaceConversationPanel
          :patient="patient"
          :sending="agentSending"
          :error="agentError"
          :agent-messages="patient.agentMessages"
          @send-agent-message="emit('send-agent-message', $event)"
        />
      </div>

      <div class="workspace__patient">
        <WorkspacePatientInfoCard :patient="patient" />
        <SystemAnalysisPanel
          :patient="patient"
          :plan="patient.aiPlan"
        />
        <DoctorFinalConfirmPanel
          :patient="patient"
          :plan="patient.aiPlan"
          :submitting="workspaceActionPending"
          @save="emit('save-diagnosis-and-back', $event)"
          @finish="emit('finish-consultation', $event)"
        />
      </div>
    </div>

    <div v-else class="workspace-empty">
      <img class="workspace-empty__image" :src="workplaceNullImage" alt="暂无工作台内容" />
      <strong>当前暂无问诊患者</strong>
      <span>请先从接诊队列选择患者进入工作台</span>
    </div>

    <RecommendationDialog
      v-if="patient && activeRecommendation"
      :type="activeRecommendation.type"
      :item="activeRecommendation.item"
      @close="closeRecommendation"
    />
  </div>
</template>

<style scoped>
.workspace-page {
  min-height: 100vh;
  padding: 12px;
}

.workspace-page__toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 12px;
}

.workspace-page__back {
  width: 44px;
  height: 44px;
  padding: 0;
  border: 1px solid rgba(45, 106, 79, 0.18);
  border-radius: 12px;
  background: linear-gradient(135deg, var(--brand), var(--brand-deep));
  color: #fff;
  font-size: 25px;
  font-weight: 700;
  line-height: 1;
  box-shadow: 0 10px 22px rgba(27, 67, 50, 0.16);
}

.workspace-page__title {
  margin: 0;
  color: var(--brand-deep);
  font-size: 26px;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-align: right;
}

.workspace {
  display: grid;
  grid-template-columns: clamp(340px, 28vw, 420px) minmax(0, 1fr);
  gap: 12px;
  align-items: start;
  min-height: calc(100vh - 94px);
}

.workspace-page__notice {
  grid-column: 1 / -1;
  border-radius: 14px;
  padding: 12px 14px;
  background: rgba(232, 245, 233, 0.78);
  color: var(--brand-deep);
  font-size: 13px;
  font-weight: 600;
}

.workspace-page__notice--error {
  background: rgba(193, 87, 79, 0.12);
  color: #b14f47;
}

.workspace__chat {
  grid-column: 1;
  position: sticky;
  top: 12px;
}

.workspace__patient {
  grid-column: 2;
  display: grid;
  gap: 12px;
}

.workspace-empty {
  display: grid;
  gap: 12px;
  place-items: center;
  align-content: center;
  min-height: calc(100vh - 94px);
  color: var(--text-subtle);
  text-align: center;
}

.workspace-empty__image {
  width: min(320px, 72vw);
  height: auto;
}

.workspace-empty strong {
  color: var(--text-main);
  font-size: 24px;
  font-weight: 700;
}

.workspace-empty span {
  color: var(--text-subtle);
  font-size: 14px;
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }

  .workspace__chat,
  .workspace__patient {
    grid-column: auto;
  }

  .workspace__chat {
    position: static;
  }
}

@media (max-width: 960px) {
  .workspace-page {
    padding: 10px;
  }

  .workspace-page__toolbar {
    align-items: center;
    gap: 8px;
  }

  .workspace-page__back {
    width: 42px;
    height: 42px;
  }

  .workspace-page__title {
    font-size: 20px;
  }
}
</style>
