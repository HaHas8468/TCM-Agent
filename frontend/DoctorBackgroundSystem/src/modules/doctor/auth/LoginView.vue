<script setup>
import { reactive } from 'vue'

const props = defineProps({
  doctorProfile: {
    type: Object,
    default: () => ({})
  },
  initialAccount: {
    type: String,
    default: ''
  },
  loginPending: {
    type: Boolean,
    default: false
  },
  loginError: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['login'])

const form = reactive({
  account: props.initialAccount || 'doctor.lin',
  password: 'Prototype123',
  remember: true
})

function submit() {
  if (props.loginPending) {
    return
  }

  emit('login', {
    account: form.account,
    password: form.password,
    remember: form.remember
  })
}
</script>

<template>
  <div class="login">
    <div class="login__glow login__glow--left" aria-hidden="true"></div>
    <div class="login__glow login__glow--right" aria-hidden="true"></div>

    <section class="login-card">
      <header class="brand-header">
        <h1 class="main-title">本草问方</h1>
        <p class="sub-title">中医药智能诊疗工作台</p>
      </header>

      <form class="login-form" @submit.prevent="submit">
        <label class="form-group">
          <span class="form-label">用户名</span>
          <input
            v-model="form.account"
            class="input-control"
            type="text"
            placeholder="请输入您的工号或邮箱"
            autocomplete="username"
            :disabled="loginPending"
          />
        </label>

        <label class="form-group">
          <span class="form-label">密码</span>
          <input
            v-model="form.password"
            class="input-control"
            type="password"
            placeholder="请输入密码"
            autocomplete="current-password"
            :disabled="loginPending"
          />
        </label>

        <div class="form-actions">
          <label class="remember-me">
            <input v-model="form.remember" type="checkbox" :disabled="loginPending" />
            <span>记住账号</span>
          </label>

          <button type="button" class="forgot-password" :disabled="loginPending">忘记密码？</button>
        </div>

        <p v-if="loginError" class="form-error">{{ loginError }}</p>

        <button type="submit" class="btn-submit" :disabled="loginPending">
          {{ loginPending ? '登录中...' : '登录' }}
        </button>
      </form>

      <footer class="footer-copyright">© 2026 本草问方 智能诊疗系统</footer>
    </section>
  </div>
</template>

<style>
.login {
  --login-bg-start: #e8f5e9;
  --login-bg-end: #ffffff;
  --login-card-bg: rgba(255, 255, 255, 0.85);
  --login-card-border: rgba(255, 255, 255, 0.7);
  --login-shadow-soft: rgba(0, 0, 0, 0.04);
  --login-shadow-hover: rgba(45, 106, 79, 0.08);
  --login-title: #1b4332;
  --login-brand: #2d6a4f;
  --login-label: #405148;
  --login-muted: #677a71;
  --login-border: #d1dcd6;
  --login-input-bg: rgba(248, 250, 249, 0.8);
  --login-footer: #99a7a0;
  --login-focus-ring: rgba(45, 106, 79, 0.1);
  --login-glow: rgba(45, 106, 79, 0.05);
  --login-button-shadow: rgba(45, 106, 79, 0.2);
  --login-button-shadow-hover: rgba(27, 67, 50, 0.3);

  position: relative;
  display: grid;
  place-items: center;
  min-height: 100vh;
  padding: 24px;
  overflow: hidden;
  background: linear-gradient(135deg, var(--login-bg-start) 0%, var(--login-bg-end) 100%);
  isolation: isolate;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, 'PingFang SC',
    'Microsoft YaHei', sans-serif;
}

.login *,
.login *::before,
.login *::after {
  box-sizing: border-box;
}

.login input,
.login button {
  font: inherit;
}

.login__glow {
  position: absolute;
  border-radius: 50%;
  background: var(--login-glow);
  filter: blur(50px);
  z-index: -1;
}

.login__glow--left {
  top: -120px;
  left: -120px;
  width: 420px;
  height: 420px;
}

.login__glow--right {
  right: -140px;
  bottom: -140px;
  width: 320px;
  height: 320px;
}

.login-card {
  width: min(100%, 420px);
  padding: 40px 35px;
  border: 1px solid var(--login-card-border);
  border-radius: 20px;
  background: var(--login-card-bg);
  box-shadow: 0 12px 40px var(--login-shadow-soft);
  backdrop-filter: blur(20px);
  text-align: center;
  transition:
    transform 0.3s ease,
    box-shadow 0.3s ease;
}

.login-card:hover {
  box-shadow: 0 16px 48px var(--login-shadow-hover);
  transform: translateY(-2px);
}

.brand-header {
  margin-bottom: 35px;
}

.main-title {
  margin: 0 0 8px;
  color: var(--login-title);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 4px;
}

.sub-title {
  margin: 0;
  color: var(--login-muted);
  font-size: 13px;
  font-weight: 400;
  letter-spacing: 2px;
}

.login-form {
  text-align: left;
}

.form-group {
  display: grid;
  gap: 8px;
  margin-bottom: 22px;
}

.form-label {
  padding-left: 2px;
  color: var(--login-label);
  font-size: 13px;
  font-weight: 500;
}

.input-control {
  width: 100%;
  height: 48px;
  padding: 0 16px;
  border: 1px solid var(--login-border);
  border-radius: 10px;
  background-color: var(--login-input-bg);
  color: var(--login-brand);
  font-size: 15px;
  outline: none;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease,
    background-color 0.2s ease;
}

.input-control::placeholder {
  color: rgba(103, 122, 113, 0.82);
}

.input-control:focus {
  border-color: var(--login-brand);
  background-color: #ffffff;
  box-shadow: 0 0 0 3px var(--login-focus-ring);
}

.form-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  margin-bottom: 25px;
  font-size: 13px;
}

.remember-me {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--login-muted);
  cursor: pointer;
}

.remember-me input {
  accent-color: var(--login-brand);
}

.forgot-password {
  border: none;
  padding: 0;
  background: transparent;
  color: var(--login-brand);
  font-size: 13px;
  cursor: pointer;
  transition: color 0.2s ease;
}

.forgot-password:hover {
  color: var(--login-title);
  text-decoration: underline;
}

.forgot-password:disabled,
.btn-submit:disabled,
.input-control:disabled {
  cursor: not-allowed;
}

.form-error {
  margin: 0 0 14px;
  color: #c1574f;
  font-size: 13px;
  line-height: 1.5;
}

.btn-submit {
  width: 100%;
  height: 48px;
  border: none;
  border-radius: 10px;
  background-color: var(--login-brand);
  color: #ffffff;
  box-shadow: 0 4px 12px var(--login-button-shadow);
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 4px;
  cursor: pointer;
  transition:
    background-color 0.2s ease,
    box-shadow 0.2s ease,
    transform 0.2s ease;
}

.btn-submit:hover {
  background-color: var(--login-title);
  box-shadow: 0 6px 16px var(--login-button-shadow-hover);
}

.btn-submit:active {
  transform: scale(0.99);
}

.btn-submit:disabled {
  opacity: 0.72;
  box-shadow: none;
  transform: none;
}

.footer-copyright {
  margin-top: 30px;
  color: var(--login-footer);
  font-size: 11px;
  letter-spacing: 0.5px;
}

@media (max-width: 520px) {
  .login {
    padding: 16px;
  }

  .login-card {
    padding: 32px 22px;
  }

  .form-actions {
    flex-direction: column;
    align-items: flex-start;
  }

  .forgot-password {
    align-self: flex-end;
  }
}
</style>
