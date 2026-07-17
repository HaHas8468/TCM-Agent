<script setup>
import SidebarNav from './SidebarNav.vue'

defineProps({
  navigationItems: {
    type: Array,
    default: () => []
  },
  activeModule: {
    type: String,
    default: ''
  },
  currentModule: {
    type: Object,
    default: () => ({})
  },
  doctorProfile: {
    type: Object,
    default: () => ({})
  },
  workspaceSettings: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['navigate', 'update-duty-status'])
</script>

<template>
  <div class="shell" :class="{ 'shell--compact': workspaceSettings.compactSidebar }">
    <div class="shell__sidebar">
      <SidebarNav
        :navigation-items="navigationItems"
        :active-module="activeModule"
        :doctor-profile="doctorProfile"
        :compact="workspaceSettings.compactSidebar"
        @navigate="$emit('navigate', $event)"
        @update-duty-status="$emit('update-duty-status', $event)"
      />
    </div>

    <main class="shell__content">
      <header class="shell__header">
        <div>
          <h2 class="shell__title">{{ currentModule.label }}</h2>
        </div>
      </header>

      <section class="shell__body">
        <slot />
      </section>
    </main>
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 320px minmax(0, 1fr);
  min-height: 100vh;
}

.shell__sidebar {
  border-right: 1px solid #e0eae4;
  background: #ffffff;
}

.shell__content {
  padding: 28px;
}

.shell__header {
  margin-bottom: 20px;
}

.shell__title {
  margin: 0;
  font-size: 34px;
  color: #1b4332;
}

.shell__body {
  min-height: calc(100vh - 180px);
}

.shell--compact {
  grid-template-columns: 272px minmax(0, 1fr);
}

@media (max-width: 1280px) {
  .shell {
    grid-template-columns: 1fr;
  }

  .shell__sidebar {
    border-right: 0;
    border-bottom: 1px solid #e0eae4;
  }
}

@media (max-width: 960px) {
  .shell__content {
    padding: 20px;
  }
}
</style>
