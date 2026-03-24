# 🎯 Polymarket Quant Sniper (AI + Whale Tracker)

Polymarket Quant Sniper is an advanced algorithmic trading agent built for the Polygon network. The bot scans the blockchain in real-time to track the movements of top-performing traders ("Whales"). Before mirroring any trade, it queries an open-source Large Language Model (Llama 3 via Groq) to validate the macroeconomic logic of the event, ensuring execution only on high-probability setups via the Polymarket CLOB (Central Limit Order Book).

## ⚠️ Important Disclaimer
**This software is for educational and research purposes only.** Trading on predictive markets involves a high risk of capital loss. The author is not responsible for any financial losses incurred. Never invest money you cannot afford to lose.

## 🚀 Key Features
* **On-Chain Tracking:** Monitors public addresses of top-tier traders directly on the Polygon blockchain with zero latency.
* **AI Validator:** Utilizes `Llama 3 70B` to filter out irrational trades, market-making noise, and low-value bets.
* **Integrated Risk Management:** Automatically calculates dynamic position sizing (max 5% of total capital per trade) to prevent account ruin.
* **Slippage Protection:** Rejects shares priced above $0.85 to maintain a strictly asymmetric risk/reward ratio.
* **Cloudflare Rate Limiter:** Built-in delay mechanisms to strictly adhere to Polymarket's API rate limits and avoid IP bans.

## 🛠️ Prerequisites
1. **Python 3.10+** installed on your machine.
2. A free **[Alchemy](https://www.alchemy.com/)** account (for the Polygon RPC node).
3. A free **[Groq](https://console.groq.com/)** account (for lightning-fast Llama 3 API access).
4. A **Polymarket** account with API Keys generated and USDC funds on the Polygon network.
5. *(Recommended)* A **VPN** connection routed through a permitted jurisdiction (e.g., Switzerland) if operating from a restricted region.

## ⚙️ Installation

1. **Clone or download the repository.**
2. **Open your terminal** in the project directory.
3. **Install the required dependencies:**
   ```bash
   pip install -r requirements.txt
