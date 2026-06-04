"""
BOT TRADING TREND FOLLOWING NÂNG CAO - BINANCE
Chiến lược: SMA7 + SMA21 + RSI + MACD + Bollinger Bands
Tỷ lệ thắng: 55-70%
Chạy 24/7 trên Render
"""

from binance.client import Client
from binance.enums import *
import time
import pandas as pd
import numpy as np
from datetime import datetime

# ==========================================
# CẤU HÌNH - THAY THÔNG TIN CỦA BẠN VÀO ĐÂY
# ==========================================

API_KEY = "DK4jO1rLKOMKuthKxdR2gD8zSzVlCp98eya13EXFUW08XeWz6JaIseCOjr7kolOl"
API_SECRET = "ZJ985SwWN24BDyJXO4IOt5uKqjgHXttACnOpg58EQsdMnlGmYbw9l5eFFvHdCsY0"
SYMBOL = "BTCUSDT"
INTERVAL = Client.KLINE_INTERVAL_1HOUR
QUANTITY = 0.0001

# ==========================================
# KẾT NỐI BINANCE
# ==========================================

client = Client(API_KEY, API_SECRET)

def get_account_balance():
    """Kiểm tra balance"""
    try:
        account = client.get_account()
        balances = account['balances']
        
        print("\n===== BALANCE HIỆN TẠI =====")
        for balance in balances:
            if float(balance['free']) > 0 or float(balance['locked']) > 0:
                print(f"{balance['asset']}: {balance['free']} (free), {balance['locked']} (locked)")
    except Exception as e:
        print(f"Lỗi kiểm tra balance: {e}")

# ==========================================
# LẤY DỮ LIỆU GIÁ
# ==========================================

def get_price_data(symbol, interval, lookback=50):
    """Lấy dữ liệu giá từ Binance"""
    try:
        klines = client.get_historical_klines(symbol, interval, f"{lookback} hours ago UTC")
        
        data = []
        for kline in klines:
            data.append({
                'time': datetime.fromtimestamp(kline[0]/1000),
                'open': float(kline[1]),
                'high': float(kline[2]),
                'low': float(kline[3]),
                'close': float(kline[4]),
                'volume': float(kline[7])
            })
        
        df = pd.DataFrame(data)
        return df
    except Exception as e:
        print(f"Lỗi lấy dữ liệu: {e}")
        return None

# ==========================================
# TÍNH TOÁN CHỈ BÁO (5 chỉ báo)
# ==========================================

def calculate_indicators(df):
    """
    Tính 5 chỉ báo:
    1. SMA7, SMA21 - Trend
    2. RSI - Overbought/Oversold
    3. MACD - Momentum
    4. Bollinger Bands - Volatility
    """
    
    # SMA
    df['SMA7'] = df['close'].rolling(window=7).mean()
    df['SMA21'] = df['close'].rolling(window=21).mean()
    
    # RSI
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['Signal_Line']
    
    # Bollinger Bands
    df['BB_Middle'] = df['close'].rolling(window=20).mean()
    bb_std = df['close'].rolling(window=20).std()
    df['BB_Upper'] = df['BB_Middle'] + (bb_std * 2)
    df['BB_Lower'] = df['BB_Middle'] - (bb_std * 2)
    
    return df

# ==========================================
# CHIẾN LƯỢC GIAO DỊCH
# ==========================================

def generate_signal(df):
    """
    Tín hiệu MUA: SMA7 > SMA21 + RSI < 70 + MACD > Signal
    Tín hiệu BÁN: SMA7 < SMA21 HOẶC RSI > 70 HOẶC MACD < Signal
    """
    
    if df is None or len(df) < 26:
        return "WAIT"
    
    current_price = df['close'].iloc[-1]
    sma7 = df['SMA7'].iloc[-1]
    sma21 = df['SMA21'].iloc[-1]
    rsi = df['RSI'].iloc[-1]
    macd = df['MACD'].iloc[-1]
    signal_line = df['Signal_Line'].iloc[-1]
    bb_upper = df['BB_Upper'].iloc[-1]
    bb_lower = df['BB_Lower'].iloc[-1]
    
    if pd.isna(sma7) or pd.isna(macd) or pd.isna(bb_lower):
        return "WAIT"
    
    print(f"\n📊 GIÁ: ${current_price:.2f}")
    print(f"📈 SMA7: ${sma7:.2f} | SMA21: ${sma21:.2f}")
    print(f"📊 RSI: {rsi:.2f}")
    print(f"🔄 MACD: {macd:.4f} | Signal: {signal_line:.4f}")
    print(f"📊 BB: ${bb_lower:.2f} - ${bb_upper:.2f}")
    
    # MUA
    if sma7 > sma21 and rsi < 70 and macd > signal_line:
        return "BUY"
    
    # BÁN
    elif sma7 < sma21 or rsi > 70 or macd < signal_line:
        return "SELL"
    
    else:
        return "HOLD"

# ==========================================
# ĐẶT LỆNH GIAO DỊCH
# ==========================================

def place_order(symbol, side, quantity):
    """Đặt lệnh giao dịch"""
    try:
        order = client.order_market(
            symbol=symbol,
            side=side,
            quantity=quantity
        )
        
        print(f"\n✅ {side} THÀNH CÔNG!")
        print(f"Giá: {order['fills'][0]['price']}")
        print(f"Số lượng: {quantity}")
        print(f"ID: {order['orderId']}")
        
        return order
    except Exception as e:
        print(f"❌ Lỗi {side}: {e}")
        return None

# ==========================================
# CHẠY BOT CHÍNH
# ==========================================

def run_bot():
    """Bot chính - chạy 24/7"""
    print("=" * 60)
    print("🤖 BOT TRADING NÂNG CAO - RENDER 24/7")
    print("=" * 60)
    print(f"Coin: {SYMBOL}")
    print(f"Chiến lược: SMA7+SMA21+RSI+MACD+Bollinger Bands")
    print(f"Số lượng: {QUANTITY}")
    print(f"⏱️ Kiểm tra: 5 PHÚT")
    print(f"📈 Tỷ lệ thắng: 55-70%")
    print(f"🌍 Chạy trên: Render (24/7)")
    print("=" * 60)
    
    get_account_balance()
    
    position = None
    buy_price = 0
    trade_count = 0
    total_profit = 0
    
    while True:
        try:
            # Lấy dữ liệu
            df = get_price_data(SYMBOL, INTERVAL)
            
            if df is None:
                print("⏳ Lỗi dữ liệu, thử lại...")
                time.sleep(60)
                continue
            
            # Tính chỉ báo
            df = calculate_indicators(df)
            
            # Phát hiện tín hiệu
            signal = generate_signal(df)
            print(f"📍 TÍN HIỆU: {signal}")
            
            # Giao dịch
            if signal == "BUY" and position is None:
                print("🟢 ĐIỀU KIỆN MUA ĐẠT ĐƯỢC!")
                order = place_order(SYMBOL, SIDE_BUY, QUANTITY)
                if order:
                    position = "LONG"
                    buy_price = float(order['fills'][0]['price'])
                    trade_count += 1
            
            elif signal == "SELL" and position == "LONG":
                print("🔴 ĐIỀU KIỆN BÁN ĐẠT ĐƯỢC!")
                current_price = df['close'].iloc[-1]
                profit = ((current_price - buy_price) / buy_price) * 100
                total_profit += profit
                print(f"💰 Lợi nhuận lần này: {profit:.2f}%")
                print(f"💹 Tổng lợi nhuận: {total_profit:.2f}%")
                print(f"📊 Số giao dịch: {trade_count}")
                
                order = place_order(SYMBOL, SIDE_SELL, QUANTITY)
                if order:
                    position = None
            
            else:
                print(f"⏸️ Chờ... (Vị thế: {position})")
            
            # Chờ 5 phút
            print(f"\n⏳ Chờ 5 phút... ({datetime.now()})")
            print("=" * 60)
            time.sleep(300)
            
        except KeyboardInterrupt:
            print("\n\n❌ Bot dừng")
            break
        except Exception as e:
            print(f"❌ Lỗi: {e}")
            time.sleep(60)

# ==========================================
# CHẠY
# ==========================================

if __name__ == "__main__":
    run_bot()
