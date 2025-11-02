import requests
import time
import threading
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Bot Configuration
BOT_TOKEN = "8475597778:AAE2OJApdoNOGYsBabaiJt_KsdUMefXXs5o"
GROUP_ID = -5014023488
CONTRACT_ADDRESS = "2zMMhcVQEXDtdE6vsFS7S7D5oUodfJHE8vd1gnBouauv"
BUY_URL = "https://pengu.pudgypenguins.com/"

class TelegramBot:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{BOT_TOKEN}"
        self.last_update_id = 0
        
    def send_message(self, chat_id, text, reply_markup=None, reply_to_message_id=None):
        """Send message to Telegram chat"""
        url = f"{self.base_url}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
            
        if reply_to_message_id:
            payload['reply_to_message_id'] = reply_to_message_id
            
        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return None
    
    def edit_message(self, chat_id, message_id, text, reply_markup=None):
        """Edit existing message"""
        url = f"{self.base_url}/editMessageText"
        payload = {
            'chat_id': chat_id,
            'message_id': message_id,
            'text': text,
            'parse_mode': 'Markdown',
            'disable_web_page_preview': True
        }
        
        if reply_markup:
            payload['reply_markup'] = reply_markup
            
        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.json()
        except Exception as e:
            logger.error(f"Error editing message: {e}")
            return None
    
    def get_updates(self):
        """Get new updates from Telegram"""
        url = f"{self.base_url}/getUpdates"
        payload = {
            'offset': self.last_update_id + 1,
            'timeout': 10
        }
        
        try:
            response = requests.post(url, json=payload, timeout=15)
            data = response.json()
            
            if data.get('ok'):
                return data['result']
            return []
        except Exception as e:
            logger.error(f"Error getting updates: {e}")
            return []
    
    def answer_callback_query(self, callback_query_id):
        """Answer callback query"""
        url = f"{self.base_url}/answerCallbackQuery"
        payload = {
            'callback_query_id': callback_query_id
        }
        
        try:
            requests.post(url, json=payload, timeout=3)
        except Exception as e:
            logger.error(f"Error answering callback: {e}")

class PudgyPenguinsBot:
    def __init__(self):
        self.coingecko_url = "https://api.coingecko.com/api/v3/coins/pudgy-penguins"
        self.telegram_bot = TelegramBot()
        self.price_cache = None
        self.cache_time = 0
        self.cache_duration = 30
        self.bot_username = None
        
    def get_bot_info(self):
        """Get bot username"""
        if self.bot_username is None:
            try:
                url = f"{self.telegram_bot.base_url}/getMe"
                response = requests.get(url, timeout=5)
                data = response.json()
                if data.get('ok'):
                    self.bot_username = data['result']['username']
                    logger.info(f"🤖 Bot username: @{self.bot_username}")
            except Exception as e:
                logger.error(f"Error getting bot info: {e}")
        return self.bot_username
        
    def get_price_data(self):
        """Fetch real-time price data from CoinGecko API with caching"""
        current_time = time.time()
        if self.price_cache and (current_time - self.cache_time) < self.cache_duration:
            return self.price_cache
            
        try:
            response = requests.get(self.coingecko_url, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            market_data = data.get('market_data', {})
            
            price_usd = market_data.get('current_price', {}).get('usd', 0)
            market_cap = market_data.get('market_cap', {}).get('usd', 0)
            fully_diluted_valuation = market_data.get('fully_diluted_valuation', {}).get('usd', 0)
            trading_volume = market_data.get('total_volume', {}).get('usd', 0)
            circulating_supply = market_data.get('circulating_supply', 0)
            total_supply = market_data.get('total_supply', 0)
            max_supply = market_data.get('max_supply', 0)
            price_change_24h = market_data.get('price_change_percentage_24h', 0)
            
            price_data = {
                'price_usd': price_usd,
                'market_cap': market_cap,
                'fully_diluted_valuation': fully_diluted_valuation,
                'trading_volume': trading_volume,
                'circulating_supply': circulating_supply,
                'total_supply': total_supply,
                'max_supply': max_supply,
                'price_change_24h': price_change_24h,
                'last_updated': data.get('last_updated', '')
            }
            
            self.price_cache = price_data
            self.cache_time = current_time
            
            return price_data
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None
    
    def format_number(self, num):
        """Format large numbers to readable format"""
        if num is None:
            return "N/A"
        
        try:
            num = float(num)
            if num >= 1_000_000_000:
                return f"${num/1_000_000_000:.2f}B"
            elif num >= 1_000_000:
                return f"${num/1_000_000:.2f}M"
            elif num >= 1_000:
                return f"${num/1_000:.2f}K"
            else:
                return f"${num:.2f}"
        except (TypeError, ValueError):
            return "N/A"
    
    def format_supply(self, num):
        """Format supply numbers"""
        if num is None:
            return "N/A"
        
        try:
            num = float(num)
            if num >= 1_000_000:
                return f"{num/1_000_000:.2f}M"
            else:
                return f"{num:,.0f}"
        except (TypeError, ValueError):
            return "N/A"
    
    def get_price_change_emoji(self, change):
        """Get emoji based on price change"""
        if change is None:
            return "🟢"
        try:
            change = float(change)
            if change > 0:
                return "🟢"
            elif change < 0:
                return "🔴"
            else:
                return "🟢"
        except (TypeError, ValueError):
            return "🟢"
    
    def create_price_message(self, data):
        """Create formatted price message"""
        if not data:
            return "❌ Unable to fetch price data at the moment. Please try again later."
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        change_emoji = self.get_price_change_emoji(data.get('price_change_24h'))
        price_change = data.get('price_change_24h', 0)
        
        message = f"""
🐧 **PUDGY PENGUINS | REAL-TIME MARKET DATA** 🐧

{change_emoji} **Price**: `${data['price_usd']:,.4f}`
📊 **24h Change**: `{price_change:+.2f}%`

**MARKET METRICS**
• **Market Cap**: `{self.format_number(data['market_cap'])}`
• **FDV**: `{self.format_number(data['fully_diluted_valuation'])}`
• **24h Volume**: `{self.format_number(data['trading_volume'])}`

**SUPPLY DATA**
• **Circulating**: `{self.format_supply(data['circulating_supply'])}`
• **Total Supply**: `{self.format_supply(data['total_supply'])}`
• **Max Supply**: `{self.format_supply(data['max_supply']) if data['max_supply'] else 'N/A'}`

**CONTRACT & LINKS**
• **CA**: `{CONTRACT_ADDRESS}`
• **Trade**: [Pengu Marketplace]({BUY_URL})

⏰ *Last Updated: {timestamp}*
        """.strip()
        
        return message
    
    def create_ca_message(self):
        """Create contract address message"""
        message = f"""
📋 **PUDGY PENGUINS CONTRACT ADDRESS**

`{CONTRACT_ADDRESS}`

*Copy and use this address for trading on DEXs*
        """.strip()
        return message
    
    def create_keyboard(self):
        """Create inline keyboard with only refresh button"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 Refresh Price", "callback_data": "refresh"}]
            ]
        }
        return keyboard
    
    def send_price_response(self, chat_id, reply_to_message_id=None):
        """Send price response quickly"""
        data = self.get_price_data()
        message = self.create_price_message(data)
        keyboard = self.create_keyboard()
        self.telegram_bot.send_message(chat_id, message, keyboard, reply_to_message_id=reply_to_message_id)
    
    def send_ca_response(self, chat_id, reply_to_message_id=None):
        """Send CA response quickly"""
        message = self.create_ca_message()
        self.telegram_bot.send_message(chat_id, message, reply_to_message_id=reply_to_message_id)
    
    def is_price_command(self, text_lower):
        """Check if text is a price command (including typos)"""
        price_commands = [
            'price', 'pricee', 'pricce', 'priice', 'prie', 'prce',
            'p', 'pp', 'pr', 'pri', 'pric'
        ]
        return text_lower in price_commands
    
    def is_ca_command(self, text_lower):
        """Check if text is a CA command (including typos)"""
        ca_commands = [
            'ca', 'caa', 'cca', 'caaa', 'c', 'cc',
            'contract', 'contrac', 'contrat', 'contrakt',
            'address', 'adress', 'addres', 'adres'
        ]
        return text_lower in ca_commands
    
    def process_message(self, message):
        """Process incoming message quickly"""
        chat_id = message['chat']['id']
        text = message.get('text', '').strip()
        message_id = message.get('message_id')
        chat_type = message['chat']['type']
        
        if not text:
            return
            
        text_lower = text.lower()
        
        # Get bot username for group mentions
        bot_username = self.get_bot_info()
        
        # Check if message is meant for bot in group (mention or direct message)
        is_bot_mentioned = False
        if chat_type != "private" and bot_username:
            # Check if bot is mentioned in the message
            if f"@{bot_username}" in text_lower:
                is_bot_mentioned = True
                # Remove the mention from text for processing
                text_lower = text_lower.replace(f"@{bot_username}", "").strip()
        
        # Process commands - in groups, only respond to:
        # 1. Commands with slash (/price, /ca)
        # 2. Messages that mention the bot (@botname price, @botname ca)
        # 3. In private chats, respond to all
        
        if chat_type == "private":
            # In private chats, respond to all commands and typos
            if self.is_price_command(text_lower):
                logger.info(f"🚀 Price command in private chat {chat_id}")
                self.send_price_response(chat_id, message_id)
                
            elif self.is_ca_command(text_lower):
                logger.info(f"🚀 CA command in private chat {chat_id}")
                self.send_ca_response(chat_id, message_id)
                
            elif text_lower in ['/start', '/help', 'start', 'help']:
                welcome_message = """
🤖 **Pudgy Penguins Price Bot** 🐧

*Professional real-time market data*

**Commands:**
/price or `price` - Get price data
/ca or `ca` - Get contract address

*Common typos also work:*
`pricee`,`pricce`, etc.

*In groups, use:*
`/price` or `@botname price`
`/ca` or `@botname ca`
                """.strip()
                self.telegram_bot.send_message(chat_id, welcome_message, reply_to_message_id=message_id)
        
        else:
            # In groups, only respond to slash commands or mentions
            if text_lower.startswith('/'):
                # Slash commands in groups
                command_parts = text_lower.split()
                base_command = command_parts[0]
                
                # Handle commands with and without bot username
                if base_command in ['/price', '/pricee', '/pricce'] or (bot_username and base_command == f'/price@{bot_username.lower()}'):
                    logger.info(f"🚀 Price command in group {chat_id}")
                    self.send_price_response(chat_id, message_id)
                    
                elif base_command in ['/ca', '/caa', '/cca'] or (bot_username and base_command == f'/ca@{bot_username.lower()}'):
                    logger.info(f"🚀 CA command in group {chat_id}")
                    self.send_ca_response(chat_id, message_id)
                    
                elif base_command in ['/start', '/help'] or (bot_username and base_command == f'/start@{bot_username.lower()}'):
                    welcome_message = f"""
🤖 **Pudgy Penguins Price Bot** 🐧

*Professional real-time market data*

**Commands:**
/price - Get price data
/ca - Get contract address

*Common typos also work:*
/pricee, /caa, /pricce

*Or mention me:*
`@{bot_username} price`
`@{bot_username} ca`
                    """.strip()
                    self.telegram_bot.send_message(chat_id, welcome_message, reply_to_message_id=message_id)
            
            elif is_bot_mentioned:
                # Bot was mentioned in group - process the command with typos
                if self.is_price_command(text_lower):
                    logger.info(f"🚀 Mentioned for price in group {chat_id}")
                    self.send_price_response(chat_id, message_id)
                    
                elif self.is_ca_command(text_lower):
                    logger.info(f"🚀 Mentioned for CA in group {chat_id}")
                    self.send_ca_response(chat_id, message_id)
    
    def handle_callback(self, chat_id, message_id, callback_data):
        """Handle callback queries"""
        if callback_data == "refresh":
            data = self.get_price_data()
            message = self.create_price_message(data)
            keyboard = self.create_keyboard()
            self.telegram_bot.edit_message(chat_id, message_id, message, keyboard)
    
    def send_group_update(self):
        """Send automatic update to group"""
        try:
            data = self.get_price_data()
            if data:
                message = self.create_price_message(data)
                keyboard = self.create_keyboard()
                result = self.telegram_bot.send_message(GROUP_ID, message, keyboard)
                if result and result.get('ok'):
                    logger.info(f"✅ Auto-update sent to group {GROUP_ID}")
        except Exception as e:
            logger.error(f"Error in group update: {e}")
    
    def start_polling(self):
        """Start polling for updates"""
        logger.info("🤖 Starting Pudgy Penguins Price Bot...")
        logger.info(f"📊 Target Group: {GROUP_ID}")
        logger.info("🕐 Auto-updates every 10 minutes")
        logger.info("⚡ Fast response mode activated")
        logger.info("🔤 Typo detection enabled: pricee, caa, etc.")
        
        # Get bot info
        self.get_bot_info()
        
        # Test group access silently
        test_result = self.telegram_bot.send_message(GROUP_ID, ".")
        if test_result and test_result.get('ok'):
            logger.info("✅ Bot has group access")
            # Delete the test message
            if test_result.get('result', {}).get('message_id'):
                delete_url = f"{self.telegram_bot.base_url}/deleteMessage"
                delete_payload = {
                    'chat_id': GROUP_ID,
                    'message_id': test_result['result']['message_id']
                }
                requests.post(delete_url, json=delete_payload, timeout=3)
        else:
            logger.warning("⚠️ Bot may not have group access")
        
        # Send initial group update
        self.send_group_update()
        
        # Start background thread for group updates
        def group_update_worker():
            while True:
                time.sleep(600)  # 10 minutes
                self.send_group_update()
        
        update_thread = threading.Thread(target=group_update_worker, daemon=True)
        update_thread.start()
        
        # Main polling loop
        logger.info("🔄 Starting polling...")
        while True:
            try:
                updates = self.telegram_bot.get_updates()
                
                for update in updates:
                    self.telegram_bot.last_update_id = update['update_id']
                    
                    # Handle callback queries
                    if 'callback_query' in update:
                        callback = update['callback_query']
                        chat_id = callback['message']['chat']['id']
                        message_id = callback['message']['message_id']
                        callback_data = callback['data']
                        callback_id = callback['id']
                        
                        self.telegram_bot.answer_callback_query(callback_id)
                        self.handle_callback(chat_id, message_id, callback_data)
                    
                    # Handle messages
                    elif 'message' in update:
                        message = update['message']
                        self.process_message(message)
                
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                time.sleep(2)

def main():
    """Start the bot"""
    try:
        bot = PudgyPenguinsBot()
        bot.start_polling()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")

if __name__ == "__main__":
    main()
