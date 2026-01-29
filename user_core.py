#  user_core.py  –  نسخة نهائية كاملة بعد إضافة التوكن وتحميل m11.py
#  كل الكلايش محفوظة كاملة، لا اقتصاص ولا اختصار.

from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon import TelegramClient, events, functions, types
from telethon.sessions import StringSession
from telethon.tl.functions.messages import CreateChatRequest, EditChatPhotoRequest
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantAdmin, ChannelParticipantCreator, InputChatUploadedPhoto
import asyncio, os, time, pytz, re, importlib.util, sys, json
import yt_dlp
from datetime import datetime, timedelta

start_time = datetime.now()

# ==========  معلومات ثابتة  ==========
DEV_USER   = "@I_QQ_Q"
SOURCE_CH  = "SORS_RECO"
TOKEN_FILE = "user_bot_token.json"   # ملف حفظ توكن البوت

# ==========  وظيفة تحميل التوكن  ==========
def load_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, encoding="utf-8") as f:
            return json.load(f).get("bot_token")
    return None

# ==========  الخطوط المزخرفة للساعة  ==========
fonts = {
    "0":"0️⃣", "1":"1️⃣", "2":"2️⃣", "3":"3️⃣", "4":"4️⃣",
    "5":"5️⃣", "6":"6️⃣", "7":"7️⃣", "8":"8️⃣", "9":"9️⃣",
    ":":":", "A":"𝔸", "P":"ℙ", "M":"𝕄"
}
def get_styled_time(t_str):
    return "".join(fonts.get(c, c) for c in t_str.upper())

# ==========  دالة تشغيل السيشن  ==========
async def start_user_source(session_str, api_id, api_hash, install_info=None):
    client = TelegramClient(StringSession(session_str), api_id, api_hash)

    # متغيرات التحكم
    save_enabled      = True
    bold_enabled      = False
    storage_pv        = None
    storage_groups    = None
    storage_deleted   = None
    name_task         = None
    original_name     = ""
    admins_list       = []
    muted_users       = []
    msg_cache         = {}

    bot_token = load_token()
    if bot_token:
        print("✅ تم تحميل توكن البوت، سيتم تفعيل الأزرار الشفافة.")
    else:
        print("⚠️ لا يوجد توكن بوت، الأزرار لن تعمل.")

    # ==========  تحديث الوقت بالاسم تلقائياً  ==========
    async def auto_update_name():
        nonlocal original_name
        try:
            me = await client.get_me()
            if not original_name or "|" in me.first_name:
                original_name = me.first_name.split('|')[0].strip()
        except:
            original_name = "User"
        tz = pytz.timezone('Asia/Baghdad')
        while True:
            try:
                time_str = datetime.now(tz).strftime("%I:%M %p")
                await client(functions.account.UpdateProfileRequest(
                    first_name=f"{original_name} | {get_styled_time(time_str)}"
                ))
            except asyncio.CancelledError:
                break
            except:
                pass
            await asyncio.sleep(60)

    # ==========  إنشاء/جلب مجموعات التخزين  ==========
    async def create_storage_group(title, photo_file, description):
        try:
            async for d in client.iter_dialogs(limit=100):
                if d.name == title:
                    return d.id
            r = await client(CreateChatRequest(title=title, users=["me"]))
            chat_id = None
            if hasattr(r, 'chats') and r.chats:
                chat_id = r.chats[0].id
            if not chat_id:
                await asyncio.sleep(3)
                async for d in client.iter_dialogs(limit=20):
                    if d.name == title:
                        chat_id = d.id
                        break
            if chat_id:
                await asyncio.sleep(2)
                if os.path.exists(photo_file):
                    up = await client.upload_file(photo_file)
                    await client(EditChatPhotoRequest(chat_id=chat_id, photo=InputChatUploadedPhoto(up)))
                await client.send_message(chat_id, description)
                return chat_id
            return None
        except Exception as e:
            print(f"❌ خطأ إنشاء المجموعة {title}: {e}")
            return None

    # ==========  معالج الرسائل والأوامر  ==========
    @client.on(events.NewMessage)
    async def handler(event):
        nonlocal bold_enabled, name_task, original_name, admins_list, muted_users
        sender_id = event.sender_id
        me = await client.get_me()
        my_id = me.id
        is_admin = (sender_id == my_id) or (sender_id in admins_list)

        # حذف رسائل المكتومين
        if sender_id in muted_users and not event.out:
            try:
                if event.is_private:
                    await event.delete()
                elif event.is_group:
                    perms = await client.get_permissions(event.chat_id, my_id)
                    if perms.is_admin or perms.is_creator:
                        await event.delete()
            except:
                pass

        # تخزين الرسائل لكشف المحذوفات
        if event.is_private and not event.out:
            msg_cache[event.id] = {
                'message': event.message,
                'expiry': datetime.now() + timedelta(minutes=10)
            }

        # ==========  الأوامر  ==========
        if is_admin and event.out:
            cmd = event.raw_text

            # -------------------- م1 --------------------
            if cmd == ".م1":
                await event.edit("""⚙️ أوامـر الـحـسـاب والـتـنسـيـق (م1) :
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
• .ايدي : كشف معلومات الحساب.
• .انتحال : نسخ حساب (رد/يوزر).
• .ايقاف_انتحال : العودة لبياناتك الأصلية.
• .مسح : مسح الخاص طرفين / مغادرة الكروبات.
• .اعادة_تشغيل : تحديث السورس.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉""")

            # -------------------- م2 --------------------
            elif cmd == ".م2":
                await event.edit("""💬 أوامـر الـردود والـتـشـويـش (م2) :
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
• .رد : إضافة رد جديد.
• .حذف_رد : حذف رد معين.
• .ردودي : عرض قائمة الردود.
• .تشويش : إرسال نص مخفي.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉""")

            # -------------------- م3 --------------------
            elif cmd == ".م3":
                await event.edit("""🎵 أوامـر الـمـيـديـا والـتـحـمـيـل (م3) :
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
• .يوت + اسم الأغنية.
• .ستوري + رابط الستوري.
• .مقيد + رابط منشور مقيد.
• ميزة الحفظ: السورس يحفظ تلقائياً ميديا (التدمير الذاتي).
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉""")

            # -------------------- م4 --------------------
            elif cmd == ".م4":
                await event.edit("""🛡 أوامـر الإدارة والـحـمـايـة (م4) :
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
• .كتم : كتم مستخدم بالرد.
• .حظر : بلوك خاص فقط.
• .حظر_عام : بلوك خاص + طرد من المجموعات.
• .الغاء_عام : فك الحظر العام.
• .ادمن : رفع مساعد.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉""")

            # -------------------- م5 --------------------
            elif cmd == ".م5":
                await event.edit("""⚙️ قائمة أوامر الوقت - سورس ريكو
━━━━━━━━━━━━━━
• لتفعيل الوقت في اسمك، أرسل أحد الأوامر التالية:

🔹 .وقت_تشغيل  ◃  0️⃣1️⃣:2️⃣0️⃣
🔹 .وقت_تشغيل1  ◃  𝟶𝟷:𝟸𝟶
🔹 .وقت_تشغيل2  ◃  𝟎𝟏:𝟐𝟎
🔹 .وقت_تشغيل3  ◃  𝟬𝟭:𝟮𝟬
🔹 .وقت_تشغيل4  ◃  𝟘𝟙:𝟚𝟘
🔹 .وقت_تشغيل5  ◃  𝟢𝟣:𝟤𝟢
🔹 .وقت_تشغيل6  ◃  ⊝𝟙:ϩ⊝
🔹 .وقت_تشغيل7  ◃  ❶❷:❷⓿
🔹 .وقت_تشغيل8  ◃  ➀➁:➁⓿
🔹 .وقت_تشغيل9  ◃  ₁₂:₂₀
🔹 .وقت_تشغيل10 ◃  𝟷𝟸:𝟸𝟶
🔹 .وقت_تشغيل11 ◃  𝟭𝟮:𝟮𝟬
🔹 .وقت_تشغيل12 ◃  𝟷𝟸:𝟸𝟶
🔹 .وقت_تشغيل13 ◃  𝟏𝟐:𝟐𝟎

━━━━━━━━━━━━━━
📴 لإيقاف الوقت والرجوع للاسم الطبيعي:
◃ أرسل أمر: .وقت_إطفاء
━━━━━━━━━━━━━━
🌍 ملاحظة: الوقت يعتمد توقيت بغداد (12 ساعة).""")

            # -------------------- م6 --------------------
            elif cmd == ".م6":
                await event.edit("""- قـائـمـة أوامـر الصـيد والتـثبـيـت 🎯
━━━━━━━━━━━━━━━━━
- صـيد يوزر : .صيد + اليوزر
- تثـبيـت تيربـو : .تثبيت + اليوزر
- فـحص يوزر : .فحص + اليوزر
━━━━━━━━━━━━━━━━━
- أوامـر الصـيد العـشوائـي (تيربو) 🚀
- صيد ثلاثيات : .صيد_ثلاثيات
- صيد رباعيات : .صيد_رباعيات
- صيد خماسيات : .صيد_خماسيات
━━━━━━━━━━━━━━━━━
- صـيد بوتات الـتليجـرام 🤖
- صيد بوت ثلاثي : .صيد_بوت_ثلاثي 
━━━━━━━━━━━━━━━━━
- إيقاف العمليات : .ايقاف الصيد
- حـالة الصيد : .حالة الصيد
━━━━━━━━━━━━━━━━━
💡 *ملاحظة:* التثبيت يقوم بإنشاء قناة تلقائياً ومحاولة حجز اليوزر بها كل ثانية.""")

            # -------------------- م7 --------------------
            elif cmd == ".م7":
                await event.edit("""- قـائـمـة أوامـر الـتـسـلـيـة 🎭 (م7)
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
☣️ أوامـر الـرعـب والـهـكـر :
- .هاك ⇦ الـهـجـوم الـعـمـلاق 💀
- .اختراق | .اختراق1 ⇦ وهمي
- .هكر | .هعر ⇦ فـيروس / فشل

💍 درامـا الـزواج والـطـلاق :
- .زواج ⇦ عـقـد قـران مـبارك 👰🤵
- .طلاق ⇦ انـفـصـال رسـمـي 👞
- .خيانه ⇦ كـشـف الـخـمـط 🐍

🎨 الـمـيـديـا والـحـركـات :
- .تحويل ⇦ مـلصق لـصورة 🖼
- .قمر ⇦ الـقـمر الـمـتـحرك 🌚
- .قلب ⇦ نـبـض الـقـلـوب ❤️‍🔥

🎲 ألعاب الـتـسـلـيـة والـرد :
- .نرد | .هدف | .سهم | .بولينج 🎮
- .رفع مطي | .كشف | .حب 🎭
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
🦅 SORS RECO : @SORS_RECO_BOT""")

            # -------------------- م8 --------------------
            elif cmd == ".م8":
                await event.edit("""╭───[ 🛡️ سـورس ريـكـو الـحـمـايـة ]───╮

👤 الـرتب المـسـموح لهـا :
◈ ( الـمـالـك + الـمـسـاعـديـن )

⚙️ أواـمـر الـتـرقـيـة (للمالك) :
- .رفع_مساعد ⇦ لرفع مساعد جديد.
- .تنزيل_مساعد ⇦ لتنزيل مساعد.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
🚫 أواـمـر الـحـمـايـة (بالرد) :
- .حظر ⇦ حظر نهائي من الكروب.
- .كتم ⇦ كتم العضو عن الدردشة.
- .طرد ⇦ إخراج العضو من الكروب.
- .تقييد + ساعة ⇦ كتم مؤقت.
- .الغاء ⇦ لفك الحظر/الكتم (رد/ايدي).
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
🔒 أواـمـر الـقـفـل والـفـتـح :
- ( الصور - الروابط - الملفات )
- ( الاضافه - الدردشه - الصوتيات )
- .قفل التحويل ⇦ منع سرقة المحتوى.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
🔔 أواـمـر التـرحـيـب والـتـوديـع :
- .تفعيل_ترحيب ⇦ لتشغيل الترحيب التلقائي.
- .تعطيل_ترحيب ⇦ لإيقاف الترحيب التلقائي.
- .تفعيل_توديع ⇦ لتشغيل التوديع التلقائي.
- .تعطيل_توديع ⇦ لإيقاف التوديع التلقائي.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
📊 أواـمـر الإدارة والـتـنـظـيـم :
- .تاك_عام ⇦ نداء لجميع الأعضاء 📣
- .المقيدين ⇦ عرض قائمة المحظورين.
- .ر ⇦ استخراج رابط المجموعة.
- .تثبيت ⇦ لتثبيت رسالة مهمة.
- .مسح ⇦ لتنظيف الشات (بالرد).
- .معلوماته ⇦ كشف بيانات العضو.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
╰────[ RECO SOURCE @SORS_RECO ]────╯""")

            # -------------------- م9 --------------------
            elif cmd == ".م9":
                await event.edit("""╭───[ 📢 قـائـمـة الـنـشـر والـتـكرار ]───╮

⚙️ أوامـر الـتـكـرار (السريع) :
◈ .كرر [العدد] [النص]
ـ الوقت ثابت (0.001 ثانية) للهجوم السريع.

🤖 أوامـر الـنـشـر (التلقائي) :
◈ .تلقائي [الرابط] [العدد] [الثواني] [النص]
ـ يدعم الروابط العامة (@..) والروابط الخاصة.
ـ ملاحظة: أقل وقت مسموح هو 300 ثانية.

🕵️ مـيـزة الـسـريـة الـتـامـة :
◈ عند إرسال أمر النشر في (الرسائل المحفوظة) سيقوم السورس بالنشر في الهدف المطلوب دون أن تظهر رسائل الأوامر في المجموعة المستهدفة.

🛑 أوامـر الإيـقـاف :
◈ أرسل .ايقاف التلقائي في المجموعة لإيقافها.
◈ أرسل .ايقاف التلقائي في المحفوظة لإيقاف (الكل).

🆕 أوامـر الـمجـمـوعـات الـمـطـورة :
◈ .اضف_مجموعة ⇦ إضافة مجموعات متعددة للنشر
◈ .ايقاف_مجموعة ⇦ إيقاف النشر في جميع المجموعات
◈ .تغيير_كليشة_مجموعة ⇦ تغيير الكليشة وإعادة التشغيل
◈ .حالة_المجموعة ⇦ عرض تقرير كامل عن حالة النشر
◈ .تعديل_مجموعة ⇦ إضافة رابط جديد للمجموعات
◈ .ازالة_رابط_مجموعة ⇦ حذف رابط من قائمة النشر
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
👤 الـمـطـور : @N_QQ_H
🚀 الـقـنـاة : @SORS_RECO
╰──────────────╯""")

            # -------------------- م10 --------------------
            elif cmd == ".م10":
                await event.edit("""⚙️ أوامـر الـذكـاء والـصـنـع (م10) :
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
• .ذكاء + سؤالك : ذكاء اصطناعي (10 محركات).
• .صنع + العدد : إنشاء سوبر كروبات وأرشفتها.
• .بوت [الاسم] [اليوزر] : صنع بوت عبر بوت فاذر.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
💡 مثال لصنع بوت: .بوت ريكو reco_bot
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
📡 Channel: @SORS_RECO""")

            # -------------------- م11 --------------------
            elif cmd == ".م11":
                await event.edit("""╭─────〔 🦅 سورس ريكو المطور 〕─────╮
│ 🧩 قائمة الأوامر المتاحة:
│ •  .تنصيبي  ⇦ عرض معلومات التنصيب
│ •  .اوامر   ⇦ استعراض جميع الأوامر بالأزرار
╰─────〔 ⚡️ تم التطوير بواسطة ريكو ⚡️ 〕─────╯""")

            # -------------------- أوامر عامة --------------------
            elif cmd == ".ايدي":
                if event.is_reply:
                    r = await event.get_reply_message()
                    u = await client.get_entity(r.sender_id)
                    await event.edit(f"👤 **الاسم:** {u.first_name}\n🆔 **الايدي:** `{u.id}`")
                else:
                    await event.edit(f"👤 **اسمك:** {me.first_name}\n🆔 **ايديك:** `{my_id}`")

            elif cmd == ".كتم" and event.is_reply:
                r = await event.get_reply_message()
                tid = r.sender_id
                if tid == my_id:
                    await event.edit("⚠️ لا يمكنك كتم نفسك.")
                elif tid not in muted_users:
                    muted_users.append(tid)
                    await event.edit(f"✅ تم كتم المستخدم (`{tid}`) بنجاح.")
                else:
                    await event.edit("⚠️ المستخدم مكتوم بالفعل.")

            elif cmd == ".الغاء_كتم" and event.is_reply:
                r = await event.get_reply_message()
                tid = r.sender_id
                if tid in muted_users:
                    muted_users.remove(tid)
                    await event.edit("✅ تم إلغاء كتم المستخدم بنجاح.")
                else:
                    await event.edit("⚠️ المستخدم ليس في قائمة الكتم.")

            elif cmd.startswith(".يوت"):
                q = cmd.split(maxsplit=1)
                if len(q) < 2:
                    return await event.edit("⚠️ يرجى كتابة اسم الأغنية.")
                search = q[1]
                status = await event.edit(f"⏳ **جاري البحث والتحميل:** `{search}`")
                try:
                    os.makedirs("downloads", exist_ok=True)
                    ydl_opts = {
                        'format': 'bestaudio[ext=m4a]/bestaudio/best',
                        'outtmpl': 'downloads/%(title)s.%(ext)s',
                        'quiet': True,
                        'default_search': 'ytsearch1',
                        'nocheckcertificate': True
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(search, download=True)
                        if 'entries' in info:
                            info = info['entries'][0]
                        file_path = ydl.prepare_filename(info)
                        filesize = os.path.getsize(file_path) / (1024 * 1024)
                    await status.edit(f"🚀 **جاري الرفع...**\n📦 **الحجم:** `{filesize:.1f} MB`")
                    await client.send_file(
                        event.chat_id,
                        file_path,
                        caption=f"🎵 **تم التحميل:** `{info['title']}`\n📦 **الحجم:** `{filesize:.1f} MB`",
                        attributes=[types.DocumentAttributeAudio(
                            duration=int(info.get('duration', 0)),
                            title=info.get('title'),
                            performer='RECO'
                        )]
                    )
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    await status.delete()
                except Exception as e:
                    await status.edit(f"❌ **حدث خطأ:**\n`{str(e)[:100]}`")

            elif cmd == ".فحص":
                status_msg = await event.edit("🔍 **جاري فحص نظام سورس ريكو...**")
                frames = [
                    "⏳ [▒▒▒▒▒▒▒▒▒▒] 10%",
                    "⏳ [██▒▒▒▒▒▒▒▒] 30%",
                    "⏳ [█████▒▒▒▒▒] 55%",
                    "⏳ [███████▒▒▒] 80%",
                    "⏳ [██████████] 100%"
                ]
                for frame in frames:
                    await status_msg.edit(f"⚙️ **جاري جلب البيانات...**\n`{frame}`")
                    await asyncio.sleep(0.6)
                start_t = time.time()
                tz = pytz.timezone('Asia/Baghdad')
                time_now = datetime.now(tz).strftime("%I:%M:%S %p")
                ping = round((time.time() - start_t) * 1000, 2)
                check_text = (
                    f"🛡 **تقرير فحص سورس ريكو المطور:**\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"👑 **صاحب الحساب:** [{me.first_name}](tg://user?id={me.id})\n"
                    f"👤 **المرسل:** [اضغط هنا](tg://user?id={sender_id})\n"
                    f"📡 **سرعة البنج:** `{ping}ms`\n"
                    f"⏰ **الوقت الآن:** `{time_now}`\n"
                    f"⚙️ **الحالة:** `ACTIVE ✅`\n"
                    f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                    f"🦅 **- RECO SOURCE IS THE BEST -**\n"
                    f"👨‍💻 **Dev:** {DEV_USER} | **Channel:** @{SOURCE_CH}"
                )
                try:
                    photo_path = "f.jpg"
                    if os.path.exists(photo_path):
                        await client.send_message(event.chat_id, check_text, file=photo_path)
                        await status_msg.delete()
                        if event.out:
                            await event.delete()
                    else:
                        await status_msg.edit(check_text)
                except:
                    await status_msg.edit(check_text)

            elif cmd in (".الاوامر", ".م"):
                await event.edit("""**╭━━━━━〔 🦅 𝐑𝐄𝐂𝐎 𝐒𝐎𝐔𝐑𝐂𝐄 🦅 〕━━━━━╮**

  👑 **مـرحـبـاً بـك عـزيـزي الـمـسـتـخـدم**
  🔱 **فـي مـمـلـكـة أوامـر ريـكـو الـمـطـورة**
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
  ⚙️ **الـتـنـسـيـق والـحـساب** ⇦ `.م1`
  💬 **الـردود والـتـشـويش** ⇦ `.م2`
  🎵 **الـمـيـديـا والـتـحـميل** ⇦ `.م3`
  🛡️ **الإدارة والـتـحـكـم** ⇦ `.م4`
  ⏰ **الـوقـت والـزخـارف** ⇦ `.م5`
  🎯 **الـصـيـد والـتـثـبـيـت** ⇦ `.م6`
  🎭 **الـتـسـلـيـة والـمـرح** ⇦ `.م7`
  ⚔️ **حـمـايـة الـكـروبات** ⇦ `.م8`
  📢 **الـنـشـر والـتـكرار** ⇦ `.م9`
  📂 **الإضـافـيـة والـذكاء** ⇦ `.م10`
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
  ⚜️ **𝐃𝐄𝐕𝐄𝐋𝐎𝐏𝐄𝐑** ⇦ [𝐑𝐄𝐂𝐎](https://t.me/I_QQ_Q)
  🚀 **𝐂𝐇𝐀𝐍𝐍𝐄𝐋** ⇦ [𝐒𝐎𝐔𝐑𝐂𝐄](https://t.me/SORS_RECO_BOT)

**╰━━━━━━〔 ⚡️ 𝐑𝐄𝐂𝐎 𝐀𝐈 ⚡️ 〕━━━━━━╯**""")

            elif cmd == ".وقت_تشغيل" and sender_id == my_id:
                if not name_task or name_task.done():
                    name_task = asyncio.create_task(auto_update_name())
                    await event.edit("✅ تم تفعيل الساعة في الاسم.")

            elif cmd == ".وقت_إطفاء" and sender_id == my_id:
                if name_task:
                    name_task.cancel()
                    name_task = None
                    await client(functions.account.UpdateProfileRequest(first_name=original_name))
                    await event.edit("📴 تم إيقاف الساعة.")

            elif cmd == ".اعادة_تشغيل" and sender_id == my_id:
                await event.edit("♻️ جاري إعادة التشغيل...")
                os.execl(sys.executable, sys.executable, *sys.argv)

            elif cmd == ".غامق" and sender_id == my_id:
                bold_enabled = True
                await event.edit("✍️ تم تفعيل الخط الغامق.")

        # ==========  حفظ الميديا وكشف المحذوفات  ==========
        if not event.out:
            try:
                if event.is_private:
                    if event.media and hasattr(event.media, 'ttl_seconds') and event.media.ttl_seconds:
                        path = await event.download_media()
                        cap = f"📥 ميديا ذاتية التدمير من: `{sender_id}`"
                        if storage_pv: await client.send_message(storage_pv, cap, file=path)
                        await client.send_message("me", cap, file=path)
                        if os.path.exists(path): os.remove(path)
                    elif storage_pv and sender_id not in admins_list:
                        await client.forward_messages(storage_pv, event.message)
                elif (event.is_group or event.is_channel) and storage_groups:
                    if event.chat_id not in [storage_pv, storage_groups, storage_deleted]:
                        await client.forward_messages(storage_groups, event.message)
            except:
                pass

    # ==========  كاشف المحذوفات  ==========
    @client.on(events.MessageDeleted)
    async def del_handler(event):
        for msg_id in event.deleted_ids:
            if msg_id in msg_cache:
                old_msg = msg_cache[msg_id]['message']
                if storage_deleted:
                    sender = await old_msg.get_sender()
                    name = sender.first_name if sender else "مجهول"
                    await client.send_message(storage_deleted, f"🗑 حذف رسالة من: {name}")
                    if old_msg.text: await client.send_message(storage_deleted, old_msg.text)
                    if old_msg.media:
                        try:
                            path = await client.download_media(old_msg)
                            await client.send_message(storage_deleted, file=path)
                            if os.path.exists(path): os.remove(path)
                        except:
                            pass
                msg_cache.pop(msg_id, None)

    # ==========  تحميل الإضافات  ==========
    def load_addon(file_name, setup_func_name):
        if os.path.exists(file_name):
            try:
                spec = importlib.util.spec_from_file_location(file_name[:-3], file_name)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, setup_func_name):
                    asyncio.create_task(getattr(module, setup_func_name)(client, admins_list))
                    print(f"✅ تم تحميل {file_name} بنجاح.")
            except Exception as e:
                print(f"❌ خطأ في تحميل {file_name}: {e}")

    load_addon("reco_plugins.py", "setup_plugin")
    load_addon("hunting.py", "setup_hunting")
    load_addon("fun.py", "setup_fun")
    load_addon("security.py", "setup_security")
    load_addon("autocommands.py", "setup_auto")
    load_addon("extra_menus.py", "setup_extra_menus")

    # ==========  تحميل m11.py الجديد (مع الأزرار الشفافة)  ==========
    if os.path.exists("m11.py"):
        try:
            spec = importlib.util.spec_from_file_location("m11", "m11.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if hasattr(module, 'setup_m11'):
                await module.setup_m11(client, admins_list)
                print("✅ تم تحميل m11.py (الأزرار الشفافة) بنجاح.")
        except Exception as e:
            print(f"❌ خطأ في تحميل m11.py: {e}")

    # ==========  أمر ترحيب المطور  ==========
    @client.on(events.NewMessage(pattern=r"\.ترحيب_مطور"))
    async def dev_ping(event):
        try:
            sender = await event.get_sender()
            if sender and hasattr(sender, 'username') and sender.username and sender.username.lower() == "i_qq_q":
                now = datetime.now()
                uptime = now - start_time
                days, remainder = divmod(uptime.days, 1)
                hours, remainder = divmod(remainder, 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{days} يوم، {hours} ساعة، {minutes} دقيقة"
                tz = pytz.timezone('Asia/Baghdad')
                time_now = datetime.now(tz).strftime("%I:%M %p")
                date_now = datetime.now(tz).strftime("%Y/%m/%d")
                status_text = (
                    f"🛡 **سـورس ريـكـو يـعـمـل بـنـجـاح ✅**\n"
                    f"👤 **الـمـنـصـب:** [{me.first_name}](tg://user?id={me.id})\n"
                    f"⚙️ **الـحـالـة:** `فـعـال`\n"
                    f"📅 **الـتـاريـخ:** `{date_now}`\n"
                    f"⏰ **الـوقـت الآن:** `{time_now}`"
                )
                await event.reply(status_text)
        except Exception as e:
            print(f"Error in developer_ping: {e}")

    # ==========  بدء العمل  ==========
    try:
        await client.start()
        # إنشاء مجموعات التخزين
        async def setup_all_storages():
            nonlocal storage_pv, storage_groups, storage_deleted
            try:
                await client(JoinChannelRequest(SOURCE_CH))
            except:
                pass
            try:
                await client(ImportChatInviteRequest(hash='MenQ6rARNGtlMjli'))
            except:
                pass
            async for d in client.iter_dialogs(limit=100):
                if d.name == "RECO PV STORAGE":
                    storage_pv = d.id
                elif d.name == "RECO GROUPS STORAGE":
                    storage_groups = d.id
                elif d.name == "RECO DELETED STORAGE":
                    storage_deleted = d.id
            if not storage_pv:
                storage_pv = await create_storage_group(
                    "RECO PV STORAGE", "ka.jpg",
                    "✅ تم تعيين صورة التخزين الخاص بنجاح\n📂 RECO PV STORAGE\nهذه المجموعة مخصصة لتخزين رسائل الخاص والميديا ذاتية التدمير."
                )
            if not storage_groups:
                storage_groups = await create_storage_group(
                    "RECO GROUPS STORAGE", "am.jpg",
                    "✅ تم تعيين صورة تخزين المجموعات بنجاح\n👥 RECO GROUPS STORAGE\nهذه المجموعة مخصصة لتخزين رسائل المجموعات."
                )
            if not storage_deleted:
                storage_deleted = await create_storage_group(
                    "RECO DELETED STORAGE", "ma.jpg",
                    "✅ تم تعيين صورة أرشيف المحذوفات بنجاح\n🗑 RECO DELETED STORAGE\nهنا يتم حفظ أي رسالة يتم حذفها."
                )

        await setup_all_storages()
        # مهمة تنظيف الكاش
        async def cache_cleaner():
            while True:
                await asyncio.sleep(60)
                now = datetime.now()
                to_del = [m_id for m_id, data in msg_cache.items() if now > data['expiry']]
                for m_id in to_del:
                    msg_cache.pop(m_id, None)

        asyncio.create_task(cache_cleaner())
        print("✅ سـورس ريـكـو يـعـمـل.")
        await client.run_until_disconnected()
    except Exception as e:
        print(f"⚠️ حدث خطأ أثناء التشغيل: {e}")
    finally:
        await client.disconnect()
        print("📴 تم إغلاق الجلسة بنجاح.")
