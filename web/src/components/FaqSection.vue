<script setup lang="ts">
import { useI18n } from 'vue-i18n'
const { t, tm } = useI18n()

const items = tm('faq.items') as Array<{ q: string; a: string }>
</script>

<template>
  <section class="section faq-section">
    <div class="container">
      <h2 class="section-title">{{ t('faq.title') }}</h2>
      <dl class="faq-list">
        <div v-for="(item, i) in items" :key="i" class="faq-item">
          <dt>
            <details>
              <summary>{{ item.q }}</summary>
              <dd>{{ item.a }}</dd>
            </details>
          </dt>
        </div>
      </dl>
    </div>
  </section>
</template>

<style scoped>
.faq-list {
  max-width: 48rem;
  margin: 0 auto;
}

.faq-item {
  border-bottom: 1px solid var(--border);
}

.faq-item:first-child {
  border-top: 1px solid var(--border);
}

details {
  padding: 1rem 0;
}

summary {
  cursor: pointer;
  font-weight: 600;
  font-size: 1rem;
  line-height: 1.5;
  list-style: none;
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

summary::before {
  content: '+';
  font-family: var(--font-mono);
  font-weight: 400;
  font-size: 1.25rem;
  color: var(--text-muted);
  flex-shrink: 0;
  transition: transform 0.2s;
}

details[open] > summary::before {
  content: '\2212';
}

summary::-webkit-details-marker {
  display: none;
}

dd {
  margin: 0.5rem 0 0.5rem 2rem;
  color: var(--text-secondary, var(--text-muted));
  line-height: 1.6;
}
</style>
