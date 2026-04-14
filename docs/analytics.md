# Analytics — Counterscale on Cloudflare

The web app ships with [Counterscale](https://github.com/benvinegar/counterscale)
analytics — a self-hosted, Cloudflare-native tracker + dashboard that runs on
Workers and stores data in Analytics Engine. **Zero cost** within Cloudflare's
free tier, **no cookie banner** needed (no persistent client ID), **no data
leaves your Cloudflare account**.

## How it's wired in the app

- **Package**: `@counterscale/tracker` (direct npm dep in `web/`)
- **Composable**: `web/src/composables/useAnalytics.ts` — wraps `init()` and
  `trackPageview()`, exposes typed helpers (`trackDownload`, `trackLayerSwitch`,
  `trackVariantSwitch`, `trackLocaleSwitch`, `trackFontTab`, `trackScrollDepth`)
- **Bootstrap**: `main.ts` calls `initAnalytics()` once after `app.mount()`. If
  `VITE_COUNTERSCALE_URL` is unset, every track call is a no-op — the app runs
  clean without analytics during local dev and before the Worker is deployed.

### Event taxonomy

Counterscale's tracker API only exposes `trackPageview()`, so custom events are
synthesised as virtual pageviews under the `/__e/<event-name>` path with props
encoded in the query string. Filter by `path LIKE '/__e/%'` in the dashboard to
see them separately from real pageviews.

| Event | Path | Props |
|---|---|---|
| Real pageview | `/`, `/pl/`, `/ru/`, `#keyboard`, etc. | — |
| Download | `/__e/download` | `category` (windows/macos/pdf/font), `file`, `variant?` |
| Layer switch | `/__e/layer-switch` | `layer` (auto/base/altgr/shift_altgr) |
| Variant switch | `/__e/variant-switch` | `variant` (polish/russian) |
| Locale switch | `/__e/locale-switch` | `from`, `to` |
| Font demo tab | `/__e/font-tab` | `tab` (cyrillic/ipa) |
| Scroll depth | `/__e/scroll-depth` | `percent` (25/50/75/100) |

## One-time setup (do this once)

### 1. Deploy the Counterscale Worker

Runs interactively and authenticates against Cloudflare via browser.

```bash
npx @counterscale/cli@latest install
```

Follow the prompts. It will:

1. Enable Cloudflare Analytics Engine on your account
2. Create an API token with `Account.Workers.Edit` + `Account.Analytics.Edit`
3. Deploy the dashboard Worker to `<subdomain>.workers.dev`
4. Ask you to pick a **site ID** — use `polish-typographic-keyboard-layout`
   (matches the default in `useAnalytics.ts`) or pick your own and set
   `VITE_COUNTERSCALE_SITE_ID` below

Write down the two things it emits:

- **Deployment URL** — something like `https://counterscale-xyz.workers.dev/`
- **Site ID** — whatever you chose

### 2. Wire env vars in Cloudflare Pages

In the CF dashboard → **Pages** → this project → **Settings** → **Environment
Variables**, add for **both Production and Preview**:

```
VITE_COUNTERSCALE_URL=https://<your-subdomain>.workers.dev/
VITE_COUNTERSCALE_SITE_ID=polish-typographic-keyboard-layout   # optional, if non-default
```

Trigger a redeploy. The build inlines these at compile time (Vite's
`VITE_` prefix), so the tracker starts running on next deploy.

### 3. Protect the dashboard with Cloudflare Access

This is the critical step — without it, anyone with the Worker URL can see
your traffic.

1. CF dashboard → **Zero Trust** → **Access** → **Applications** →
   **Add an application** → **Self-hosted**
2. **Application name**: `Counterscale Dashboard`
3. **Session duration**: 24 hours (or whatever you prefer)
4. **Application domain**: the Worker's hostname — e.g.
   `counterscale-xyz.workers.dev`. You can optionally use a subdomain of a
   zone you own (e.g. `stats.example.com`) if you've set up a custom domain
   for the Worker.
5. **Path**: leave blank (protect the whole dashboard)
6. Click **Next** → **Policies** → **Add a policy**:
   - **Policy name**: `Me only`
   - **Action**: `Allow`
   - **Include** → **Emails** → your email address
   - (Optional) add a GitHub or Google identity provider first under
     Settings → Authentication if you want SSO instead of email-OTP
7. **Next** → **Save**

Within ~1 minute, visiting the dashboard URL will redirect you to a CF Access
login page. Cloudflare's free tier covers up to 50 users.

**Important:** the tracker's `/collect` endpoint (the one the browser beacons
to) also lives on the same Worker. Make sure your Access policy **exempts the
collect path** — otherwise real visitors will be blocked by the login redirect
and no data will come in. Under the Access application's **Policies** tab,
add a `Bypass` rule matching the collect path (usually `/collect`), with
"Everyone" as the source. Counterscale's docs should confirm the exact path.

## Verification

After deploy:

1. Visit your live site in an incognito window
2. DevTools → Network → filter `collect` — you should see a POST to
   `<your-worker>/collect` with `sid=polish-typographic-keyboard-layout`
3. Click a download button — another beacon fires with
   `p=/__e/download&category=windows&file=...`
4. Open `https://<your-worker>.workers.dev/` → authenticate via CF Access →
   see the pageview land within ~1 minute

## Cost ceiling

- **CF Workers free tier**: 100k requests/day — plenty for this traffic level
- **CF Analytics Engine free tier**: 10M events/month write, 90-day retention
- **CF Access free tier**: up to 50 users
- **R2 long-term archive** (optional): ~$0.015/GB/month if you enable
  Counterscale's archive feature to keep data past 90 days

For a typography keyboard site, this should stay at $0/month indefinitely.

## Swapping analytics backends later

The composable is the only place Counterscale is imported. To switch to
Umami / Plausible / PostHog later, reimplement `initAnalytics`, `trackEvent`,
and `trackPageview` against the new SDK. All call sites across the Vue app
use the wrapper functions, not Counterscale directly.
