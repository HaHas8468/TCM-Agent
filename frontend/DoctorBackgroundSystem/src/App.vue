<script setup>
import AppShell from './components/layout/AppShell.vue'
import LoginView from './modules/doctor/auth/LoginView.vue'
import QueueOverview from './modules/doctor/queue/QueueOverview.vue'
import ConsultationWorkspace from './modules/doctor/workspace/ConsultationWorkspace.vue'
import RecordsManager from './modules/doctor/records/RecordsManager.vue'
import CaseLibrary from './modules/doctor/cases/CaseLibrary.vue'
import SettingsCenter from './modules/doctor/settings/SettingsCenter.vue'
import { useDoctorPrototype } from './composables/useDoctorPrototype'

const {
  state,
  activeNavigation,
  filteredPatients,
  activePatient,
  activeRecord,
  queueStats,
  queueDepartments,
  queuePeriods,
  login,
  logout,
  setActiveModule,
  returnToQueue,
  updateQueueFilter,
  updateDutyStatus,
  searchRecords,
  openConsultation,
  openRecord,
  sendAgentMessage,
  saveDiagnosisAndReturnToQueue,
  saveCaseLibraryEntry,
  deleteCaseLibraryEntry,
    saveProfileSettings,
    finishConsultation
  } = useDoctorPrototype()

async function handleSaveCaseLibraryEntry(payload, callbacks = {}) {
  try {
    await saveCaseLibraryEntry(payload)
    callbacks.resolve?.()
  } catch (error) {
    callbacks.reject?.(error)
  }
}

async function handleDeleteCaseLibraryEntry(entryId, callbacks = {}) {
  try {
    await deleteCaseLibraryEntry(entryId)
    callbacks.resolve?.()
  } catch (error) {
    callbacks.reject?.(error)
  }
}
</script>

<template>
  <LoginView
    v-if="!state.loggedIn"
    :doctor-profile="state.doctorProfile"
    :initial-account="state.rememberedAccount"
    :login-pending="state.loginPending"
    :login-error="state.loginError"
    @login="login"
  />

  <ConsultationWorkspace
    v-else-if="state.activeModule === 'workspace'"
    :patient="activePatient"
    :agent-sending="state.agentSending"
    :agent-error="state.agentError"
    :workspace-loading="state.workspaceLoading"
    :workspace-error="state.workspaceError"
    :workspace-action-pending="state.workspaceActionPending"
    :workspace-action-error="state.workspaceActionError"
    :workspace-action-success="state.workspaceActionSuccess"
    :workspace-settings="state.settings.workspace"
    @send-agent-message="sendAgentMessage"
    @save-diagnosis-and-back="saveDiagnosisAndReturnToQueue"
    @finish-consultation="finishConsultation"
    @open-record="openRecord"
    @back-to-queue="returnToQueue"
  />

  <AppShell
    v-else
    :navigation-items="state.navigationItems"
    :active-module="state.activeModule"
    :current-module="activeNavigation"
    :doctor-profile="state.doctorProfile"
    :workspace-settings="state.settings.workspace"
    @navigate="setActiveModule"
    @update-duty-status="updateDutyStatus"
  >
    <QueueOverview
      v-if="state.activeModule === 'queue'"
      :summary="queueStats"
      :loading="state.queueLoading"
      :error="state.queueError"
      :patients="filteredPatients"
      :filters="state.queueFilters"
      :department-options="queueDepartments"
      :period-options="queuePeriods"
      @update-filter="updateQueueFilter"
      @start-consultation="openConsultation"
    />

    <RecordsManager
      v-if="state.activeModule === 'records'"
      :loading="state.recordsLoading"
      :error="state.recordsError"
      :detail-loading="state.recordDetailLoading"
      :records="state.recordSearchResults"
      :selected-record="activeRecord"
      @search-records="searchRecords"
      @select-record="openRecord"
    />

    <CaseLibrary
      v-else-if="state.activeModule === 'cases'"
      :entries="state.caseLibrary"
      :doctor-name="state.doctorProfile.name"
      @save-entry="handleSaveCaseLibraryEntry"
      @delete-entry="handleDeleteCaseLibraryEntry"
    />

    <SettingsCenter
      v-else-if="state.activeModule === 'settings'"
      :settings="state.settings"
      :doctor-profile="state.doctorProfile"
      :department-options="state.departmentOptions"
      :auth-token="state.authToken"
      @save-profile="saveProfileSettings"
      @logout="logout"
    />
  </AppShell>
</template>
