// Single source of truth for floating-vue's app.use() options.
//
// Both the client entrypoint (`main.ts`) and the SSR entrypoint
// (`entry-server.ts`) need to call `app.use(FloatingVue, ...)` with the
// same options — without this shared module they were duplicating the
// `themes['key-tooltip']` config and could drift if one was edited and
// not the other.
//
// `FloatingVue.install`'s options type isn't exported by floating-vue, so
// we declare it as a loose object. The keys we touch are stable in
// floating-vue 5.x.
export const FLOATING_VUE_OPTIONS = {
  themes: {
    'key-tooltip': {
      $extend: 'tooltip',
      // Default placement is `top`. Floating UI's `flip` + `shift` middleware
      // (enabled by default in floating-vue) keep the popper onscreen on
      // narrow mobile viewports.
      placement: 'top',
      // 'touch' lets the keycap show its tooltip on a tap as well as on
      // hover/focus — the keycap isn't a button itself, so we lean on
      // floating-vue's pointer-event handling.
      triggers: ['hover', 'focus', 'touch'],
    },
  },
}
