import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import en from './i18n/en.json'
import pl from './i18n/pl.json'
import ru from './i18n/ru.json'
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
app.mount('#app')
