import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { createI18n } from 'vue-i18n'
import FloatingVue from 'floating-vue'
import App from './App.vue'
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
  // the server), but the directive registration must exist.
  app.use(FloatingVue, {
    themes: {
      'key-tooltip': {
        $extend: 'tooltip',
        placement: 'top',
        triggers: ['hover', 'focus', 'touch'],
      },
    },
  })
  return renderToString(app)
}
