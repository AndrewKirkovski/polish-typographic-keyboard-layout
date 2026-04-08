import { createApp } from 'vue'
import { createI18n } from 'vue-i18n'
import App from './App.vue'
import en from './i18n/en.json'
import pl from './i18n/pl.json'
import ru from './i18n/ru.json'
import './style.css'

const i18n = createI18n({
  legacy: false,
  locale: navigator.language.startsWith('pl') ? 'pl'
        : navigator.language.startsWith('ru') ? 'ru'
        : 'en',
  fallbackLocale: 'en',
  messages: { en, pl, ru },
})

const app = createApp(App)
app.use(i18n)
app.mount('#app')
