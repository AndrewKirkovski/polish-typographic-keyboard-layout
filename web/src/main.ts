import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import FloatingVue from 'floating-vue'
import App from './App.vue'
import { FLOATING_VUE_OPTIONS } from './floating-vue-options'
import en from './i18n/en.json'
import pl from './i18n/pl.json'
import ru from './i18n/ru.json'
// floating-vue base styles MUST load before our app stylesheet so our
// `.v-popper--theme-key-tooltip` overrides actually win on source-order
// (specificity is identical between their `.v-popper--theme-tooltip` and
// our extended class because the popper element gets BOTH theme classes).
import 'floating-vue/dist/style.css'
import './style.css'

function detectLocale(): string {
  const path = window.location.pathname
  if (path.startsWith('/pl')) return 'pl'
  if (path.startsWith('/ru')) return 'ru'
  return 'en'
}

const i18n = createI18n({
  legacy: false,
  locale: detectLocale(),
  fallbackLocale: 'en',
  messages: { en, pl, ru },
})

const app = createApp(App)
app.use(i18n)
// floating-vue exposes <VTooltip>, <VDropdown>, and the v-tooltip directive.
// Options are shared with entry-server.ts via floating-vue-options so the
// SSR and client renders can never drift on tooltip config.
app.use(FloatingVue, FLOATING_VUE_OPTIONS)
app.mount('#app')
