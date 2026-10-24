"""
Pokémon Card Restock Bot for New Zealand
Monitors multiple retailers for stock changes and alerts via Discord webhook.
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from urllib.parse import urljoin
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ CONFIGURATION ============

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL', '')

# Shopify stores - use JSON API
SHOPIFY_STORES = {
    'The Game Tree': {
        'url': 'https://thegametree.co.nz',
        'collection': 'pokemon-products',
    },
    'TCG Collector NZ': {
        'url': 'https://tcgcollectornz.com',
        'collection': 'pokemon-tcg-collector-nz',
    },
    'Card Masters': {
        'url': 'https://cardmasters.co.nz',
        'collection': 'pokemon-booster-boxes-etbs',
    },
    'WP Games': {
        'url': 'https://wpgames.co.nz',
        'collection': 'latest-pokemon-sets',
    },
    'Animal Kingdoms': {
        'url': 'https://animalkingdoms.co.nz',
        'collection': 'pokemon-tcg',
    },
    'Bay Dragon': {
        'url': 'https://www.baydragon.co.nz',
        'collection': 'pokemon',
    },
    'Otaku Mart': {
        'url': 'https://otakumart.co.nz',
        'collection': 'pokemon-tcg',
    },
    'TCG NZ': {
        'url': 'https://www.tcgnz.co.nz',
        'collection': 'pokemon',
    },
    'Card Topia': {
        'url': 'https://www.cardtopia.co.nz',
        'collection': 'pokemon',
    },
}

# Non-Shopify stores - HTML scraping
HTML_SCRAPE_STORES = {
    'Pokémon Center NZ': {
        'url': 'https://www.pokemoncenter.com/en-nz/category/trading-card-game',
        'product_selector': 'div[data-product-id]',
        'name_selector': 'a.product-title',
        'stock_selector': 'button.add-to-cart',
        'sold_out_class': 'disabled',
    },
    'The Warehouse': {
        'url': 'https://www.thewarehouse.co.nz/c/official-merchandise/pok%C3%A9mon/pokemon-trading-cards',
        'product_selector': 'div.productCard',
        'name_selector': 'a.productCardTitle',
        'stock_indicator': 'span.productCardPrice',
    },
    'Kmart': {
        'url': 'https://www.kmart.co.nz/category/toys/pokemon-trading-cards/',
        'product_selector': 'div.product-item',
        'name_selector': 'span.product-title',
        'stock_indicator': 'span.availability',
    },
}

STATE_FILE = 'pokemon_bot_state.json'
TIMEOUT = 10  # seconds
REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ============ MAIN FUNCTIONS ============

def load_state() -> Dict:
    """Load previous state from file."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load state: {e}")
    return {}


def save_state(state: Dict) -> None:
    """Save current state to file."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save state: {e}")


def send_discord_alert(message: str, embed_data: Optional[Dict] = None) -> bool:
    """Send alert to Discord webhook."""
    if not DISCORD_WEBHOOK_URL:
        logger.warning("Discord webhook URL not set")
        return False
    
    try:
        payload = {
            'content': message,
            'username': '🎴 Pokémon Restock Bot'
        }
        
        if embed_data:
            payload['embeds'] = [embed_data]
        
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            json=payload,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        logger.info(f"Discord alert sent: {message[:50]}")
        return True
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {e}")
        return False


def fetch_shopify_products(store_name: str, store_config: Dict) -> Dict[str, bool]:
    """Fetch products from Shopify store using JSON API."""
    try:
        url = f"{store_config['url']}/collections/{store_config['collection']}/products.json?limit=250"
        response = requests.get(url, headers=REQUEST_HEADERS, timeout=TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        products = {}
        
        for product in data.get('products', []):
            product_title = product['title']
            # A product is "in stock" if any variant has available: true
            in_stock = any(v.get('available', False) for v in product.get('variants', []))
            products[product_title] = in_stock
        
        logger.info(f"{store_name}: Fetched {len(products)} products")
        return products
    
    except Exception as e:
        logger.error(f"Error fetching {store_name}: {e}")
        return {}


def fetch_html_products(store_name: str, store_config: Dict) -> Dict[str, bool]:
    """Fetch products from HTML-based store using BeautifulSoup."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        logger.warning("BeautifulSoup not installed, skipping HTML scrape stores")
        return {}
    
    try:
        response = requests.get(
            store_config['url'],
            headers=REQUEST_HEADERS,
            timeout=TIMEOUT
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        products = {}
        product_elements = soup.select(store_config.get('product_selector', 'div'))
        
        for elem in product_elements:
            try:
                name_elem = elem.select_one(store_config.get('name_selector', 'a'))
                if not name_elem:
                    continue
                
                product_name = name_elem.get_text(strip=True)
                
                # Check if product is in stock
                stock_button = elem.select_one(store_config.get('stock_selector', 'button'))
                in_stock = True
                
                if stock_button:
                    # If button has 'disabled' class or contains "sold out" text, it's out of stock
                    is_disabled = 'disabled' in stock_button.get('class', [])
                    has_soldout_text = 'sold out' in stock_button.get_text(strip=True).lower()
                    in_stock = not (is_disabled or has_soldout_text)
                
                products[product_name] = in_stock
            except Exception as e:
                logger.debug(f"Error parsing product in {store_name}: {e}")
                continue
        
        logger.info(f"{store_name}: Fetched {len(products)} products")
        return products
    
    except Exception as e:
        logger.error(f"Error scraping {store_name}: {e}")
        return {}



def check_store(store_name: str, store_config: Dict, previous_state: Dict) -> Tuple[Dict[str, bool], List[str]]:
    """Check a store for restocks and new products."""

    if 'collection' in store_config:
        current_products = fetch_shopify_products(store_name, store_config)
    else:
        current_products = fetch_html_products(store_name, store_config)

    if not current_products:
        logger.warning(f"No products found for {store_name}")
        return {}, []

    store_state_key = f"{store_name}_products"
    previous_products = previous_state.get(store_state_key)

    if previous_products is None:
        logger.info(f"{store_name}: Initial baseline saved; no alerts for existing products.")
        return current_products, []

    newly_restocked = []

    for product_name, is_in_stock in current_products.items():
        name_lower = product_name.lower()
                sealed_keywords = [
            "booster pack",
            "booster box",
            "booster bundle",
            "booster display",
            "elite trainer box",
            "pokemon center etb",
            " etb",
            "pokemon tin",
            " tin",
            "collection box",
            "premium collection",
            "ultra premium collection",
            "build & battle box",
            "build and battle box",
            "battle academy",
            "blister pack",
            "three-pack blister",
            "3-pack blister",
            "sleeved booster",
            "special collection",
            "trainer toolkit",
            "ascended heroes",
            "30th celebrations",
            "30th",
            "delta reign",
        ]
        if not any(word in name_lower for word in sealed_keywords):
            continue
        if not is_in_stock:
            continue

        if product_name not in previous_products:
            newly_restocked.append(product_name)
            logger.info(f"🆕 NEW PRODUCT: {store_name} - {product_name}")
        elif not previous_products[product_name]:
            newly_restocked.append(product_name)
            logger.info(f"✅ RESTOCK: {store_name} - {product_name}")

    return current_products, newly_restocked


    

def main():
    """Main execution function."""
    logger.info("=" * 60)
    logger.info(f"Starting Pokémon Restock Bot - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Load previous state
    previous_state = load_state()
    new_state = {}
    all_restocks = []
    
    # Check Shopify stores
    logger.info("\n--- Checking Shopify Stores ---")
    for store_name, store_config in SHOPIFY_STORES.items():
        current_products, restocks = check_store(store_name, store_config, previous_state)
        new_state[f"{store_name}_products"] = current_products
        
        if restocks:
            for product in restocks:
                all_restocks.append((store_name, product, store_config['url']))
    
    # Check HTML scrape stores
    logger.info("\n--- Checking HTML Stores ---")
    for store_name, store_config in HTML_SCRAPE_STORES.items():
        current_products, restocks = check_store(store_name, store_config, previous_state)
        new_state[f"{store_name}_products"] = current_products
        
        if restocks:
            for product in restocks:
                all_restocks.append((store_name, product, store_config['url']))
    
    # Send Discord alerts for all restocks
    if all_restocks:
        logger.info(f"\n🔔 Found {len(all_restocks)} restock(s)!")
        
        # Send individual alerts for each restock
        for store_name, product_name, store_url in all_restocks:
            embed = {
                'title': '🎴 Pokémon Cards In Stock!',
                'description': f'**{product_name}** just restocked at **{store_name}**',
                'url': store_url,
                'color': 3447003,  # Blue
                'footer': {
                    'text': 'Pokémon Restock Bot',
                    'icon_url': 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/25.png'
                },
                'timestamp': datetime.utcnow().isoformat()
            }
            send_discord_alert(
                f'🎴 **POKÉMON RESTOCK** - {product_name} at {store_name}',
                embed
            )
    else:
        logger.info("\n✅ No restocks detected")
    
    # Save new state
    save_state(new_state)
    logger.info(f"\nState saved to {STATE_FILE}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
