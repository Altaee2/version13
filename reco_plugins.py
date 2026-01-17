#pylint:disable=E0401
from telethon import events, functions, types
import asyncio
import json
import os
import sys
import datetime
import asyncio
from telethon import functions, types, events
import pytz, re, asyncio
from datetime import datetime
# ملفات التخزين
RESP_FILE = "responses.json"
SETTINGS_FILE = "reco_settings.json"
user_states = {}

# دالة تحميل الردود
def load_data(file_name):
    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as f:
            try: return json.load(f)
            except: return {}
    return {}

# دالة حفظ البيانات
def save_data(file_name, data):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

reco_responses = load_data(RESP_FILE)
reco_settings = load_data(SETTINGS_FILE)

async def setup_plugin(client, admins_list, muted_users):

    @client.on(events.NewMessage)
    async def reco_plugins_handler(event):
        global reco_responses, user_states, reco_settings
        cmd = event.raw_text
        sender_id = event.sender_id
        me = await client.get_me()
        my_id = me.id
        is_admin = (sender_id == my_id) or (sender_id in admins_list)

        # 1. وضع إضافة الرد
        if is_admin and event.out and sender_id in user_states:
            word_to_save = user_states[sender_id]
            reco_responses[word_to_save] = cmd
            save_data(RESP_FILE, reco_responses)
            del user_states[sender_id]
            await event.edit(f"✅ **تم حفظ الرد بنجاح!**\n🔹 الكلمة: `{word_to_save}`\n🔸 الجواب: `{cmd}`")
            return

        # 2. تنفيذ الردود التلقائية
        if not event.out and cmd in reco_responses:
            await event.reply(reco_responses[cmd])

        # 3. أوامر الإدارة
        if is_admin and event.out:
            
            # أمر التشويش
            if cmd.startswith(".تشويش "):
                text_to_spoiler = cmd[7:].strip()
                if text_to_spoiler:
                    await event.edit(text_to_spoiler, formatting_entities=[types.MessageEntitySpoiler(offset=0, length=len(text_to_spoiler))])

            # أمر الرد
            elif cmd == ".رد":
                if not event.is_reply:
                    return await event.edit("⚠️ **يجب الرد على الرسالة!**")
                reply_msg = await event.get_reply_message()
                user_states[sender_id] = reply_msg.text
                await event.edit(f"⏳ **تم استلام الكلمة:** `{reply_msg.text}`\n💬 **أرسل الآن الجواب لحفظه.**")

            # أمر إعادة التشغيل والنسخ الاحتياطي
            elif cmd == ".اعادة_تشغيل":
                await event.edit("🔄 **جاري إنشاء النسخة الاحتياطية وإعادة التشغيل...**")
                try:
                    backup_data = {
                        "phone": me.phone,
                        "name": me.first_name,
                        "id": me.id,
                        "session": client.session.save(),
                        "date": str(datetime.datetime.now()),
                        "responses": reco_responses
                    }
                    backup_file = "reco_backup.json"
                    save_data(backup_file, backup_data)
                    
                    # إرسال النسخة للرسائل المحفوظة
                    await client.send_file("me", backup_file, caption="📦 **نسخة احتياطية كاملة لبيانات السورس**")
                    
                    os.remove(backup_file) # حذف للأمان
                    await event.edit("✅ **تم الحفظ. السورس سيعيد التشغيل الآن.**")
                    
                    # إعادة التشغيل الفوري
                    os.execl(sys.executable, sys.executable, *sys.argv)
                except Exception as e:
                    await event.edit(f"❌ خطأ: {str(e)}")

            # عرض الردود
            elif cmd == ".ردودي":
                if not reco_responses: return await event.edit("📭 لا توجد ردود.")
                msg = "📋 **قائمة الردود:**\n\n"
                for word, resp in reco_responses.items(): msg += f"🔹 `{word}` ⬅️ `{resp}`\n"
                await event.edit(msg)

            # حذف رد
            elif cmd == ".حذف_رد":
                if not event.is_reply: return await event.edit("⚠️ رد على الكلمة المراد حذف ردها.")
                rm = await event.get_reply_message()
                if rm.text in reco_responses:
                    del reco_responses[rm.text]
                    save_data(RESP_FILE, reco_responses)
                    await event.edit(f"🗑 تم حذف الرد الخاص بـ `{rm.text}`")
                else: await event.edit("⚠️ الكلمة غير موجودة.")
        # --- أوامر شرح الأقسام (تضاف في reco_plugins) ---
        # --- بداية قسم أوامر المساعدة (م1 - م5) ---
        if cmd == ".م1":
            await event.edit(
                "⚙️ **أوامـر الـحـسـاب والـتـنسـيق (م1) :**\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "• `.ايدي` : كشف معلومات الحساب.\n"
                "• `.انتحال` : نسخ حساب (رد/يوزر).\n"
                "• `.ايقاف_انتحال` : العودة لبياناتك الأصلية.\n"
                "• `.مسح` : مسح الخاص طرفين / مغادرة الكروبات.\n"
                "• `.اعادة_تشغيل` : تحديث السورس.\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉"
            )


        elif cmd == ".م2":
            await event.edit(
                "💬 **أوامـر الـردود والـتـشـويـش (م2) :**\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "• `.رد` : إضافة رد جديد.\n"
                "• `.حذف_رد` : حذف رد معين.\n"
                "• `.ردودي` : عرض قائمة الردود.\n"
                "• `.تشويش` : إرسال نص مخفي.\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉"
            )

        elif cmd == ".م3":
            await event.edit(
                "🎵 **أوامـر الـمـيـديـا والـتـحـمـيـل (م3) :**\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "• `.يوت` + اسم الأغنية.\n"
                "• `.ستوري` + رابط الستوري.\n"
                "• `.مقيد` + رابط منشور مقيد.\n"
                "• **ميزة الحفظ:** السورس يحفظ تلقائياً ميديا (التدمير الذاتي).\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉"
            )

        elif cmd == ".م4":
            await event.edit(
                "🛡 **أوامـر الإدارة والـحـمـايـة (م4) :**\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "• `.كتم` : كتم مستخدم بالرد.\n"
                "• `.حظر` : بلوك خاص فقط.\n"
                "• `.حظر_عام` : بلوك خاص + طرد من المجموعات.\n"
                "• `.الغاء_عام` : فك الحظر العام.\n"
                "• `.ادمن` : رفع مساعد.\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉"
            )

        elif cmd == ".م5":
            styles_list = {
                "0": "0️⃣1️⃣:2️⃣0️⃣", "1": "𝟶𝟷:𝟸𝟶", "2": "𝟎𝟏:𝟐𝟎", "3": "𝟬𝟭:𝟮𝟬",
                "4": "𝟘𝟙:𝟚𝟘", "5": "𝟢𝟣:𝟤𝟢", "6": "⊝𝟙:ϩ⊝", "7": "❶❷:❷⓿",
                "8": "➀➁:➁⓿", "9": "₁₂:₂₀", "10": "𝟷𝟸:𝟸𝟶", "11": "𝟭𝟮:𝟮𝟬",
                "12": "𝟷𝟸:𝟸𝟶", "13": "𝟏𝟐:𝟐𝟎"
            }
            help_text = (
                "⚙️ **قائمة أوامر الوقت - سورس ريكو**\n"
                "━━━━━━━━━━━━━━\n"
                "• لتفعيل الوقت في اسمك، أرسل أحد الأوامر التالية:\n\n"
                f"🔹 `.وقت_تشغيل`  ◃  `{styles_list['0']}`\n"
                f"🔹 `.وقت_تشغيل1`  ◃  `{styles_list['1']}`\n"
                f"🔹 `.وقت_تشغيل2`  ◃  `{styles_list['2']}`\n"
                f"🔹 `.وقت_تشغيل3`  ◃  `{styles_list['3']}`\n"
                f"🔹 `.وقت_تشغيل4`  ◃  `{styles_list['4']}`\n"
                f"🔹 `.وقت_تشغيل5`  ◃  `{styles_list['5']}`\n"
                f"🔹 `.وقت_تشغيل6`  ◃  `{styles_list['6']}`\n"
                f"🔹 `.وقت_تشغيل7`  ◃  `{styles_list['7']}`\n"
                f"🔹 `.وقت_تشغيل8`  ◃  `{styles_list['8']}`\n"
                f"🔹 `.وقت_تشغيل9`  ◃  `{styles_list['9']}`\n"
                f"🔹 `.وقت_تشغيل10` ◃  `{styles_list['10']}`\n"
                f"🔹 `.وقت_تشغيل11` ◃  `{styles_list['11']}`\n"
                f"🔹 `.وقت_تشغيل12` ◃  `{styles_list['12']}`\n"
                f"🔹 `.وقت_تشغيل13` ◃  `{styles_list['13']}`\n\n"
                "━━━━━━━━━━━━━━\n"
                "📴 لإيقاف الوقت والرجوع للاسم الطبيعي:\n"
                "◃ أرسل أمر: `.وقت_إطفاء`\n"
                "━━━━━━━━━━━━━━\n"
                "🌍 **ملاحظة:** الوقت يعتمد توقيت بغداد (12 ساعة)."
            )
            await event.edit(help_text)
        # --- نهاية قسم أوامر المساعدة ---


        elif cmd == ".اوامر_كل":
            all_cmds = (
                "🌀 **قـائـمـة أوامـر سـورس ريـكـو الـكـاملـة :**\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "• `.ايدي` : كشف معلومات الحساب\n"
                "• `.انتحال` : نسخ حساب (رد/يوزر)\n"
                "• `.ايقاف_انتحال` : العودة لبياناتك الأصلية\n"
                "• `.مسح` : مسح الخاص طرفين والمغادرة\n"
                "• `.اعادة_تشغيل` : تحديث وتنظيف السورس\n"
                "• `.فحص` : فحص متاحية يوزر معين\n"
                "• `.رد` : إضافة رد جديد تلقائي\n"
                "• `.حذف_رد` : إزالة رد من القائمة\n"
                "• `.ردودي` : عرض كل الردود المضافة\n"
                "• `.تشويش` : إرسال نص بشكل مخفي\n"
                "• `.يوت` : تحميل صوتيات من اليوتيوب\n"
                "• `.ستوري` : تحميل ستوريات تليكرام\n"
                "• `.مقيد` : جلب منشورات القنوات المقيدة\n"
                "• `.حظر` : حظر المستخدم من المجموعه\n"
                "• `.كتم` : منع مستخدم من التحدث\n"
                "• `.طرد` : إخراج العضو من الكروب\n"
                "• `.تقييد` : كتم العضو لوقت محدد\n"
                "• `.حظر_عام` : طرد وحظر من كل الكروبات\n"
                "• `.رفع_مساعد` : رفع مستخدم كمساعد في السورس\n"
                "• `.تنزيل_مساعد` : تنزيل مساعد من السورس\n"
                "• `.وقت_تشغيل` : تفعيل الساعة (0-13)\n"
                "• `.وقت_إطفاء` : إيقاف الساعة والرجوع للاسم\n"
                "• `.كرر` : التكرار السريع جداً\n"
                "• `.تلقائي` : النشر التلقائي المبرمج\n"
                "• `.ايقاف النشر` : إيقاف مهام النشر\n"
                "• `.حالة النشر` : عرض حالة النشر الحالية\n"
                "• `.صيد_ثلاثيات` : صيد يوزرات ثلاثية\n"
                "• `.صيد_رباعيات` : صيد يوزرات رباعية\n"
                "• `.ايقاف الصيد` : إنهاء عمليات الصيد\n"
                "• `.حالة الصيد` : معرفة وضع الصيد الحالي\n"
                "• `.ريكو` : سؤال ذكاء اصطناعي Gemini\n"
                "• `.صنع` : إنشاء سوبر كروبات تلقائياً\n"
                "• `.هاك` : الهجوم العملاق (وهمي)\n"
                "• `.اختراق` : محاكاة اختراق وهمية\n"
                "• `.زواج` : عقد قران مبارك\n"
                "• `.طلاق` : انفصال رسمي\n"
                "• `.خيانه` : بلاغ خيانة عظمى\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "📡 **Channel:** @SORS_RECO"
            )
            await event.edit(all_cmds)



            # أمر رفع أدمن (تم تصحيح المسافات هنا)





        elif cmd == ".ادمن":
            await event.edit("🛠️ **هذا الأمر قيد البرمجة والتطوير حالياً..**\n⏳ سيتم تفعيله في التحديث القادم لسورس ريكو.")

        elif cmd == ".تنزيل":
            await event.edit("🛠️ **هذا الأمر قيد البرمجة والتطوير حالياً..**\n⏳ سيتم تفعيله في التحديث القادم لسورس ريكو.")


            # أمر الأيدي
        elif cmd == ".ايدي":
                if event.is_reply:
                    reply_msg = await event.get_reply_message()
                    target_id = reply_msg.sender_id
                    user = await client.get_entity(target_id)
                    id_text = (
                        f"👤 **الاسم:** {user.first_name}\n"
                        f"🆔 **الايدي:** `{target_id}`\n"
                        f"✨ **المعرف:** @{user.username if user.username else 'لا يوجد'}"
                    )
                else:
                    id_text = (
                        f"👤 **اسمك:** {me.first_name}\n"
                        f"🆔 **ايديك:** `{my_id}`\n"
                        f"📡 **الحالة:** متصل"
                    )
                await event.edit(id_text)
    # --- كود أوامر تغيير الوقت في الاسم (توقيت بغداد 12 ساعة) ---
    # --- نظام وقت الاسم (نمط الهيبة الملكي) لـ سورس ريكو ---
       # --- نظام وقت الاسم المطور (نمط الهيبة الملكي) لـ سورس ريكو ---
    
    
    if 'time_tasks' not in globals():
        global time_tasks
        time_tasks = {}

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.وقت_تشغيل(\d|1[0-3])$"))
    async def toggle_time_name(event):
        cmd_num = event.pattern_match.group(1)
        my_id = (await client.get_me()).id
        
        if my_id in time_tasks:
            time_tasks[my_id].cancel()
            del time_tasks[my_id]

        # 13 نمط ملكي (تم توحيد الفاصلة لتكون : دائمًا)
        fonts_map = {
            "1": {"0":"𝟶", "1":"𝟷", "2":"𝟸", "3":"𝟹", "4":"𝟺", "5":"𝟻", "6":"𝟼", "7":"𝟽", "8":"𝟾", "9":"𝟿"}, # الآلة الكاتبة
            "2": {"0":"𝟎", "1":"𝟏", "2":"𝟐", "3":"𝟑", "4":"𝟒", "5":"𝟓", "6":"𝟔", "7":"𝟕", "8":"𝟖", "9":"𝟗"}, # عريض
            "3": {"0":"𝟬", "1":"𝟭", "2":"𝟮", "3":"𝟯", "4":"𝟰", "5":"𝟱", "6":"𝟲", "7":"𝟳", "8":"𝟴", "9":"𝟵"}, # هيبة تقيل
            "4": {"0":"𝟘", "1":"𝟙", "2":"𝟚", "3":"𝟛", "4":"𝟜", "5":"𝟝", "6":"𝟞", "7":"𝟟", "8":"𝟠", "9":"𝟡"}, # مفرغ ناعم
            "5": {"0":"𝟢", "1":"𝟣", "2":"𝟤", "3":"𝟥", "4":"𝟦", "5":"𝟧", "6":"𝟨", "7":"𝟩", "8":"𝟪", "9":"𝟫"}, # مائل ناعم
            "6": {"0":"⊝", "1":"𝟙", "2":"ϩ", "3":"Ӡ", "4":"५", "5":"Ƽ", "6":"Ϭ", "7":"𝟽", "8":"𝟪", "9":"९"}, # فرعوني
            "7": {"0":"⓿", "1":"❶", "2":"❷", "3":"❸", "4":"❹", "5":"❺", "6":"❻", "7":"❼", "8":"❽", "9":"❾"}, # دوائر سوداء
            "8": {"0":"🄋", "1":"➀", "2":"➁", "3":"➂", "4":"➃", "5":"➄", "6":"➅", "7":"➆", "8":"➇", "9":"➈"}, # كلاسيك
            "9": {"0":"₀", "1":"₁", "2":"₂", "3":"₃", "4":"₄", "5":"₅", "6":"₆", "7":"₇", "8":"₈", "9":"₉"}, # نجوم
            "10": {"0":"𝒪", "1":"𝟷", "2":"𝟸", "3":"𝟹", "4":"𝟺", "5":"𝟻", "6":"𝟼", "7":"𝟽", "8":"𝟾", "9":"𝟿"}, # عمودي
            "11": {"0":"𝟬", "1":"𝟭", "2":"𝟮", "3":"𝟯", "4":"𝟰", "5":"𝟱", "6":"𝟲", "7":"𝟳", "8":"𝟴", "9":"𝟵"}, # سميك
            "12": {"0":"𝟶", "1":"𝟷", "2":"𝟸", "3":"𝟹", "4":"𝟺", "5":"𝟻", "6":"𝟼", "7":"𝟽", "8":"𝟾", "9":"𝟿"}, # فواصل
            "13": {"0":"𝟎", "1":"𝟏", "2":"𝟐", "3":"𝟑", "4":"𝟒", "5":"𝟓", "6":"𝟔", "7":"𝟕", "8":"𝟖", "9":"𝟗"}  # نمط ملكي
        }
        
        selected_font = fonts_map[cmd_num]
        tz = pytz.timezone('Asia/Baghdad')
        
        # دالة زخرفة الوقت مع الحفاظ على : ثابتة
        def style_time(t_str):
            res = ""
            for char in t_str:
                res += selected_font.get(char, char)
            return res

        me = await client.get_me()
        # تنظيف الاسم من الفاصلة | والوقت السابق
        clean_name = re.split(r' \| ', me.first_name)[0].strip()
        # تنظيف إضافي للرموز المنفردة
        clean_name = re.sub(r'(𝟶|𝟷|𝟸|𝟛|𝟜|𝟻|𝟼|𝟽|𝟾|𝟿|𝟎|𝟏|𝟐|𝟑|𝟒|𝟓|𝟔|𝟕|𝟖|𝟗|𝟬|𝟭|𝟮|𝟯|𝟰|𝟱|𝟲|𝟳|𝟴|𝟵|𝟘|𝟙|𝟚|𝟛|𝟜|𝟝|𝟞|𝟟|𝟠|𝟡|𝟢|𝟣|𝟤|𝟥|𝟦|𝟧|𝟨|𝟩|𝟪|𝟫|⊝|ϩ|Ӡ|५|Ƽ|Ϭ|९|⓿|❶|❷|❸|❹|❺|❻|❼|❽|❾|🄋|➀|➁|➂|➃|➄|➅|➆|➇|➈|₀|₁|₂|₃|₄|₅|₆|₇|₈|₉|𝒪).*', '', clean_name).strip()

        now_str = datetime.now(tz).strftime("%I:%M")
        example_time = style_time(now_str)
        
        await event.edit(f"👑 **تـم تـفـعـيـل نـمـط الـهـيـبـة ({cmd_num})**\n\n👤 **الشكل الجديد:**\n`{clean_name} | {example_time}`")

        async def update_name_loop():
            while True:
                try:
                    t_now = datetime.now(tz).strftime("%I:%M")
                    styled_t = style_time(t_now)
                    # التحديث بالصيغة المطلوبة: الاسم | الوقت
                    await client(functions.account.UpdateProfileRequest(first_name=f"{clean_name} | {styled_t}"))
                except: pass
                await asyncio.sleep(60)

        time_tasks[my_id] = asyncio.create_task(update_name_loop())

    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.وقت_إطفاء$"))
    async def disable_time_name(event):
        my_id = (await client.get_me()).id
        if my_id in time_tasks:
            time_tasks[my_id].cancel()
            del time_tasks[my_id]
            me = await client.get_me()
            clean_name = re.split(r' \| ', me.first_name)[0].strip()
            clean_name = re.sub(r'(𝟶|𝟷|𝟸|𝟛|𝟜|𝟻|𝟼|𝟽|𝟾|𝟿|𝟎|𝟏|𝟐|𝟑|𝟒|𝟓|𝟔|𝟕|𝟖|𝟗|𝟬|𝟭|𝟮|𝟯|𝟰|𝟱|𝟲|𝟳|𝟴|𝟵|𝟘|𝟙|𝟚|𝟛|𝟜|𝟝|𝟞|𝟟|𝟠|𝟡|𝟢|𝟣|𝟤|𝟥|𝟦|𝟧|𝟨|𝟩|𝟪|𝟫|⊝|ϩ|Ӡ|५|Ƽ|Ϭ|९|⓿|❶|❷|❸|❹|❺|❻|❼|❽|❾|🄋|➀|➁|➂|➃|➄|➅|➆|➇|➈|₀|₁|₂|₃|₄|₅|₆|₇|₈|₉|𝒪).*', '', clean_name).strip()
            await client(functions.account.UpdateProfileRequest(first_name=clean_name))
            await event.edit(f"📴 **تم إيقاف الوقت وإعادة اسمك الأصلي:**\n`{clean_name}`")


    # --- أمر تحميل ستوري تليجرام (كتم + مسح فوري) ---
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ستوري(?:\s+(.*))?$"))
    async def story_downloader(event):
        link = event.pattern_match.group(1)
        chat = event.chat_id
        download_bot = "@download_story_tele_bot"
        channels_to_join = ["alikwiq_News", "Mintors_tag_bots"]
        
        if not link:
            return await event.edit("⚠️ **يجب وضع رابط الستوري بعد الأمر!**")

        link = link.strip()
        await event.edit("⏳ **جاري العمل بسرية (أرشفة + جلب)...**")

        try:
            # 1. الانضمام للقنوات ونقلها للأرشيف فوراً للسرية
            for ch in channels_to_join:
                try:
                    # الانضمام
                    await client(functions.channels.JoinChannelRequest(channel=ch))
                    
                    # الحصول على كيان القناة (Entity)
                    entity = await client.get_input_entity(ch)
                    
                    # نقل القناة للأرشيف (folder_id=1 هو مجلد الأرشيف)
                    await client(functions.folders.EditPeerFoldersRequest(folder_peers=[
                        types.InputFolderPeer(peer=entity, folder_id=1)
                    ]))
                except Exception as e:
                    print(f"Error joining/archiving {ch}: {e}")

            # 2. إعدادات البوت (كتم وفك حظر)
            try:
                await client(functions.account.UpdateNotifySettingsRequest(
                    peer=download_bot,
                    settings=types.InputPeerNotifySettings(mute_until=2147483647)
                ))
                await client(functions.contacts.UnblockRequest(id=download_bot))
            except: pass

            # 3. التواصل مع البوت
            async with client.conversation(download_bot, timeout=60) as conv:
                await conv.send_message(link)
                
                found_media = False
                for _ in range(4):
                    response = await conv.get_response()
                    if response.media:
                        await client.send_file(chat, response.media, caption="✅ **تم تحميل الستوري بنجاح بواسطة ريكو**")
                        await event.delete()
                        found_media = True
                        break
                
                if not found_media:
                    await event.edit("❌ **فشل التحميل، تأكد من الرابط أو اشتراكك.**")

            # 4. تنظيف الآثار (مغادرة القنوات + حذف المحادثة + حظر البوت)
            for ch in channels_to_join:
                try: await client(functions.channels.LeaveChannelRequest(channel=ch))
                except: pass

            await client(functions.messages.DeleteHistoryRequest(
                peer=download_bot, 
                max_id=0, 
                just_clear=False, 
                revoke=True
            ))
            await client(functions.contacts.BlockRequest(id=download_bot))

        except Exception as e:
            # في حال الفشل نغادر القنوات فوراً ونحظر البوت للسرية
            for ch in channels_to_join:
                try: await client(functions.channels.LeaveChannelRequest(channel=ch))
                except: pass
            try: await client(functions.contacts.BlockRequest(id=download_bot))
            except: pass
            print(f"Global Error: {e}")
            await event.edit(f"⚠️ **حدث خطأ، تأكد من الرابط.**")







    # --- أمر حفظ المحتوى المقيد ---
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.مقيد(?:\s+(.*))?$"))
    async def save_restricted_pro(event):
        link = event.pattern_match.group(1)
        chat = event.chat_id
        
        if not link:
            return await event.edit("⚠️ **يجب وضع رابط المنشور المقيد بعد الأمر!**")

        await event.edit("⏳ **جاري فحص الرابط وجلب المحتوى...**")
        
        try:
            # 1. تحليل الرابط (عالمي أو خاص)
            if "t.me/c/" in link:
                # رابط قناة خاصة: t.me/c/123456789/10
                parts = link.split('/')
                real_id = int(parts[-2])
                msg_id = int(parts[-1].split('?')[0])
                # تحويل الايدي لصيغة تليثون الدولية
                peer = types.InputPeerChannel(real_id, 0) # سيحاول التليثون جلبها من الذاكرة
                # محاولة جلب الكيان الكامل
                try:
                    entity = await client.get_entity(real_id)
                except:
                    # إذا فشل، نستخدم الايدي المباشر (المفروض الحساب منضم)
                    entity = int(f"-100{real_id}")
            else:
                # رابط قناة عامة: t.me/username/10
                parts = link.split('/')
                entity = parts[-2]
                msg_id = int(parts[-1].split('?')[0])

            # 2. جلب الرسالة
            msg = await client.get_messages(entity, ids=msg_id)

            if not msg:
                return await event.edit("❌ **فشل الوصول للمنشور. تأكد أنك منضم للقناة.**")

            # 3. معالجة المحتوى وإرساله
            if msg.media:
                await event.edit("🔄 **جاري تحميل الميديا المقيدة (قد يستغرق وقتاً)...**")
                
                # استخدام دالة تحميل مباشرة وإرسالها
                # تليثون تسمح بإرسال الميديا مباشرة دون حفظها في ملف أحياناً للسرعة
                file = await client.download_media(msg)
                
                caption = msg.text if msg.text else ""
                await client.send_file(
                    chat, 
                    file, 
                    caption=f"✅ **تم فك القيد بنجاح**\n\n{caption}",
                    reply_to=event.reply_to_msg_id
                )
                
                # حذف الملف المؤقت بعد الإرسال
                if os.path.exists(file):
                    os.remove(file)
                    
                await event.delete()
            elif msg.text:
                # إذا كان نص فقط
                await client.send_message(chat, msg.text, reply_to=event.reply_to_msg_id)
                await event.delete()
            else:
                await event.edit("❌ **محتوى غير مدعوم أو فارغ.**")

        except Exception as e:
            error_msg = str(e)
            if "No user has" in error_msg:
                await event.edit("❌ **الحساب ليس عضواً في هذه القناة الخاصة.**")
            else:
                await event.edit(f"⚠️ **حدث خطأ أثناء الجلب:**\n`{error_msg}`")


    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.انتحال(?:\s+(.*))?$"))
    async def impersonate(event):
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        await event.edit("⏳ **جاري نسخ الحساب بالمليمتر...**")
        
        try:
            # 1. حفظ بياناتك الأصلية قبل التغيير
            if 'first_name' not in my_original_data:
                me = await client.get_me()
                full_me = await client(functions.users.GetFullUserRequest(me.id))
                my_original_data.update({
                    'first_name': me.first_name or "",
                    'last_name': me.last_name or "",
                    'about': full_me.full_user.about or "",
                    'emoji_status': me.emoji_status # حفظ الحالة الموسيقية/الايموجي
                })
                photos = await client.get_profile_photos('me')
                if photos:
                    my_original_data['photo'] = photos[0]

            # 2. جلب كيان الضحية
            if reply:
                user = await client.get_entity(reply.sender_id)
            elif args:
                user = await client.get_entity(args)
            else:
                return await event.edit("⚠️ **رد على شخص أو ضع معرفه!**")

            # جلب معلومات الضحية الكاملة (للبايو والحالة)
            full_user = await client(functions.users.GetFullUserRequest(user.id))
            
            # 3. نسخ الاسم (مطابقة تامة للأول والأخير)
            f_name = user.first_name or ""
            l_name = user.last_name or ""
            
            # 4. نسخ البايو والحالة (الموسيقى/الايموجي)
            u_about = full_user.full_user.about or ""
            u_emoji = user.emoji_status # جلب الحالة الموسيقية إذا كان بريميوم

            # تطبيق التغييرات على الاسم والبايو
            await client(functions.account.UpdateProfileRequest(
                first_name=f_name,
                last_name=l_name,
                about=u_about
            ))
            
            # تطبيق الحالة (الايموجي/الموسيقى)
            if u_emoji:
                try:
                    await client(functions.account.UpdateEmojiStatusRequest(emoji_status=u_emoji))
                except: pass # تجنب الخطأ إذا كان حسابك ليس بريميوم

            # 5. نسخ الصورة
            u_photos = await client.get_profile_photos(user.id)
            if u_photos:
                path = await client.download_media(u_photos[0])
                up_file = await client.upload_file(path)
                await client(functions.photos.UploadProfilePhotoRequest(file=up_file))
                if os.path.exists(path): os.remove(path)

            await event.edit(f"✅ **تم الانتحال بنجاح!**\n👤 **الاسم:** {f_name} {l_name}\n📝 **البايو:** {u_about}")

        except Exception as e:
            await event.edit(f"⚠️ **خطأ أثناء الانتحال:** `{str(e)}` ")




























    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.ايقاف_انتحال$"))
    async def restore_profile(event):
        if 'first_name' not in my_original_data:
            return await event.edit("⚠️ **لم يتم حفظ بياناتك الأصلية بعد!**")

        await event.edit("🔄 **جاري استعادة هويتك الأصلية...**")
        try:
            # استعادة الاسم والبايو
            await client(functions.account.UpdateProfileRequest(
                first_name=my_original_data['first_name'],
                last_name=my_original_data['last_name'],
                about=my_original_data['about']
            ))

            # استعادة الحالة (الايموجي/الموسيقى)
            if my_original_data.get('emoji_status'):
                try:
                    await client(functions.account.UpdateEmojiStatusRequest(emoji_status=my_original_data['emoji_status']))
                except: pass

            # استعادة الصورة
            if 'photo' in my_original_data:
                path = await client.download_media(my_original_data['photo'])
                up_file = await client.upload_file(path)
                await client(functions.photos.UploadProfilePhotoRequest(file=up_file))
                if os.path.exists(path): os.remove(path)

            await event.edit("✅ **عُدت لحسابك الطبيعي بنجاح!**")
            my_original_data.clear()
        except Exception as e:
            await event.edit(f"⚠️ **خطأ بالاستعادة:** `{str(e)}` ")











    # --- أمر الحظر (بلوك) ---
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.حظر(?:\s+(.*))?$"))
    async def block_user(event):
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        await event.edit("⏳ **جاري تنفيذ الحظر...**")
        
        try:
            # 1. تحديد الشخص (رد، يوزر، أو آيدي)
            if reply:
                user = await client.get_entity(reply.sender_id)
            elif args:
                user = await client.get_entity(args)
            else:
                return await event.edit("⚠️ **يجب الرد على مستخدم أو وضع معرفه لحظره!**")

            # 2. تنفيذ الحظر (Block)
            await client(functions.contacts.BlockRequest(id=user.id))
            
            # 3. مسح الرسالة أو تأكيد الحظر
            await event.edit(f"🚫 **تم حظر المستخدم بنجاح.**\n👤 **الاسم:** {user.first_name}\n🆔 **الأيدي:** `{user.id}`")
            
        except Exception as e:
            await event.edit(f"⚠️ **فشل الحظر:**\n`{str(e)}` ")

    # --- أمر إلغاء الحظر ---
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.الغاء_حظر(?:\s+(.*))?$"))
    async def unblock_user(event):
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        await event.edit("⏳ **جاري إلغاء الحظر...**")
        
        try:
            if reply:
                user = await client.get_entity(reply.sender_id)
            elif args:
                user = await client.get_entity(args)
            else:
                return await event.edit("⚠️ **رد على الشخص أو ضع معرفه لإلغاء الحظر.**")

            await client(functions.contacts.UnblockRequest(id=user.id))
            await event.edit(f"✅ **تم إلغاء حظر {user.first_name} بنجاح.**")
            
        except Exception as e:
            await event.edit(f"⚠️ **خطأ:** `{str(e)}` ")


    # --- أمر الحظر العام (خاص + مجموعات + قنوات) ---
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.حظر_عام(?:\s+(.*))?$"))
    async def global_block(event):
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        
        await event.edit("⏳ **جاري تنفيذ الحظر العام...**")
        
        try:
            # 1. تحديد الشخص
            if reply:
                user = await client.get_entity(reply.sender_id)
            elif args:
                user = await client.get_entity(args)
            else:
                return await event.edit("⚠️ **رد على الشخص أو ضع معرفه للحظر العام.**")

            user_id = user.id
            
            # 2. الحظر من الخاص (بلوك)
            await client(functions.contacts.BlockRequest(id=user_id))
            
            # 3. الطرد من المجموعات والقنوات المشتركة (التي أنت فيها أدمن)
            count = 0
            async for dialog in client.iter_dialogs():
                if dialog.is_group or dialog.is_channel:
                    try:
                        # محاولة طرد المستخدم من الدردشة
                        await client.edit_permissions(dialog.id, user_id, view_messages=False)
                        count += 1
                    except:
                        # يتخطى إذا لم تكن أدمن أو لا تملك صلاحية الطرد
                        continue

            await event.edit(
                f"🚫 **تم الحظر العام بنجاح!**\n"
                f"👤 **المستخدم:** {user.first_name}\n"
                f"🔒 **الحالة:** بلوك خاص + طرد من ({count}) مجموعة/قناة."
            )
            
        except Exception as e:
            await event.edit(f"⚠️ **فشل الحظر العام:**\n`{str(e)}` ")

    # --- أمر إلغاء الحظر العام ---
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.الغاء_عام(?:\s+(.*))?$"))
    async def unglobal_block(event):
        args = event.pattern_match.group(1)
        reply = await event.get_reply_message()
        await event.edit("🔄 **جاري إلغاء الحظر العام...**")
        
        try:
            if reply:
                user = await client.get_entity(reply.sender_id)
            elif args:
                user = await client.get_entity(args)
            else:
                return await event.edit("⚠️ **رد على الشخص أو ضع معرفه.**")

            # إلغاء البلوك من الخاص فقط (أما الكروبات فيجب دخوله يدوياً)
            await client(functions.contacts.UnblockRequest(id=user.id))
            await event.edit(f"✅ **تم إلغاء الحظر العام عن {user.first_name}.**")
            
        except Exception as e:
            await event.edit(f"⚠️ **خطأ:** `{str(e)}` ")


    # --- أمر المسح والمغادرة (الخاص والمجموعات) ---
    @client.on(events.NewMessage(outgoing=True, pattern=r"^\.مسح$"))
    async def clear_and_leave(event):
        chat = await event.get_chat()
        
        # رسالة الوداع اللطيفة
        farewell_msg = "🤍 **شكراً لكم على كل شيء، أتمنى لكم كل التوفيق. وداعاً!**"

        try:
            if event.is_private:
                # في الخاص: مسح المحادثة من الطرفين
                await event.edit("🗑 **جاري مسح المحادثة من الطرفين...**")
                await client(functions.messages.DeleteHistoryRequest(
                    peer=event.chat_id,
                    max_id=0,
                    just_clear=False,
                    revoke=True  # الحذف من الطرفين
                ))
            else:
                # في المجموعات والقنوات: إرسال وداع ثم المغادرة
                await event.edit(farewell_msg)
                await asyncio.sleep(2) # انتظار بسيط ليقرأوا الرسالة
                await client(functions.channels.LeaveChannelRequest(channel=event.chat_id))
                
        except Exception as e:
            await event.edit(f"⚠️ **حدث خطأ أثناء التنفيذ:**\n`{str(e)}` ")
        # --- كود أمر جميع الأوامر (سرد مباشر) ---
      