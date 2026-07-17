<script setup>
import { reactive, ref, watch } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  settings: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['save'])

const form = reactive({
  twoFactorEnabled: false,
  loginProtection: false,
  deviceReviewRequired: false,
  sessionTimeoutMinutes: 30,
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const errorMessage = ref('')

function syncForm() {
  form.twoFactorEnabled = props.settings.twoFactorEnabled
  form.loginProtection = props.settings.loginProtection
  form.deviceReviewRequired = props.settings.deviceReviewRequired
  form.sessionTimeoutMinutes = props.settings.sessionTimeoutMinutes
  form.currentPassword = ''
  form.newPassword = ''
  form.confirmPassword = ''
  errorMessage.value = ''
}

watch(
  () => props.settings,
  () => {
    syncForm()
  },
  { immediate: true, deep: true }
)

function submit() {
  const wantsPasswordChange = form.currentPassword || form.newPassword || form.confirmPassword

  if (wantsPasswordChange) {
    if (!form.currentPassword || !form.newPassword || !form.confirmPassword) {
      errorMessage.value = '如需修改密码，请完整填写当前密码、新密码和确认密码。'
      return
    }

    if (form.newPassword.length < 8) {
      errorMessage.value = '新密码至少需要 8 位。'
      return
    }

    if (form.newPassword !== form.confirmPassword) {
      errorMessage.value = '两次输入的新密码不一致，请重新确认。'
      return
    }
  }

  errorMessage.value = ''
  emit('save', {
    twoFactorEnabled: form.twoFactorEnabled,
    loginProtection: form.loginProtection,
    deviceReviewRequired: form.deviceReviewRequired,
    sessionTimeoutMinutes: Number(form.sessionTimeoutMinutes),
    passwordChanged: Boolean(wantsPasswordChange)
  })
}
</script>

<template>
  <BaseCard title="账号安全" subtitle="调整登录保护、会话超时和二次验证策略，支持模拟修改密码。">
    <div class="security-card">
      <div class="security-card__meta">
        <span class="pill">最近登录：{{ settings.lastLogin }}</span>
        <span class="pill">密码更新时间：{{ settings.lastPasswordUpdate }}</span>
        <span class="pill">可信设备：{{ settings.trustedDevices }} 台</span>
      </div>

      <div class="security-card__toggle-list">
        <label class="security-card__toggle">
          <input v-model="form.twoFactorEnabled" type="checkbox" />
          <span>启用二次验证</span>
        </label>
        <label class="security-card__toggle">
          <input v-model="form.loginProtection" type="checkbox" />
          <span>开启异地登录保护</span>
        </label>
        <label class="security-card__toggle">
          <input v-model="form.deviceReviewRequired" type="checkbox" />
          <span>新增设备需人工审核</span>
        </label>
      </div>

      <label class="security-card__field">
        <span>会话超时（分钟）</span>
        <input v-model="form.sessionTimeoutMinutes" class="field" type="number" min="15" step="15" />
      </label>

      <div class="security-card__password-grid">
        <label class="security-card__field">
          <span>当前密码</span>
          <input v-model="form.currentPassword" class="field" type="password" />
        </label>
        <label class="security-card__field">
          <span>新密码</span>
          <input v-model="form.newPassword" class="field" type="password" />
        </label>
        <label class="security-card__field">
          <span>确认新密码</span>
          <input v-model="form.confirmPassword" class="field" type="password" />
        </label>
      </div>

      <p v-if="errorMessage" class="security-card__error">{{ errorMessage }}</p>

      <button type="button" class="primary-button" @click="submit">保存安全设置</button>
    </div>
  </BaseCard>
</template>

<style scoped>
.security-card {
  display: grid;
  gap: 14px;
}

.security-card__meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.security-card__toggle-list {
  display: grid;
  gap: 10px;
}

.security-card__toggle {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 16px;
  background: #f7fafc;
}

.security-card__field {
  display: grid;
  gap: 8px;
}

.security-card__field span {
  color: #59738f;
  font-size: 13px;
}

.security-card__password-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.security-card__error {
  margin: 0;
  color: #c1574f;
  font-size: 13px;
}

@media (max-width: 960px) {
  .security-card__password-grid {
    grid-template-columns: 1fr;
  }
}
</style>
