import { ref, onMounted, onUnmounted } from 'vue'

type Theme = 'light' | 'dark'

const theme = ref<Theme>('light')

let mql: MediaQueryList | null = null
const handler = (e: MediaQueryListEvent) => {
  theme.value = e.matches ? 'dark' : 'light'
}

export function useTheme() {
  onMounted(() => {
    mql = window.matchMedia('(prefers-color-scheme: dark)')
    theme.value = mql.matches ? 'dark' : 'light'
    mql.addEventListener('change', handler)
  })

  onUnmounted(() => {
    mql?.removeEventListener('change', handler)
  })

  return { theme }
}
