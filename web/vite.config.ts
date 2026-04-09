import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve, basename } from 'node:path'
import { readFileSync, existsSync, mkdirSync, copyFileSync } from 'node:fs'
import type { Plugin } from 'vite'

const ROOT = resolve(__dirname, '..')
const LAYOUT_FILES = ['polish_typographic.json', 'russian_typographic.json']

// Read project version once at config-load time (cheap, file is tiny).
// Single source of truth lives at <repo-root>/VERSION; index.html and the
// schema.org JSON-LD pick it up via the %VERSION% placeholder below, and
// the Vue components consume the same value via __APP_VERSION__.
const APP_VERSION: string = readFileSync(resolve(ROOT, 'VERSION'), 'utf-8').trim()

// Serve layout JSON files from project root in dev, copy them for production build
function parentLayouts(): Plugin {
  return {
    name: 'parent-layouts',

    // Dev: serve from parent directory via middleware
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (req.url?.startsWith('/layouts/')) {
          const name = basename(req.url)
          const file = resolve(ROOT, name)
          if (LAYOUT_FILES.includes(name) && existsSync(file)) {
            res.setHeader('Content-Type', 'application/json')
            res.end(readFileSync(file, 'utf-8'))
            return
          }
        }
        next()
      })
    },

    // Build: copy layout JSONs into public/layouts/ before build
    buildStart() {
      const outDir = resolve(__dirname, 'public', 'layouts')
      mkdirSync(outDir, { recursive: true })
      for (const name of LAYOUT_FILES) {
        const src = resolve(ROOT, name)
        if (existsSync(src)) {
          copyFileSync(src, resolve(outDir, name))
        }
      }
    },

    // Inject the project version into index.html (replaces %VERSION% in
    // schema.org softwareVersion etc). Runs in dev and build. Reuses the
    // value read at config-load time — no per-transform disk I/O.
    transformIndexHtml(html) {
      return html.replace(/%VERSION%/g, APP_VERSION)
    },
  }
}

export default defineConfig({
  // Inject the project version as a compile-time constant. Vue components
  // and the prerender script reference this via __APP_VERSION__ so a single
  // bump of /VERSION propagates through every URL, label, and download link.
  define: {
    __APP_VERSION__: JSON.stringify(APP_VERSION),
  },
  plugins: [
    vue({
      // iconify-icon is a custom element registered globally by the
      // @iconify/iconify-icon CDN script in index.html. Tell Vue's compiler
      // about it so SSR doesn't warn "Component <Anonymous> is missing
      // template or render function" for every iconify-icon usage.
      template: {
        compilerOptions: {
          isCustomElement: (tag) => tag === 'iconify-icon',
        },
      },
    }),
    parentLayouts(),
  ],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
})
