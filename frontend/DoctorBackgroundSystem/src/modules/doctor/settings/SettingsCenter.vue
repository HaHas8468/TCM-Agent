<script setup>
import { computed, reactive, ref, watch } from 'vue'
import {
  buildDoctorContactUpdatePayload,
  buildDoctorProfileUpdatePayload,
  doctorShiftOptions,
  resolveDoctorDepartment,
  resolveDoctorShift
} from '../../../api/doctorProfileApi'
import { getDoctorSchedules, updateDoctorSchedule } from '../../../api/doctorScheduleApi'
import settingsEmptyImage from '../../../assets/empty-states/settings.png'

const props = defineProps({
  settings: {
    type: Object,
    default: () => ({})
  },
  doctorProfile: {
    type: Object,
    default: () => ({})
  },
  departmentOptions: {
    type: Array,
    default: () => []
  },
  authToken: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['save-profile', 'logout'])

const activeSection = ref('')
const profileError = ref('')
const profileSaving = ref(false)
const scheduleLoading = ref(false)
const scheduleError = ref('')
const scheduleDays = ref([])
const scheduleUpdatingKey = ref('')
const shiftOptions = doctorShiftOptions
const mergedDepartmentOptions = computed(() => {
  const profile = props.settings.profile || {}

  return Array.from(
    new Set(
      [props.departmentOptions, profile.department, props.doctorProfile.department]
        .flat()
        .map((item) => String(item || '').trim())
        .filter(Boolean)
    )
  )
})

const profileForm = reactive({
  name: '',
  account: '',
  department: '',
  shift: '',
  focus: '',
  bio: '',
  phone: '',
  password: '',
  confirmPassword: ''
})

const passwordMismatch = computed(() => {
  return Boolean(
    profileForm.confirmPassword && profileForm.password !== profileForm.confirmPassword
  )
})

watch(
  () => [profileForm.password, profileForm.confirmPassword],
  () => {
    if (profileError.value && profileError.value.includes('密码')) {
      profileError.value = ''
    }
  }
)

function syncProfileForm() {
  const profile = props.settings.profile || {}

  profileForm.name = profile.name || props.doctorProfile.name || ''
  profileForm.account = profile.account || props.doctorProfile.account || ''
  profileForm.department = resolveDoctorDepartment(
    profile.department || props.doctorProfile.department,
    mergedDepartmentOptions.value
  )
  profileForm.shift = resolveDoctorShift(profile.shift || props.doctorProfile.shift)
  profileForm.focus = profile.focus || props.doctorProfile.focus || ''
  profileForm.bio = profile.bio || ''
  profileForm.phone = profile.phone || ''
  profileForm.password = ''
  profileForm.confirmPassword = ''
}

async function loadSchedules() {
  if (!props.authToken) {
    scheduleError.value = '当前登录状态已失效，请重新登录后再查看排班。'
    return
  }
  scheduleLoading.value = true
  scheduleError.value = ''
  try {
    const result = await getDoctorSchedules(props.authToken, 30)
    scheduleDays.value = Array.isArray(result?.days) ? result.days : []
  } catch (error) {
    scheduleError.value = error?.message || '排班加载失败，请稍后重试。'
  } finally {
    scheduleLoading.value = false
  }
}

async function changeSchedule(day, item) {
  const action = item.status === 'closed' ? 'reopen' : 'close'
  const key = `${day.date}-${item.period}`
  scheduleUpdatingKey.value = key
  scheduleError.value = ''
  try {
    await updateDoctorSchedule(props.authToken, day.date, item.period, action)
    await loadSchedules()
  } catch (error) {
    scheduleError.value = error?.message || '排班更新失败，请稍后重试。'
  } finally {
    scheduleUpdatingKey.value = ''
  }
}

async function selectSection(section) {
  activeSection.value = section
  profileError.value = ''
  profileSaving.value = false

  if (section === 'profile') {
    syncProfileForm()
  }
  if (section === 'schedule') {
    await loadSchedules()
  }
}

function clearSelection() {
  activeSection.value = ''
  profileError.value = ''
  profileSaving.value = false
}

function saveProfile() {
  profileError.value = ''

  if (profileForm.password || profileForm.confirmPassword) {
    if (!profileForm.password) {
      profileError.value = '请输入新密码'
      return
    }
    if (!profileForm.confirmPassword) {
      profileError.value = '请输入确认新密码'
      return
    }
    if (profileForm.password !== profileForm.confirmPassword) {
      profileError.value = '确认密码和新密码不匹配'
      return
    }
  }

  profileSaving.value = true

  emit(
    'save-profile',
    buildDoctorProfileUpdatePayload({
      ...profileForm,
      phone: profileForm.phone
    }),
    () => {
      profileSaving.value = false
      clearSelection()
    },
    (message) => {
      profileSaving.value = false
      profileError.value = message || '个人资料保存失败，请稍后重试。'
    }
  )
}
</script>

<template>
  <div class="settings-page">
    <aside class="settings-menu">
      <button
        type="button"
        class="settings-menu__item"
        :class="{ 'settings-menu__item--active': activeSection === 'profile' }"
        @click="selectSection('profile')"
      >
        个人资料
      </button>

      <button
        type="button"
        class="settings-menu__item"
        :class="{ 'settings-menu__item--active': activeSection === 'schedule' }"
        @click="selectSection('schedule')"
      >
        排班管理
      </button>

      <span class="settings-menu__divider"></span>

      <button type="button" class="settings-menu__item settings-menu__item--danger" @click="emit('logout')">
        退出登录
      </button>
    </aside>

    <section class="settings-detail">
      <div v-if="!activeSection" class="settings-empty">
        <img class="settings-empty__image" :src="settingsEmptyImage" alt="请选择设置项" />
        <strong>请选择左侧设置项</strong>
        <span>可维护个人资料，包括电话和密码修改。</span>
      </div>

      <div v-else-if="activeSection === 'profile'" class="settings-panel">
        <header class="settings-panel__header">
          <h3>个人资料</h3>
        </header>

        <div class="settings-form settings-form--profile">
          <label class="settings-form__field">
            <span>姓名</span>
            <input v-model="profileForm.name" class="field" type="text" />
          </label>

          <label class="settings-form__field">
            <span>医生账号（工号）</span>
            <input v-model="profileForm.account" class="field" type="text" disabled />
          </label>

          <label class="settings-form__field">
            <span>所属科室</span>
            <select v-model="profileForm.department" class="select">
              <option v-for="item in mergedDepartmentOptions" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>

          <label class="settings-form__field">
            <span>门诊时间</span>
            <select v-model="profileForm.shift" class="select">
              <option v-for="item in shiftOptions" :key="item" :value="item">{{ item }}</option>
            </select>
          </label>

          <label class="settings-form__field">
            <span>联系电话</span>
            <input v-model="profileForm.phone" class="field" type="tel" />
          </label>

          <label class="settings-form__field">
            <span>新密码</span>
            <input v-model="profileForm.password" class="field" type="password" placeholder="不修改请留空" />
          </label>

          <label class="settings-form__field">
            <span>确认新密码</span>
            <input
              v-model="profileForm.confirmPassword"
              class="field"
              :class="{ 'field--error': passwordMismatch }"
              type="password"
              placeholder="不修改请留空"
            />
            <span v-if="passwordMismatch" class="field-error">确认密码和新密码不匹配</span>
          </label>

          <label class="settings-form__field settings-form__field--wide">
            <span>专业擅长（门诊信息显示）</span>
            <input v-model="profileForm.focus" class="field" type="text" />
          </label>

          <label class="settings-form__field settings-form__field--wide">
            <span>个人简介</span>
            <textarea v-model="profileForm.bio" class="textarea" />
          </label>
        </div>

        <p v-if="profileError" class="settings-panel__error">{{ profileError }}</p>

        <div class="settings-panel__actions">
          <button type="button" class="ghost-button" :disabled="profileSaving" @click="clearSelection">取消</button>
          <button type="button" class="primary-button" :disabled="profileSaving" @click="saveProfile">
            {{ profileSaving ? '保存中...' : '保存修改' }}
          </button>
        </div>
      </div>

      <div v-else class="settings-panel">
        <header class="settings-panel__header">
          <h3>未来 30 天排班</h3>
          <p class="schedule-tip">关闭时段后将停止新患者预约，已预约患者不受影响。</p>
        </header>

        <p v-if="scheduleError" class="settings-panel__error">{{ scheduleError }}</p>
        <div v-else-if="scheduleLoading" class="schedule-empty">正在加载排班…</div>
        <div v-else class="schedule-list">
          <article v-for="day in scheduleDays" :key="day.date" class="schedule-day">
            <header>
              <strong>{{ day.date }} {{ day.weekday }}</strong>
              <span v-if="!day.periods?.length">非出诊日</span>
            </header>
            <div v-if="day.periods?.length" class="schedule-periods">
              <div v-for="item in day.periods" :key="item.period" class="schedule-period">
                <div>
                  <strong>{{ item.label }} {{ item.start_time }}–{{ item.end_time }}</strong>
                  <span>{{ item.status === 'closed' ? '已停诊' : `可预约 ${item.available_slots} 个，已预约 ${item.booked_count} 个` }}</span>
                </div>
                <button
                  type="button"
                  class="ghost-button"
                  :disabled="scheduleUpdatingKey === `${day.date}-${item.period}`"
                  @click="changeSchedule(day, item)"
                >
                  {{ scheduleUpdatingKey === `${day.date}-${item.period}` ? '处理中…' : (item.status === 'closed' ? '恢复出诊' : '停诊') }}
                </button>
              </div>
            </div>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<style>
.settings-page {
  display: grid;
  grid-template-columns: minmax(220px, 280px) minmax(0, 1fr);
  gap: 28px;
  align-items: start;
}

.settings-page *,
.settings-page *::before,
.settings-page *::after {
  box-sizing: border-box;
}

.settings-page button,
.settings-page input,
.settings-page select,
.settings-page textarea {
  font: inherit;
}

.settings-menu,
.settings-detail {
  border: 1px solid var(--border-soft);
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 18px 36px rgba(45, 106, 79, 0.08);
}

.settings-menu {
  display: grid;
  gap: 10px;
  padding: 18px;
}

.settings-menu__item {
  min-height: 54px;
  border: 1px solid transparent;
  outline: none;
  border-radius: 12px;
  background: transparent;
  color: var(--text-main);
  padding: 0 18px;
  text-align: left;
  font-size: 18px;
  font-weight: 700;
  transition:
    background-color 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

.settings-menu__item:hover {
  transform: translateX(2px);
  background: rgba(232, 245, 233, 0.55);
}

.settings-menu__item--active {
  border-color: rgba(45, 106, 79, 0.18);
  background: var(--brand-soft);
  color: var(--brand-deep);
}

.settings-menu__item:focus-visible {
  border-color: rgba(45, 106, 79, 0.28);
  box-shadow: 0 0 0 3px rgba(45, 106, 79, 0.08);
}

.settings-menu__divider {
  height: 1px;
  margin: 12px 8px;
  background: var(--border-soft);
}

.settings-menu__item--danger {
  color: #c1574f;
}

.settings-detail {
  min-height: 620px;
  padding: 36px;
}

.settings-empty {
  display: grid;
  gap: 12px;
  place-items: center;
  align-content: center;
  min-height: 548px;
  color: var(--text-subtle);
  text-align: center;
}

.settings-empty__image {
  width: min(360px, 72vw);
  height: auto;
}

.settings-empty strong {
  color: var(--text-main);
  font-size: 24px;
}

.settings-empty span {
  font-size: 14px;
}

.settings-panel {
  display: grid;
  gap: 28px;
}

.settings-panel__header {
  padding-bottom: 18px;
  border-bottom: 1px solid var(--border-soft);
}

.settings-panel__header h3 {
  margin: 0;
  color: var(--brand-deep);
  font-size: 26px;
}

.schedule-tip {
  margin: 10px 0 0;
  color: var(--text-subtle);
}

.schedule-list {
  display: grid;
  gap: 12px;
  max-height: 640px;
  overflow: auto;
  padding-right: 4px;
}

.schedule-day {
  display: grid;
  gap: 10px;
  padding: 16px;
  border: 1px solid var(--border-soft);
  border-radius: 14px;
  background: rgba(248, 251, 249, 0.8);
}

.schedule-day > header,
.schedule-period,
.schedule-period > div {
  display: flex;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
}

.schedule-day > header span,
.schedule-period span {
  color: var(--text-subtle);
  font-size: 14px;
}

.schedule-periods {
  display: grid;
  gap: 8px;
}

.schedule-period {
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
}

.schedule-period > div {
  align-items: flex-start;
  flex-direction: column;
  gap: 4px;
}

.schedule-empty {
  padding: 48px 0;
  color: var(--text-subtle);
  text-align: center;
}

.settings-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22px;
}

.settings-form--profile {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.settings-form__field {
  display: grid;
  gap: 8px;
}

.settings-form__field--wide {
  grid-column: 1 / -1;
}

.settings-form__field span {
  color: var(--text-subtle);
  font-size: 14px;
  font-weight: 700;
}

.settings-form :deep(.field),
.settings-form :deep(.select),
.settings-form :deep(.textarea) {
  min-height: 46px;
  border-radius: 10px;
}

.settings-form :deep(.field:disabled) {
  color: var(--text-faint);
  background: rgba(244, 247, 245, 0.8);
  cursor: not-allowed;
}

.settings-form :deep(.field--error) {
  border-color: #c1574f;
  box-shadow: 0 0 0 3rpx rgba(193, 87, 79, 0.12);
}

.field-error {
  display: block;
  margin-top: 6rpx;
  color: #c1574f;
  font-size: 13rpx;
  font-weight: 600;
}

.settings-form :deep(.textarea) {
  min-height: 118px;
}

.settings-panel__error {
  margin: -10px 0 0;
  color: #c1574f;
  font-size: 14px;
}

.settings-panel__actions {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  flex-wrap: wrap;
  gap: 14px;
}

.settings-panel__actions .primary-button,
.settings-panel__actions .ghost-button {
  min-width: 104px;
  min-height: 44px;
}

@media (max-width: 1180px) {
  .settings-page {
    grid-template-columns: 1fr;
  }

  .settings-detail {
    min-height: 520px;
  }

  .settings-empty {
    min-height: 448px;
  }
}

@media (max-width: 760px) {
  .settings-detail {
    padding: 24px;
  }

  .settings-form,
  .settings-form--profile {
    grid-template-columns: 1fr;
  }
}
</style>
