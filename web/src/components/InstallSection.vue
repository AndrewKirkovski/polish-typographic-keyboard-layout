<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
const activeTab = ref<'windows' | 'macos'>('windows')
</script>

<template>
  <section class="section">
    <div class="container">
      <h2 class="section-title">{{ t('install.title') }}</h2>

      <div class="tabs">
        <button
          :class="{ active: activeTab === 'windows' }"
          @click="activeTab = 'windows'"
        >{{ t('install.windows.tab') }}</button>
        <button
          :class="{ active: activeTab === 'macos' }"
          @click="activeTab = 'macos'"
        >{{ t('install.macos.tab') }}</button>
      </div>

      <div v-if="activeTab === 'windows'" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.windows.step1', { dll: 'pltypo.dll', script: 'install.ps1' }) }}</p>
        </div>
        <div class="step">
          <span class="step-num">2</span>
          <p>{{ t('install.windows.step2') }}</p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.windows.step3', { script: 'install.ps1' }) }}</p>
        </div>
        <div class="step">
          <span class="step-num">4</span>
          <p>{{ t('install.windows.step4') }}</p>
        </div>
        <div class="step">
          <span class="step-num">5</span>
          <p>{{ t('install.windows.step5') }}</p>
        </div>
        <p class="info-note">
          {{ t('install.windows.loginScreen') }}
        </p>
        <p class="uninstall-note">
          {{ t('install.windows.uninstall') }}
        </p>
        <p class="uninstall-note">
          {{ t('install.windows.hardCleanup', { cmd: '.\\install.ps1 -HardCleanup' }) }}
        </p>
      </div>

      <div v-if="activeTab === 'macos'" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.macos.step1', { file: 'polish_typographic.keylayout' }) }}</p>
        </div>
        <div class="step">
          <span class="step-num">2</span>
          <p>{{ t('install.macos.step2', {
            userPath: '~/Library/Keyboard Layouts/',
            systemPath: '/Library/Keyboard Layouts/'
          }) }}</p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.macos.step3') }}</p>
        </div>
        <div class="step">
          <span class="step-num">4</span>
          <p>{{ t('install.macos.step4') }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
.tabs {
  display: inline-flex;
  gap: 2px;
  background: var(--bg-subtle);
  border-radius: 8px;
  padding: 3px;
  margin-bottom: 2rem;
}

.tabs button {
  font-family: var(--font-body);
  font-size: 0.85rem;
  font-weight: 500;
  padding: 8px 24px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
}

.tabs button.active {
  background: var(--bg-elevated);
  color: var(--text);
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.install-steps {
  max-width: 600px;
}

.step {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  padding: 1rem 0;
  border-bottom: 1px solid var(--border);
}

.step:last-of-type {
  border-bottom: none;
}

.step-num {
  font-family: var(--font-display);
  font-size: 1.5rem;
  color: var(--color-altgr);
  line-height: 1;
  min-width: 24px;
  flex-shrink: 0;
}

.step p {
  color: var(--text-secondary);
  line-height: 1.5;
  padding-top: 0.15rem;
}

.info-note {
  margin-top: 1.5rem;
  padding: 1rem;
  background: var(--bg-subtle);
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--text-secondary);
  border-left: 3px solid var(--color-altgr);
}

.uninstall-note {
  margin-top: 0.75rem;
  padding: 1rem;
  background: var(--bg-subtle);
  border-radius: 8px;
  font-size: 0.85rem;
  color: var(--text-muted);
}
</style>
