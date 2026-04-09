import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { createI18n } from 'vue-i18n'
import FloatingVue from 'floating-vue'
import App from './App.vue'
import { FLOATING_VUE_OPTIONS } from './floating-vue-options'
import en from './i18n/en.json'
import pl from './i18n/pl.json'
import ru from './i18n/ru.json'

export async function render(locale: string): Promise<string> {
  const i18n = createI18n({
    legacy: false,
    locale,
    fallbackLocale: 'en',
    messages: { en, pl, ru },
  })

  const app = createSSRApp(App)
  app.use(i18n)
  // floating-vue must be installed in the SSR app too, otherwise the
  // v-tooltip directive on KeyCap.vue throws "Failed to resolve directive"
  // during prerender. SSR doesn't render any tooltip content (no hover on
  // the server), but the directive registration must exist. Options are
  // shared with main.ts via floating-vue-options to prevent drift.
  app.use(FloatingVue, FLOATING_VUE_OPTIONS)
  return renderToString(app)
}
