<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { detectOS } from '../composables/useOS'

const { t } = useI18n()
// Default the tab to the visitor's actual OS. Synchronous detection so the
// first render lands on the correct panel — no flash of Windows content for
// mac users.
const activeTab = ref<'windows' | 'macos'>(detectOS())
</script>

<template>
  <section class="section">
    <div class="container">
      <h2 class="section-title">{{ t('install.title') }}</h2>

      <div class="tabs" role="tablist" :aria-label="t('install.title')">
        <button
          id="tab-windows"
          role="tab"
          :aria-selected="activeTab === 'windows'"
          :tabindex="activeTab === 'windows' ? 0 : -1"
          aria-controls="panel-windows"
          :class="{ active: activeTab === 'windows' }"
          @click="activeTab = 'windows'"
        >{{ t('install.windows.tab') }}</button>
        <button
          id="tab-macos"
          role="tab"
          :aria-selected="activeTab === 'macos'"
          :tabindex="activeTab === 'macos' ? 0 : -1"
          aria-controls="panel-macos"
          :class="{ active: activeTab === 'macos' }"
          @click="activeTab = 'macos'"
        >{{ t('install.macos.tab') }}</button>
      </div>

      <div v-if="activeTab === 'windows'" id="panel-windows" role="tabpanel" aria-labelledby="tab-windows" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.windows.step1_exe') }}</p>
        </div>
        <div class="step step--alt">
          <span class="step-num" aria-hidden="true">&mdash;</span>
          <p>{{ t('install.windows.step1_zip') }}</p>
        </div>
        <div class="step step--warning">
          <span class="step-num">
            <iconify-icon icon="material-symbols:warning-rounded" aria-hidden="true"></iconify-icon>
            <span class="step-num-text">2</span>
          </span>
          <p><strong>{{ t('install.windows.step2') }}</strong></p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.windows.step3') }}</p>
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

      <div v-if="activeTab === 'macos'" id="panel-macos" role="tabpanel" aria-labelledby="tab-macos" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.macos.step1_install', {
            userPath: '~/Library/Keyboard Layouts/',
            systemPath: '/Library/Keyboard Layouts/'
          }) }}</p>
        </div>
        <div class="step step--command">
          <span class="step-num">2</span>
          <p>{{ t('install.macos.step2_xattr', {
            cmd: 'xattr -dr com.apple.quarantine ~/Library/Keyboard\\ Layouts/Kirkouski\\ Typographic.bundle'
          }) }}</p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.macos.step3_logout') }}</p>
        </div>
        <div class="step">
          <span class="step-num">4</span>
          <p>{{ t('install.macos.step4_pick') }}</p>
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

/* Warning step (Windows reboot requirement) — visually loud so users
   don't skip it. The crash reports we get are 100% from people who
   skipped this step. */
.step--warning {
  background: rgba(212, 64, 58, 0.06);
  border-radius: 8px;
  padding: 1rem;
  margin: 0.5rem -1rem;
  border: 1px solid rgba(212, 64, 58, 0.18);
}

.step--warning .step-num {
  color: var(--color-altgr, #d4403a);
  font-size: 1.5rem;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.step--warning .step-num iconify-icon {
  font-size: 1.75rem;
}

.step--warning .step-num-text {
  font-family: var(--font-display);
  font-size: 1.5rem;
}

.step--warning p {
  color: var(--text);
}

.step--warning p strong {
  font-weight: 600;
}

/* macOS shell-command step (xattr quarantine clear). Same prominence as a
   numbered step, but the body text is monospace because it includes a
   verbatim command the user must run. Not styled as `step--alt` because
   it's mandatory, not optional. */
.step--command p {
  font-family: var(--font-mono, ui-monospace, 'JetBrains Mono', monospace);
  font-size: 0.85rem;
  background: var(--bg-subtle);
  padding: 0.5rem 0.75rem;
  border-radius: 6px;
  word-break: break-all;
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
