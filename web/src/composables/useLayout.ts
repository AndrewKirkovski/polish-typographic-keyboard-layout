import { ref, computed } from 'vue'

export interface LayoutEntry {
  char: string
  name: string
  source: string
}

export interface LayoutData {
  name: string
  layers: {
    base: Record<string, string>
    shift: Record<string, string>
    altgr: Record<string, LayoutEntry | null>
    shift_altgr: Record<string, LayoutEntry | null>
  }
}

const DEAD_KEY_SYMBOLS: Record<string, string> = {
  'grave': '\u02CB',
  'acute': '\u00B4',
  'acute-2': '\u00B4',
  'circumflex': '\u02C6',
  'tilde': '\u02DC',
  'diaeresis': '\u00A8',
  'ring': '\u02DA',
  'cedilla': '\u00B8',
  'caron': '\u02C7',
  'breve': '\u02D8',
  'double-acute': '\u02DD',
}

export interface ParsedKey {
  display: string
  isDead: boolean
  name: string
  source: string
}

export function parseEntry(entry: LayoutEntry | null): ParsedKey | null {
  if (!entry || !entry.char) return null
  const ch = entry.char
  if (ch.startsWith('dk:') || ch.startsWith('act:')) {
    const dkName = ch.replace(/^(dk:|act:)/, '').trim()
    const symbol = DEAD_KEY_SYMBOLS[dkName] || dkName
    return { display: symbol, isDead: true, name: entry.name, source: entry.source }
  }
  return { display: ch, isDead: false, name: entry.name, source: entry.source }
}

const layouts = ref<Record<string, LayoutData>>({})
const activeId = ref('polish')
const loading = ref(false)

const LAYOUT_FILES: Record<string, string> = {
  polish: '/layouts/polish_typographic.json',
  russian: '/layouts/russian_typographic.json',
}

async function loadLayout(id: string) {
  if (layouts.value[id]) return
  loading.value = true
  try {
    const resp = await fetch(LAYOUT_FILES[id])
    if (!resp.ok) throw new Error(`Failed to load ${id}`)
    layouts.value[id] = await resp.json()
  } catch (e) {
    console.error('Failed to load layout:', e)
  } finally {
    loading.value = false
  }
}

export function useLayout() {
  const active = computed(() => layouts.value[activeId.value] || null)

  const setActive = async (id: string) => {
    await loadLayout(id)
    activeId.value = id
  }

  const init = async () => {
    await loadLayout('polish')
    await loadLayout('russian')
  }

  return { active, activeId, loading, setActive, init, layouts }
}
