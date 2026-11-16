# Deployment verification checklist

Use this checklist after updating the public market dashboard at `finance.laoxu.org`.

## GitHub Pages

- Confirm GitHub Pages is configured to publish from the intended `main` branch and root folder.
- Check the latest deployment status in GitHub Actions / Pages.
- Confirm that the repository's `CNAME` matches `finance.laoxu.org`.
- Confirm that DNS resolves the subdomain to the intended GitHub Pages endpoint and HTTPS is available.

## Functional checks

- Open the site in a desktop browser and on a narrow mobile viewport.
- Check that all six market widgets render without mock data: USD/CNY, NASDAQ-100, S&P 500, spot gold, BTC/USD, and Shanghai Composite.
- Confirm that weekly chart views and responsive layout behave as intended.
- Verify that no private portfolio, credentials, account numbers, or API tokens were committed.
- Check browser console errors and third-party widget blocking before assuming a site-code failure.

## Rollback

If a deployment causes a regression, inspect the relevant commit and revert the problematic change through a new pull request. Do not publish credentials in issue reports or screenshots.
