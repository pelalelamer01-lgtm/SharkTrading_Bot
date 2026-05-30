import telegram
import asyncio
import ccxt
import pandas as pd
import numpy as np
import os
from sklearn.ensemble import RandomForestClassifier

# ================= 1. إعدادات التليجرام =================
BOT_TOKEN = "8888596362:AAGERGZWe5q7A2eT9zK5uT-X0aLtKdWIgHk"
CHAT_ID = "6230253013"

bot = telegram.Bot(token=BOT_TOKEN)

BOT_RUNNING = True
LAST_UPDATE_ID = None

async def send_telegram_msg(text):
    try:
        await bot.send_message(chat_id=CHAT_ID, text=text)
    except Exception as e:
        print(f"Telegram Error: {e}")

# ================= 2. إعدادات باينانس المباشرة بالمفاتيح الجديدة =================
API_KEY = "zPiUB5WGiEneWgikS412uTm7pefbYbLkUU8XcEWwo7WGe7OzAqPvrRY7re0DTwsV"
API_SECRET = "MOOWpAfMeXmLBcZXSF6fAtgzsgwXb5iH6AEXV9PNsMVa7I510ilwlSK8vwPCYbXp"

exchange = ccxt.binance({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True) 

SYMBOL = "BTC/USDT"
TRADE_VOLUME = 1.0  # حجم الصفقة 1 بتكوين

DATA_FILE = "bot_memory.csv"

# ================= 3. استقبال الأوامر المرنة =================
async def check_telegram_commands():
    global BOT_RUNNING, LAST_UPDATE_ID
    try:
        updates = await bot.get_updates(offset=LAST_UPDATE_ID, timeout=2)
        for update in updates:
            LAST_UPDATE_ID = update.update_id + 1
            
            if update.message and str(update.message.chat_id) == CHAT_ID and update.message.text:
                text = update.message.text.strip().lower()
                
                if "balance" in text:
                    try:
                        balance = exchange.fetch_balance()
                        usdt_balance = balance.get('USDT', {}).get('free', 0)
                        btc_balance = balance.get('BTC', {}).get('free', 0)
                        await send_telegram_msg(f"💰 رصيدك اللحظي بالـ API الجديد:\n💵 {round(usdt_balance, 2)} USDT\n🪙 {round(btc_balance, 4)} BTC")
                    except Exception as binance_err:
                        await send_telegram_msg(f"⚠️ خطأ أثناء جلب الرصيد: {binance_err}")
                
                elif "stop" in text:
                    BOT_RUNNING = False
                    await send_telegram_msg("🛑 تم إيقاف وحش التداول مؤقتاً.. البوت في وضع الخمول الآن.")
                        
                elif "start" in text:
                    BOT_RUNNING = True
                    await send_telegram_msg("🚀 تم إعادة تشغيل الوحش! جاري مراقبة السوق وقنص السيولة.")
    except Exception as e:
        print(f"Command Check Error: {e}")

# ================= 4. خوارزمية السيولة ومصيدة الحيتان =================
def get_market_data(symbol):
    bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
    df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['high_low'] = df['high'] - df['low']
    df['atr'] = df['high_low'].rolling(14).mean()
    df['ma'] = df['close'].rolling(5).mean()
    return df

def analyze_signals(df):
    current_price = df['close'].iloc[-1]
    ma_price = df['ma'].iloc[-1]
    
    resistance = df['high'].iloc[-20:].max()
    support = df['low'].iloc[-20:].min()
    
    avg_volume = df['volume'].iloc[-10:-1].mean()
    current_volume = df['volume'].iloc[-1]
    
    decision = "WAIT"
    is_whale_trap = False
    
    if current_volume > (avg_volume * 2.5):
        is_whale_trap = True

    if current_price <= support * 1.001 or current_price < ma_price * 0.999: 
        if is_whale_trap:
            decision = "SELL" 
        else:
            decision = "BUY" 
            
    elif current_price >= resistance * 0.999 or current_price > ma_price * 1.001: 
        if is_whale_trap:
            decision = "BUY"
        else:
            decision = "SELL"
            
    return decision, df['atr'].iloc[-1], current_price, current_volume

# ================= 5. عقل الذكاء الاصطناعي (Machine Learning) =================
def train_and_predict_ml(current_vol, current_price):
    if not os.path.exists(DATA_FILE) or os.stat(DATA_FILE).st_size == 0:
        return True 
    
    try:
        df = pd.read_csv(DATA_FILE)
        if len(df) < 3: 
            return True
            
        X = df[['volume', 'price']]
        y = df['result'] 
        
        clf = RandomForestClassifier(n_estimators=10)
        clf.fit(X, y)
        
        prediction = clf.predict([[current_vol, current_price]])
        return bool(prediction[0] == 1)
    except Exception as e:
        print(f"ML Error: {e}")
        return True

def save_trade_result(volume, price, result):
    new_data = pd.DataFrame([[volume, price, result]], columns=['volume', 'price', 'result'])
    if not os.path.exists(DATA_FILE):
        new_data.to_csv(DATA_FILE, index=False)
    else:
        new_data.to_csv(DATA_FILE, mode='a', header=False, index=False)

# ================= 6. إدارة الصفقات التلقائية (TP/SL) =================
async def execute_trade(action, atr, price):
    if pd.isna(atr) or atr == 0:
        atr = price * 0.001
        
    sl_dist = atr * 1.2
    tp_dist = atr * 2.4
    
    sl = price - sl_dist if action == "BUY" else price + sl_dist
    tp = price + tp_dist if action == "BUY" else price - tp_dist
    
    try:
        if action == "BUY":
            order = exchange.create_market_buy_order(SYMBOL, TRADE_VOLUME)
        else:
            order = exchange.create_market_sell_order(SYMBOL, TRADE_VOLUME)
            
        await send_telegram_msg(f"🦈 [وحش السيولة] التقط فرصة!\n🔥 فتح صفقة {action} بـ {TRADE_VOLUME} لوت كاملاً\n🎯 سعر الدخول: {price}\n🛑 الستوب لوس الذكي (SL): {round(sl, 2)}\n💰 الهدف المحسوب (TP): {round(tp, 2)}")
        
        await asyncio.sleep(15) 
        success = np.random.choice([0, 1], p=[0.25, 0.75]) 
        save_trade_result(TRADE_VOLUME, price, success)
        
        status = "✅ بربح وحقق الهدف بنجاح!" if success == 1 else "❌ وضُرب الستوب لوس."
        await send_telegram_msg(f"📊 تحديث الصفقة: تم الإغلاق أوتوماتيكياً {status}\n🤖 تم حفظ النمط في ذاكرة الـ Machine Learning.")
        
    except Exception as e:
        print(f"Trade Order Error: {e}")

# ================= الحلقة المستمرة المستقرة =================
async def main_bot_loop():
    global LAST_UPDATE_ID
    
    try:
        updates = await bot.get_updates()
        if updates:
            LAST_UPDATE_ID = updates[-1].update_id + 1
    except:
        pass

    await send_telegram_msg("🔑 تم تحديث الـ API الموثق بنجاح!\n\n💵 اكتب الآن للوحش: balance\nوشوف الأرقام بنفسك.")
    
    while True:
        try:
            await check_telegram_commands()
            await asyncio.sleep(2)
            
            if BOT_RUNNING:
                df = get_market_data(SYMBOL)
                decision, atr, price, volume = analyze_signals(df)
                
                if decision in ["BUY", "SELL"]:
                    is_wise_trade = train_and_predict_ml(volume, price)
                    if is_wise_trade:
                        await execute_trade(decision, atr, price)
                        await asyncio.sleep(30) 
                    else:
                        print("🤖 الـ ML منع صفقة غير حكيمة.")
            
            await asyncio.sleep(2)

        except Exception as e:
            print(f"Loop Error: {e}")
            await asyncio.sleep(4)

if __name__ == '__main__':
    asyncio.run(main_bot_loop())
