<script setup lang="ts">
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { detectOS } from '../composables/useOS'

const { t } = useI18n()

type InstallTab = 'win-exe' | 'win-zip' | 'mac-dmg' | 'mac-zip'
const activeTab = ref<InstallTab>(detectOS() === 'macos' ? 'mac-dmg' : 'win-exe')
</script>

<template>
  <section class="section">
    <div class="container">
      <h2 class="section-title">{{ t('install.title') }}</h2>

      <div class="tabs" role="tablist" :aria-label="t('install.title')">
        <button
          v-for="tab in ([
            { id: 'win-exe', label: `${t('install.windows.tab')} · ${t('install.windows.subtab_exe')}` },
            { id: 'win-zip', label: `${t('install.windows.tab')} · ${t('install.windows.subtab_zip')}` },
            { id: 'mac-dmg', label: `${t('install.macos.tab')} · ${t('install.macos.subtab_dmg')}` },
            { id: 'mac-zip', label: `${t('install.macos.tab')} · ${t('install.macos.subtab_zip')}` },
          ] as const)"
          :key="tab.id"
          :id="`tab-${tab.id}`"
          role="tab"
          :aria-selected="activeTab === tab.id"
          :tabindex="activeTab === tab.id ? 0 : -1"
          :aria-controls="`panel-${tab.id}`"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id as InstallTab"
        >{{ tab.label }}</button>
      </div>

      <!-- ── Windows EXE ───────────────────────────────────────────── -->
      <div v-if="activeTab === 'win-exe'" id="panel-win-exe" role="tabpanel" aria-labelledby="tab-win-exe" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.windows.exe.step1') }}</p>
        </div>
        <div class="step">
          <span class="step-num">2</span>
          <p>{{ t('install.windows.exe.step2') }}</p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.windows.exe.step3') }}</p>
        </div>
        <p class="uninstall-note">{{ t('install.windows.exe.uninstall') }}</p>
        <p class="info-note">{{ t('install.windows.loginScreen') }}</p>
      </div>

      <!-- ── Windows ZIP ───────────────────────────────────────────── -->
      <div v-if="activeTab === 'win-zip'" id="panel-win-zip" role="tabpanel" aria-labelledby="tab-win-zip" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.windows.zip.step1') }}</p>
        </div>
        <div class="step step--warning">
          <span class="step-num">
            <iconify-icon icon="material-symbols:warning-rounded" aria-hidden="true"></iconify-icon>
            <span class="step-num-text">2</span>
          </span>
          <p><strong>{{ t('install.windows.zip.step2') }}</strong></p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.windows.zip.step3') }}</p>
        </div>
        <p class="uninstall-note">{{ t('install.windows.zip.uninstall') }}</p>
        <p class="info-note">{{ t('install.windows.loginScreen') }}</p>
        <p class="uninstall-note">
          {{ t('install.windows.hardCleanup', { cmd: '.\\install.ps1 -HardCleanup' }) }}
        </p>
      </div>

      <!-- ── macOS DMG ─────────────────────────────────────────────── -->
      <div v-if="activeTab === 'mac-dmg'" id="panel-mac-dmg" role="tabpanel" aria-labelledby="tab-mac-dmg" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.macos.dmg.step1') }}</p>
        </div>
        <div class="step">
          <span class="step-num">2</span>
          <p>{{ t('install.macos.dmg.step2') }}</p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.macos.dmg.step3') }}</p>
        </div>
      </div>

      <!-- ── macOS ZIP ─────────────────────────────────────────────── -->
      <div v-if="activeTab === 'mac-zip'" id="panel-mac-zip" role="tabpanel" aria-labelledby="tab-mac-zip" class="install-steps">
        <div class="step">
          <span class="step-num">1</span>
          <p>{{ t('install.macos.zip.step1', {
            userPath: '~/Library/Keyboard Layouts/',
            systemPath: '/Library/Keyboard Layouts/'
          }) }}</p>
        </div>
        <div class="step step--command">
          <span class="step-num">2</span>
          <p>{{ t('install.macos.zip.step2', {
            cmd: 'xattr -dr com.apple.quarantine ~/Library/Keyboard\\ Layouts/Kirkouski\\ Typographic.bundle'
          }) }}</p>
        </div>
        <div class="step">
          <span class="step-num">3</span>
          <p>{{ t('install.macos.zip.step3') }}</p>
        </div>
        <div class="step">
          <span class="step-num">4</span>
          <p>{{ t('install.macos.zip.step4') }}</p>
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
  flex-wrap: wrap;
}

.tabs button {
  font-family: var(--font-body);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 7px 16px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;
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
