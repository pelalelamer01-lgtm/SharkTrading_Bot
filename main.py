import MetaTrader5 as mt5
import telegram
import asyncio
import pandas as pd
import time
from datetime import datetime

# ================= إعدادات التليجرام =================
BOT_TOKEN = "8888596362:AAGERGZWe5q7A2eT9zK5uT-X0aLtKdWIgHk"
CHAT_ID = "6230253013"

async def send_telegram_msg(text):
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ================= إعدادات التداول (MT5 & Exness) =================
SYMBOL = "EURUSD" # يمكنك تغييره للذهب XAUUSD
LOT_SIZE = 1.0    # 1 لوت كامل كما طلبت (انتبه: يحتاج رأس مال كبير)
TP_PIPS = 50      # تيك بروفت (Take Profit)
SL_PIPS = 25      # ستوب لوس (Stop Loss)

# ================= 1. الخوارزميات وتحديد مناطق السيولة =================
def analyze_liquidity_and_trend(symbol):
    # جلب آخر 100 شمعة لتحليلها
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)
    df = pd.DataFrame(rates)
    
    # تحديد القمم والقيعان (Liquidity Zones)
    resistance_zone = df['high'].max()
    support_zone = df['low'].min()
    current_price = df['close'].iloc[-1]
    
    # خوارزمية مبدئية: الشراء قرب الدعم، البيع قرب المقاومة
    if current_price <= support_zone + 0.0005:
        return "BUY"
    elif current_price >= resistance_zone - 0.0005:
        return "SELL"
    return "WAIT"

# ================= 2. مصيدة الحيتان (Whale Trap) =================
def check_whale_trap(symbol):
    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M1, 0, 5)
    df = pd.DataFrame(rates)
    
    # مراقبة حجم التداول (Volume Anomaly) في آخر دقيقة
    avg_volume = df['tick_volume'].iloc[:-1].mean()
    current_volume = df['tick_volume'].iloc[-1]
    
    # إذا كان الحجم فجأة ضعف المتوسط = دخول حيتان (فخ محتمل)
    if current_volume > (avg_volume * 3):
        return True # يوجد فخ، توقف عن التداول مؤقتاً
    return False

# ================= 3. التعلم الآلي (Machine Learning - الهيكل) =================
def learn_from_market():
    # هنا سيتم دمج مكتبة Scikit-Learn لاحقاً لتحليل ملف الصفقات (Trade_History.csv)
    # وجعل البوت يغير الـ TP والـ SL بناءً على نسبة النجاح
    pass

# ================= 4. تنفيذ الصفقة (فتح / إغلاق) =================
def open_trade(symbol, action):
    tick = mt5.symbol_info_tick(symbol)
    point = mt5.symbol_info(symbol).point
    
    if action == "BUY":
        order_type = mt5.ORDER_TYPE_BUY
        price = tick.ask
        sl = price - (SL_PIPS * point)
        tp = price + (TP_PIPS * point)
    elif action == "SELL":
        order_type = mt5.ORDER_TYPE_SELL
        price = tick.bid
        sl = price + (SL_PIPS * point)
        tp = price - (TP_PIPS * point)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": LOT_SIZE,
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 20,
        "magic": 777777, # رقم البوت
        "comment": "Shark Whale Hunter",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    result = mt5.order_send(request)
    return result, price

# ================= الحلقة الرئيسية (المراقب الدائم) =================
async def main_bot_loop():
    await send_telegram_msg("🚀 وحش التداول بدأ العمل.. جاري البحث عن سيولة وفخاخ الحيتان!")
    
    if not mt5.initialize():
        await send_telegram_msg("❌ فشل الاتصال بمنصة MT5. يرجى مراجعة التشغيل.")
        return

    while True:
        try:
            # 1. هل هناك فخ حيتان؟
            if check_whale_trap(SYMBOL):
                print("تم رصد سيولة ضخمة (حيتان).. الانتظار لتجنب الفخ.")
                time.sleep(60)
                continue
            
            # 2. تحليل السيولة والاتجاه
            decision = analyze_liquidity_and_trend(SYMBOL)
            
            # 3. اتخاذ القرار
            if decision in ["BUY", "SELL"]:
                result, entry_price = open_trade(SYMBOL, decision)
                
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    msg = f"✅ تم فتح صفقة {decision} بنجاح!\nاللوت: {LOT_SIZE}\nالسعر: {entry_price}"
                    await send_telegram_msg(msg)
                    # بعد فتح الصفقة ننتظر قليلاً كي لا يفتح صفقات متكررة في نفس الثانية
                    time.sleep(3600) 
                
            # 4. تدريب الذكاء الاصطناعي (يتم استدعاؤه بشكل دوري)
            learn_from_market()

            time.sleep(10) # مراقبة السوق كل 10 ثوانٍ

        except Exception as e:
            print(f"Error: {e}")
            time.sleep(10)

if __name__ == '__main__':
    asyncio.run(main_bot_loop())
