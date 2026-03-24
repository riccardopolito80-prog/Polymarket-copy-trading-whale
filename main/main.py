import time
import os
import json
import requests
from web3 import Web3
from py_clob_client.client import ClobClient
from py_clob_client.credentials import ApiCreds
from openai import OpenAI
from dotenv import load_dotenv

# Load variables from the .env file
load_dotenv()

# ==========================================
# 1. RISK AND CAPITAL MANAGEMENT
# ==========================================
class RiskManager:
    def __init__(self, starting_capital):
        self.current_capital = float(starting_capital)
        self.max_risk_per_trade = 0.05  # Max 5% of total capital per trade
        
    def calculate_position_size(self):
        size = self.current_capital * self.max_risk_per_trade
        if size < 2.0: # Minimum sensible amount on Polymarket to offset gas/fees
            return 0
        return round(size, 2)

# ==========================================
# 2. RATE LIMITER (Cloudflare Protection)
# ==========================================
class RateLimiter:
    def __init__(self):
        self.last_call = 0
        self.interval = 0.2 # Maximum 5 requests per second to stay extremely safe
        
    def wait(self):
        now = time.time()
        elapsed = now - self.last_call
        if elapsed < self.interval:
            time.sleep(self.interval - elapsed)
        self.last_call = time.time()

# ==========================================
# 3. THE MAIN BOT
# ==========================================
class PolymarketSniper:
    def __init__(self):
        print("🚀 Initializing Polymarket Sniper Bot...")
        
        # Initialize Modules
        self.risk = RiskManager(os.getenv("STARTING_CAPITAL", 100))
        self.limiter = RateLimiter()
        
        # Blockchain Connection (Polygon)
        self.w3 = Web3(Web3.HTTPProvider(os.getenv("ALCHEMY_RPC_URL")))
        if not self.w3.is_connected():
            raise Exception("❌ Unable to connect to Alchemy. Check your RPC URL.")
            
        # Polymarket CLOB Connection
        creds = ApiCreds(
            api_key=os.getenv("CLOB_API_KEY"),
            api_secret=os.getenv("CLOB_SECRET"),
            api_passphrase=os.getenv("CLOB_PASSPHRASE")
        )
        self.clob = ClobClient(
            "https://clob.polymarket.com", 
            key=os.getenv("PK"), 
            chain_id=137, 
            creds=creds
        )
        
        # Artificial Intelligence Connection (Groq / Llama 3)
        self.ai = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"), 
            base_url="https://api.groq.com/openai/v1"
        )
        
        # Whales Configuration (Insert the public addresses of top traders here)
        self.whales = {
            self.w3.to_checksum_address("0x1111111111111111111111111111111111111111"), # Replace this
            self.w3.to_checksum_address("0x2222222222222222222222222222222222222222")  # Replace this
        }
        
        # Polymarket Exchange Contract Address on Polygon
        self.exchange_address = self.w3.to_checksum_address("0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E")

    def get_market_info(self, token_id):
        """Fetches the market question based on the token_id via Gamma API"""
        self.limiter.wait()
        try:
            res = requests.get(f"https://gamma-api.polymarket.com/tokens/{token_id}")
            if res.status_code == 200:
                data = res.json()
                return data.get('question', 'Unknown Market')
        except:
            pass
        return "Unknown Market"

    def ask_ai(self, question, action_type):
        """Uses Llama 3 to validate the logic of the trade"""
        self.limiter.wait()
        prompt = f"""
        You are a quantitative trading bot. A highly profitable 'Whale' has just made a '{action_type}' transaction on this market: "{question}".
        Our budget is strictly limited. Does betting on this event make macroeconomic or logical sense right now?
        Reply ONLY with the exact word: BUY or IGNORE.
        """
        try:
            res = self.ai.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0 # Zero creativity, purely logical response
            )
            decision = res.choices[0].message.content.strip().upper()
            return "BUY" in decision
        except Exception as e:
            print(f"⚠️ AI Error: {e}")
            return False

    def execute_trade(self, token_id, side="BUY"):
        """Places the order on the Polymarket CLOB"""
        size = self.risk.calculate_position_size()
        if size == 0:
            print("⚠️ Insufficient capital to open new positions.")
            return

        self.limiter.wait()
        try:
            # Fetch the current midpoint price
            price_data = self.clob.get_midpoint(token_id)
            current_price = float(price_data.get('mid', 0.5))
            
            # Slippage control (do not buy if shares are too expensive)
            if current_price > 0.85:
                print(f"🛑 Price at ${current_price}. Too high (poor risk/reward). Trade ignored.")
                return

            print(f"💸 Sending order: {size} USDC on token {token_id} at ~${current_price}...")
            
            # Create and post the order (LIMIT order to avoid taker fees and slippage)
            order = self.clob.create_order(
                token_id=token_id,
                price=current_price,
                side=side,
                size=size,
                fee_rate_bps=0 # Zero fees if placed correctly as a maker limit order
            )
            resp = self.clob.post_order(order)
            print(f"✅ Trade Executed! Response: {resp}")
            
        except Exception as e:
            print(f"❌ Order execution failed: {e}")

    def decode_and_process_tx(self, tx):
        """Extracts and processes data from the Whale's transaction"""
        # In a production environment, the hex input data must be decoded using the contract ABI.
        # Since the Polymarket ABI is massive, the safest method for a bot is to
        # check the generated events (Logs) or decode the first 4 bytes of the method.
        # For this executable script, we simulate the token_id decoding.
        
        input_data = tx['input'].hex()
        
        # Basic check: the transaction contains data payload
        if len(input_data) > 10:
            print(f"\n🚨 WHALE {tx['from']} IN ACTION! Hash: {tx['hash'].hex()}")
            
            # TODO: Replace with an actual token_id extractor based on tx_receipt.logs
            fake_token_id = "0x286364020a67e810a9cf1b9cf2e20d6f228cbdf243e86c12ba3c3a9f06ddbe24" 
            
            question = self.get_market_info(fake_token_id)
            print(f"📊 Market identified: {question}")
            
            if self.ask_ai(question, "Purchase"):
                print("🧠 AI: Green Light. Executing whale copy trade.")
                self.execute_trade(fake_token_id, "BUY")
            else:
                print("🛡️ AI: Operation rejected. Saving funds.")

    def run(self):
        print(f"✅ System Online. Operating capital: ${self.risk.current_capital}")
        last_block = self.w3.eth.block_number
        
        while True:
            try:
                current_block = self.w3.eth.block_number
                if current_block > last_block:
                    for block_num in range(last_block + 1, current_block + 1):
                        block = self.w3.eth.get_block(block_num, full_transactions=True)
                        for tx in block.transactions:
                            # Check if the sender is a Whale and the recipient is Polymarket
                            if tx['from'] in self.whales and tx['to'] == self.exchange_address:
                                self.decode_and_process_tx(tx)
                                
                    last_block = current_block
                
                # Wait to avoid burning Alchemy API credits (Polygon block time is ~2 seconds)
                time.sleep(2)
                
            except Exception as e:
                print(f"Loop error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    bot = PolymarketSniper()
    bot.run()
