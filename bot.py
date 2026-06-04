"""
BOT TRADING TREND FOLLOWING - BINANCE
Chạy 24/7 trên Render
"""

from binance.client import Client
from binance.enums import *
import time
from datetime import datetime

# ==========================================
# CẤU HÌNH
# ==========================================

API_KEY = "DK4jO1rLKOMKuthKxdR2gD8zSzVlCp98eya13EXFUW08XeWz6JaIseCOjr7kolOl"
API_SECRET = "ZJ985SwWN24BDyJXO4IOt5uKqjgHXttACnOpg58EQsdMnlGmYbw9l5eFFvHdCsY0"
SYMBOL = "BTCUSDT"
INTERVAL = Client.KLINE_INTERVAL_1HOUR
QUANTITY = 0.0001

client = Client(API_KEY, API_SECRET)

def get_account_balance():
    try:
        account = client.get_account()
        balances = account['balances']
        
        print("\n===== BALANCE HIỆN TẠI =====")
        for balance in balances:
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                print(f"{balance['asset']}: {balance['free']}")
    except Exception as e:
        print(f"Lỗi: {e}")

def get_price_data(symbol, interval, lookback=30):
    try:
        klines = client.get_historical_klines(symbol, interval, f"{lookback} hours ago UTC")
        prices = [float(kline[4]) for kline in klines]
        return prices
    except Exception as e:
        print(f"Lỗi lấy dữ liệu: {e}")
        return None

def calculate_sma(prices, period):
    if len(prices) < period:
        return None
    return sum(prices[-period:]) / period

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = [c if c > 0 else 0 for c in changes[-period:]]
    losses = [-c if c < 0 else 0 for c in changes[-period:]]
    
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    
    if avg_loss == 0:
        return 100
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi

def generate_signal(prices):
    if prices is None or len(prices) < 21:
        return "WAIT"
    
    current_price = prices[-1]
    sma7 = calculate_sma(prices, 7)
    sma21 = calculate_sma(prices, 21)
    rsi = calculate_rsi(prices)
    
    if sma7 is None or sma21 is None or rsi is None:
        return "WAIT"
    
    print(f"\n📊 GIÁ: ${current_price:.2f}")
    print(f"📈 SMA7: ${sma7:.2f} | SMA21: ${sma21:.2f}")
    print(f"📊 RSI: {rsi:.2f}")
    
    if sma7 > sma21 and rsi < 70:
        return "BUY"
    elif sma7 < sma21 or rsi > 70:
        return "SELL"
    else:
        return "HOLD"

def place_order(symbol, side, quantity):
    try:
        order = client.order_market(
            symbol=symbol,
            side=side,
            quantity=quantity
        )
        
        print(f"\n✅ {side} THÀNH CÔNG!")
        print(f"Giá: {order['fills'][0]['price']}")
        print(f"ID: {order['orderId']}")
        
        return order
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        return None

def run_bot():
    print("=" * 60)
    print("🤖 BOT TRADING - RENDER 24/7")
    print("=" * 60)
    print(f"Coin: {SYMBOL}")
    print(f"Chiến lược: SMA7 + SMA21 + RSI")
    print(f"Kiểm tra: Mỗi 5 phút")
    print("=" * 60)
    
    get_account_balance()
    
    position = None
    buy_price = 0
    
    while True:
        try:
            prices = get_price_data(SYMBOL, INTERVAL)
            
            if prices is None:
                print("⏳ Lỗi, thử lại...")
                time.sleep(60)
                continue
            
            signal = generate_signal(prices)
            print(f"📍 TÍN HIỆU: {signal}")
            
            if signal == "BUY" and position is None:
                print("🟢 ĐIỀU KIỆN MUA!")
                order = place_order(SYMBOL, SIDE_BUY, QUANTITY)
                if order:
                    position = "LONG"
                    buy_price = float(order['fills'][0]['price'])
            
            elif signal == "SELL" and position == "LONG":
                print("🔴 ĐIỀU KIỆN BÁN!")
                current_price = prices[-1]
                profit = ((current_price - buy_price) / buy_price) * 100
                print(f"💰 Lợi nhuận: {profit:.2f}%")
                
                order = place_order(SYMBOL, SIDE_SELL, QUANTITY)
                if order:
                    position = None
            
            else:
                print(f"⏸️ Chờ... (Vị thế: {position})")
            
            print(f"\n⏳ Chờ 5 phút... ({datetime.now()})")
            print("=" * 60)
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n❌ Bot dừng")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()
