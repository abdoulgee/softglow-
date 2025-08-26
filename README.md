# SoftGlow on Vercel (Flask)

## Quick start

```bash
# 1) Install Vercel CLI (requires Node.js 18+)
npm i -g vercel

# 2) From this folder, link & deploy
vercel       # creates a preview URL
vercel --prod  # deploys to production
```

## Environment variables (Vercel Dashboard or CLI)

- `SECRET_KEY`
- `PAYPAL_CLIENT_ID`
- `PAYPAL_SECRET`
- `STRIPE_PUBLIC_KEY` (if you use Stripe)
- `STRIPE_SECRET_KEY` (if you use Stripe)

CLI examples:

```bash
vercel env add SECRET_KEY production
vercel env add PAYPAL_CLIENT_ID production
vercel env add PAYPAL_SECRET production
# and so on... (repeat for "preview" and "development" as needed)
```

## Local dev with Vercel

```bash
vercel dev
```

This runs the same serverless entrypoint as production (`api/index.py`).