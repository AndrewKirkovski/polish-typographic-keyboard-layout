/**
 * Cloudflare Pages Functions middleware.
 *
 * Permanently redirects the built-in `polish-typographic-keyboard-layout.pages.dev`
 * subdomain to the canonical `polish-typographic.com` custom domain. CF Pages
 * does not expose an API to disable the default `.pages.dev` URL on a project
 * that has a custom domain attached, so we intercept it at the Functions layer.
 *
 * Everything else passes through to the static assets.
 */
export async function onRequest(context) {
  const url = new URL(context.request.url)

  if (url.hostname === 'polish-typographic-keyboard-layout.pages.dev') {
    const target = new URL(url.pathname + url.search + url.hash, 'https://polish-typographic.com')
    return Response.redirect(target.toString(), 301)
  }

  return context.next()
}
