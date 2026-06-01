# Pokémon Card Restock Bot (New Zealand)

Automated bot that monitors multiple NZ online retailers for Pokémon trading card game restocks and sends instant Discord alerts.

## Features

✅ **Multiple Store Monitoring**
- Shopify API integration (JSON): The Game Tree, TCG Collector NZ, Card Masters, WP Games, Animal Kingdoms, Bay Dragon, Otaku Mart, TCG NZ, Card Topia
- HTML scraping: Pokémon Center NZ, The Warehouse, Kmart

✅ **Smart Detection**
- Detects restocks (product goes from out-of-stock → in-stock)
- Detects new product listings
- Avoids duplicate alerts

✅ **Free Hosting**
- Runs on GitHub Actions (2,000 free minutes/month)
- Polls every 5 minutes
- State persisted in git

✅ **Discord Notifications**
- Rich embeds with product names and store links
- Instant alerts to your Discord channel

---

## Setup Instructions

### 1. Create Discord Webhook

1. Open your Discord server
2. Go to **Settings → Integrations → Webhooks**
3. Click **New Webhook**
4. Give it a name (e.g., "Pokemon Bot")
5. Copy the Webhook URL

### 2. Fork This Repository

Fork this repo to your GitHub account, then clone it locally:

```bash
git clone https://github.com/YOUR_USERNAME/pokemon-restock-bot.git
cd pokemon-restock-bot
```

### 3. Add Discord Webhook Secret

1. Go to your forked repo on GitHub
2. Navigate to **Settings → Secrets and variables → Actions**
3. Click **New repository secret**
4. Name: `DISCORD_WEBHOOK_URL`
5. Value: Paste your Discord webhook URL
6. Click **Add secret**

### 4. Enable GitHub Actions

1. Go to **Actions** tab in your repo
2. Click **I understand my workflows, go ahead and enable them**

### 5. Test the Bot

1. Go to **Actions** tab
2. Click **Pokémon Restock Bot**
3. Click **Run workflow**
4. Select **main** branch
5. Click **Run workflow**
6. Wait ~30 seconds and check your Discord channel

If it works, you'll see a message in Discord and the bot is ready!

---

## How It Works

The bot runs every 5 minutes:

1. **Fetch current stock** from all stores (Shopify JSON + HTML scraping)
2. **Compare to previous state** (stored in `pokemon_bot_state.json`)
3. **Detect changes** (restocks, new listings)
4. **Send Discord alerts** for any changes found
5. **Save new state** back to the repo

No expensive API calls, no external services needed.

---

## Customization

### Change Poll Interval

Edit `.github/workflows/pokemon_bot.yml`:

```yaml
- cron: '*/5 * * * *'  # Change 5 to desired minutes
```

Common options:
- `*/2 * * * *` = every 2 minutes
- `*/10 * * * *` = every 10 minutes
- `0 * * * *` = every hour

### Add/Remove Stores

Edit `pokemon_restock_bot.py`:

**Shopify stores:**
```python
SHOPIFY_STORES = {
    'Store Name': {
        'url': 'https://store.co.nz',
        'collection': 'pokemon',  # Collection slug from URL
    },
    # Add more...
}
```

**HTML scrape stores:**
```python
HTML_SCRAPE_STORES = {
    'Store Name': {
        'url': 'https://store.co.nz/pokemon',
        'product_selector': 'div.product',  # CSS selector for products
        'name_selector': 'a.name',           # CSS selector for product name
        'stock_selector': 'button.add-to-cart',
        'sold_out_class': 'disabled',
    },
    # Add more...
}
```

### Filter by Keywords

To only alert on specific products (e.g., "booster box" only), edit the alert logic in `check_store()`:

```python
if 'booster box' in product_name.lower():
    newly_restocked.append(product_name)
```

---

## Troubleshooting

### Bot not running
- Check **Actions** tab → **Pokémon Restock Bot** for error logs
- Ensure `DISCORD_WEBHOOK_URL` secret is set

### Discord alerts not arriving
- Test webhook: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`
- Check Discord channel permissions (bot should be able to post)

### False alerts / High noise
- The bot learns over time. First run will be noisy.
- After first successful run, only *actual* changes trigger alerts

### Store returns 0 products
- Check if the store URL is correct
- For Shopify: verify the collection slug in the URL
- For HTML stores: inspect the page and update CSS selectors

---

## What Gets Tracked

- **Pokémon TCG Booster Boxes**
- **Elite Trainer Boxes (ETBs)**
- **Theme Decks & Battle Decks**
- **Starter Collections**
- **Bulk products, sleeves, mats** (everything on the page)

---

## Performance

- **Execution time**: ~5-15 seconds per run
- **API calls**: ~10-15 requests total (all stores)
- **GitHub free tier**: 2,000 minutes/month = ~400 runs (every 5 min)
- **State file size**: <50KB

---

## Privacy & Safety

✅ No data stored externally
✅ No accounts required (except Discord, GitHub)
✅ Webhook URL is private (in GitHub Secrets)
✅ All code is open source

---

## License

MIT - Use freely, no credit required.

---

## Contributing

Found a store to add? Have ideas?

1. Fork the repo
2. Make changes
3. Test locally: `python pokemon_restock_bot.py`
4. Push and submit a pull request

---

## Questions?

Check the code comments in `pokemon_restock_bot.py` or open an issue on GitHub.

Happy collecting! 🎴✨
