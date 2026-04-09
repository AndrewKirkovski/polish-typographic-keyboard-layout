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

// floating-vue v5 hardcodes `tabindex="0"` on every popper element so
// "interactive" tooltips (with clickable content inside) can be reached
// by keyboard. Our keycap tooltips are read-only and we don't want them
// in the tab order — the popper appearing in the focus chain after the
// trigger key causes a focus race that makes Tab navigation flash the
// tooltip in and out. There's no theme option to disable this in v5, so
// we strip the attribute as poppers are added to <body>.
const popperTabindexStripper = new MutationObserver((mutations) => {
  for (const m of mutations) {
    for (const node of m.addedNodes) {
      if (node.nodeType !== 1) continue
      const el = node as HTMLElement
      if (el.classList?.contains('v-popper__popper')) {
        el.removeAttribute('tabindex')
      }
      // Also handle deeper insertions where the popper isn't the direct
      // added node (defensive — floating-vue currently appends directly
      // to body, but this future-proofs against teleport-target changes).
      el.querySelectorAll?.('.v-popper__popper[tabindex]').forEach((p) => {
        p.removeAttribute('tabindex')
      })
    }
  }
})
popperTabindexStripper.observe(document.body, {
  childList: true,
  subtree: true,
})
