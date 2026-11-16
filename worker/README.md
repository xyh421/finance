# Cloudflare Worker — public quotes

Deploy with Cloudflare dashboard (Workers & Pages → Create Worker → import GitHub repository) or locally:

```sh
cd worker
npx wrangler deploy
```

Endpoint: `https://laoxu-finance-quotes.<your-subdomain>.workers.dev/api/quotes`

For the website, assign a custom domain **quotes.laoxu.org** to this Worker under Workers & Pages → Settings → Domains & Routes. The frontend will use `https://quotes.laoxu.org/api/quotes` and fall back to GitHub-hosted static JSON when unavailable.

No secrets required. This is a best-effort unofficial Yahoo Finance proxy, not exchange-authorized live data. Quotes may be delayed or blocked. Cloudflare edge caching is 120 seconds per region, not a guaranteed global refresh schedule.
