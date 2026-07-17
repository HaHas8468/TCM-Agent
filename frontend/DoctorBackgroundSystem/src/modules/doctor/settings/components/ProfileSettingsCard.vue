<script setup>
import { reactive, watch } from 'vue'
import BaseCard from '../../../../components/ui/BaseCard.vue'

const props = defineProps({
  profile: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['save'])

const form = reactive({
  name: '',
  title: '',
  role: '',
  account: '',
  phone: '',
  email: '',
  department: '',
  clinicRoom: '',
  organization: '',
  shift: '',
  focus: '',
  bio: '',
  signature: ''
})

function syncForm() {
  Object.assign(form, props.profile || {})
}

watch(
  () => props.profile,
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
  <BaseCard title="个人资料" subtitle="维护医生展示信息、门诊归属和个性化签名，保存后同步侧边栏。">
    <div class="settings-form">
      <div class="settings-form__grid">
        <label class="settings-form__field">
          <span>姓名</span>
          <input v-model="form.name" class="field" type="text" />
        </label>
        <label class="settings-form__field">
          <span>职称</span>
          <input v-model="form.title" class="field" type="text" />
        </label>
        <label class="settings-form__field">
          <span>角色</span>
          <select v-model="form.role" class="select">
            <option value="管理员">管理员</option>
            <option value="普通医师">普通医师</option>
          </select>
        </label>
        <label class="settings-form__field">
          <span>登录账号</span>
          <input v-model="form.account" class="field" type="text" />
        </label>
        <label class="settings-form__field">
          <span>手机号</span>
          <input v-model="form.phone" class="field" type="text" />
        </label>
        <label class="settings-form__field">
          <span>邮箱</span>
          <input v-model="form.email" class="field" type="email" />
        </label>
        <label class="settings-form__field">
          <span>所属科室</span>
          <input v-model="form.department" class="field" type="text" />
        </label>
        <label class="settings-form__field">
          <span>诊室</span>
          <input v-model="form.clinicRoom" class="field" type="text" />
        </label>
      </div>

      <label class="settings-form__field">
        <span>机构名称</span>
        <input v-model="form.organization" class="field" type="text" />
      </label>

      <label class="settings-form__field">
        <span>值班时间</span>
        <input v-model="form.shift" class="field" type="text" />
      </label>

      <label class="settings-form__field">
        <span>专业方向</span>
        <input v-model="form.focus" class="field" type="text" />
      </label>

      <label class="settings-form__field">
        <span>个人简介</span>
        <textarea v-model="form.bio" class="textarea" />
      </label>

      <label class="settings-form__field">
        <span>个性签名</span>
        <input v-model="form.signature" class="field" type="text" />
      </label>

      <button type="button" class="primary-button" @click="submit">保存个人资料</button>
    </div>
  </BaseCard>
</template>

<style scoped>
.settings-form {
  display: grid;
  gap: 14px;
}

.settings-form__grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.settings-form__field {
  display: grid;
  gap: 8px;
}

.settings-form__field span {
  color: #59738f;
  font-size: 13px;
}

@media (max-width: 960px) {
  .settings-form__grid {
    grid-template-columns: 1fr;
  }
}
</style>
