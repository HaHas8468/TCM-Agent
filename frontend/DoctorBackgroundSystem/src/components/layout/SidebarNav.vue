<script setup>
defineProps({
  navigationItems: {
    type: Array,
    default: () => []
  },
  activeModule: {
    type: String,
    default: ''
  },
  doctorProfile: {
    type: Object,
    default: () => ({})
  },
  compact: {
    type: Boolean,
    default: false
  }
})

defineEmits(['navigate', 'update-duty-status'])
</script>

<template>
  <aside class="sidebar" :class="{ 'sidebar--compact': compact }">
    <div class="sidebar__top">
      <div class="sidebar__brand">
        <h1 class="sidebar__brand-title">本草问方</h1>
      </div>

      <div class="sidebar__profile" :class="{ 'sidebar__profile--rest': doctorProfile.dutyStatus === '休息' }">
        <div class="sidebar__duty-toggle" aria-label="设置值班状态">
          <button
            type="button"
            class="sidebar__duty-button"
            :class="{ 'sidebar__duty-button--active': (doctorProfile.dutyStatus || '值班') === '值班' }"
            @click="$emit('update-duty-status', '值班')"
          >
            值班
          </button>
          <button
            type="button"
            class="sidebar__duty-button"
            :class="{ 'sidebar__duty-button--active': doctorProfile.dutyStatus === '休息' }"
            @click="$emit('update-duty-status', '休息')"
          >
            休息
          </button>
        </div>

        <h2 class="sidebar__doctor">{{ doctorProfile.name }}</h2>
        <p class="sidebar__meta">{{ doctorProfile.department }}</p>
        <p class="sidebar__meta sidebar__meta--secondary">工作时间：{{ doctorProfile.shift }}</p>
      </div>
    </div>

    <nav class="sidebar__nav">
      <button
        v-for="item in navigationItems"
        :key="item.key"
        type="button"
        class="sidebar__nav-item"
        :class="{ 'sidebar__nav-item--active': activeModule === item.key }"
        @click="$emit('navigate', item.key)"
      >
        <span class="sidebar__nav-label">{{ item.label }}</span>
      </button>
    </nav>
  </aside>
</template>

<style scoped>
.sidebar {
  --sidebar-primary: #2d6a4f;
  --sidebar-primary-dark: #1b4332;
  --sidebar-primary-light: #e8f5e9;
  --sidebar-text-main: #2c3e35;
  --sidebar-text-sub: #677a71;
  --sidebar-border: #e0eae4;
  --sidebar-white: #ffffff;
  --sidebar-shadow-md: 0 8px 24px rgba(45, 106, 79, 0.08);

  display: grid;
  gap: 28px;
  align-content: start;
  padding: 28px 22px;
}

.sidebar__top {
  display: grid;
  gap: 18px;
}

.sidebar__brand {
  padding: 0 8px;
}

.sidebar__brand-title {
  margin: 0;
  color: var(--sidebar-primary-dark);
  font-size: 32px;
  font-weight: 800;
  letter-spacing: 2px;
  line-height: 1.1;
}

.sidebar__profile {
  display: grid;
  gap: 10px;
  padding: 20px;
  border-radius: 22px;
  background: linear-gradient(135deg, var(--sidebar-primary), var(--sidebar-primary-dark));
  color: var(--sidebar-white);
  box-shadow: var(--sidebar-shadow-md);
}

.sidebar__profile--rest {
  background: linear-gradient(135deg, #5e796d, #405148);
}

.sidebar__duty-toggle {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px;
  padding: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.2);
}

.sidebar__duty-button {
  min-height: 34px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(255, 255, 255, 0.82);
  font-size: 13px;
  font-weight: 700;
  transition:
    background-color 0.3s ease,
    color 0.3s ease,
    transform 0.2s ease;
}

.sidebar__duty-button--active {
  background: rgba(255, 255, 255, 0.96);
  color: var(--sidebar-primary);
}

.sidebar__doctor {
  margin: 14px 0 0;
  font-size: 22px;
  font-weight: 700;
}

.sidebar__meta {
  margin: 0;
  font-size: 14px;
  line-height: 1.6;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.sidebar__meta--secondary {
  font-size: 13px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.8);
}

.sidebar__nav {
  display: grid;
  gap: 10px;
}

.sidebar__nav-item {
  display: grid;
  gap: 6px;
  width: 100%;
  border: 1px solid rgba(64, 81, 72, 0.1);
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.54);
  padding: 14px 16px;
  text-align: left;
  transition: 0.2s ease;
}

.sidebar__nav-item:hover {
  transform: translateX(3px);
}

.sidebar__nav-item--active {
  border-color: rgba(45, 106, 79, 0.18);
  background: linear-gradient(135deg, rgba(232, 245, 233, 0.96), rgba(255, 255, 255, 0.96));
  box-shadow: 0 12px 24px rgba(45, 106, 79, 0.08);
}

.sidebar__nav-label {
  font-weight: 700;
  color: var(--sidebar-primary-dark);
}

.sidebar--compact {
  gap: 22px;
  padding: 24px 18px;
}

.sidebar--compact .sidebar__brand-title {
  font-size: 28px;
}

.sidebar--compact .sidebar__nav-item {
  padding: 12px 14px;
}

.sidebar--compact .sidebar__profile {
  padding: 16px;
}
</style>
