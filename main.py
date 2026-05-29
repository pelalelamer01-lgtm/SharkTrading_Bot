import time
import requests # المكتبة الجديدة اللي DeepSeek نصح بيها

# ========== إعدادات الربط ==========
# هنا بتحط الرابط اللي الإكسبرت (EA) بتاعك هيديهولك
WEBHOOK_URL = "http://your_vps_ip_or_domain:port/trade"

def send_order_webhook(action, symbol, volume=0.01, sl=None, tp=None):
    """إرسال أمر عبر الشبكة بدلاً من مكتبة MT5"""
    payload = {
        "symbol": symbol,
        "action": action, # 'buy' أو 'sell'
        "volume": volume,
        "sl": sl,
        "tp": tp,
        "comment": "Shark_Bot_Cloud_Signal"
    }
    try:
        response = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        print(f"✅ إشارة {action} مرسلة: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"❌ فشل إرسال الإشارة عبر Webhook: {e}")
        return None

# ========== دالة التنفيذ (تعديل دالة open_trade القديمة) ==========
def open_trade(signal_type, current_price):
    # الحسابات اللي كنا بنعملها
    sl = current_price - 2.00 if signal_type == 'Buy' else current_price + 2.00
    tp = current_price + 4.00 if signal_type == 'Buy' else current_price - 4.00
    
    # الإرسال
    send_order_webhook(signal_type.lower(), "XAUUSDm", volume=0.01, sl=sl, tp=tp)
