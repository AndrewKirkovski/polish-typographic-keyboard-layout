import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve, basename } from 'node:path'
import { readFileSync, existsSync, mkdirSync, copyFileSync } from 'node:fs'
import type { Plugin } from 'vite'

const ROOT = resolve(__dirname, '..')
const LAYOUT_FILES = ['polish_typographic.json', 'russian_typographic.json']

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
  }
}

export default defineConfig({
  plugins: [vue(), parentLayouts()],
  resolve: {
    alias: { '@': resolve(__dirname, 'src') },
  },
})
