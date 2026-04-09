<script setup lang="ts">
import { useI18n } from 'vue-i18n'

const { t } = useI18n()
</script>

<template>
  <section class="why-section">
    <div class="container">
      <div class="why-grid">
        <div class="why-card">
          <h3 class="why-card-title">{{ t('why.windows.title') }}</h3>
          <p class="why-card-body">{{ t('why.windows.problem') }}</p>
          <ul class="why-list">
            <li>
              <i18n-t keypath="why.windows.case1" tag="span">
                <template #en><code>EN</code></template>
                <template #pl><code>PL</code></template>
              </i18n-t>
            </li>
            <li>
              <i18n-t keypath="why.windows.case2" tag="span">
                <template #en><code>EN</code></template>
                <template #pl><code>PL</code></template>
                <template #ru><code>RU</code></template>
              </i18n-t>
            </li>
          </ul>
          <p class="why-card-body why-card-body--solution">
            {{ t('why.windows.solution') }}
          </p>
        </div>
        <div class="why-card">
          <h3 class="why-card-title">{{ t('why.typography.title') }}</h3>
          <p class="why-card-body">{{ t('why.typography.lead') }}</p>
          <ul class="why-list">
            <li>
              <i18n-t keypath="why.typography.dimensions" tag="span">
                <template #good><code>30×20</code></template>
                <template #bad><code>30x20</code></template>
              </i18n-t>
            </li>
            <li>
              <i18n-t keypath="why.typography.dashes" tag="span">
                <template #good><code>—</code></template>
                <template #bad><code>--</code></template>
              </i18n-t>
            </li>
            <li>
              <i18n-t keypath="why.typography.quotes" tag="span">
                <template #good><code>{{ t('why.typography.quotesGood') }}</code></template>
                <template #bad><code>{{ t('why.typography.quotesBad') }}</code></template>
              </i18n-t>
            </li>
            <li>{{ t('why.typography.symbols') }}</li>
          </ul>
          <p class="why-card-body why-card-body--note">{{ t('why.typography.note') }}</p>
        </div>
      </div>
    </div>
  </section>
</template>

<style scoped>
/* Pulled in close to the keyboard preview above so the rationale reads as
   a continuation, not a separate marketing block. No card chrome — these
   are just two short prose blocks side-by-side on desktop, stacked on
   mobile. */
.why-section {
  padding: 1.5rem 0 1rem;
}

.why-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2.5rem;
}

.why-card-title {
  font-family: var(--font-body);
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--color-altgr);
  margin: 0 0 0.6rem;
}

.why-card-body {
  font-size: 0.95rem;
  line-height: 1.55;
  color: var(--text-secondary);
}

.why-card-body + .why-list {
  margin-top: 0.6rem;
}

.why-list {
  list-style: none;
  padding: 0;
  margin: 0 0 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.why-list li {
  position: relative;
  padding-left: 1.1rem;
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--text-secondary);
}

.why-list li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0.6em;
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--color-altgr);
}

.why-card-body--solution {
  margin-top: 0.5rem;
  color: var(--text);
  /* No bold — the line is already visually distinct via text colour
     bump from --text-secondary to --text and the spacing above. */
}

.why-card-body--note {
  margin-top: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.why-card-body code,
.why-list code {
  font-family: var(--font-mono);
  font-size: 0.85em;
  background: var(--bg-subtle);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1px 6px;
  color: var(--text);
  white-space: nowrap;
}

@media (max-width: 720px) {
  .why-section {
    padding: 1rem 0 0.5rem;
  }
  .why-grid {
    grid-template-columns: 1fr;
    gap: 1.75rem;
  }
}
</style>
