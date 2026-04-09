/// <reference types="vite/client" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// Compile-time constant injected by vite.config.ts `define`. Sourced from
// the repo-root VERSION file so every UI string stays in lockstep.
declare const __APP_VERSION__: string
