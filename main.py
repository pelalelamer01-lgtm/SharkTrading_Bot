import telegram
import asyncio

# بيانات التليجرام الخاصة بك
BOT_TOKEN = "8888596362:AAGERGZWe5q7A2eT9zK5uT-X0aLtKdWIgHk"
CHAT_ID = "6230253013"

async def send_message(text):
    try:
        bot = telegram.Bot(token=BOT_TOKEN)
        await bot.send_message(chat_id=CHAT_ID, text=text)
        print("تم إرسال الرسالة بنجاح")
    except Exception as e:
        print(f"حدث خطأ: {e}")

if __name__ == '__main__':
    print("البوت بدأ العمل...")
    # إرسال رسالة ترحيبية عند التشغيل
    asyncio.run(send_message("تم ربط البوت بنجاح! أنا جاهز للبدء في صيد الصفقات. 🦅🦈"))
