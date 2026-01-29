import asyncio
from datetime import datetime, timedelta
from telethon import events, functions, types
from telethon.tl.functions.channels import EditBannedRequest, GetParticipantsRequest
from telethon.tl.functions.messages import EditChatDefaultBannedRightsRequest
from telethon.tl.types import ChatBannedRights, ChannelParticipantsBanned

# تعريف قائمة المساعدين في الذاكرة لضمان استمراريتها خلال تشغيل السورس
if 'helpers_list' not in globals():
    globals()['helpers_list'] = []

# تهيئة متغيرات الترحيب والتوديع (مرة واحدة)
if 'welcome_enabled' not in globals():
    globals()['welcome_enabled'] = False   # افتراضياً مفعّل
if 'goodbye_enabled' not in globals():
    globals()['goodbye_enabled'] = False   # افتراضياً مفعّل

async def setup_security(client, admins_list):

    # --- 1. نظام الترحيب والمغادرة التلقائي ---
    @client.on(events.ChatAction)
    async def welcome_handler(event):
        # ترحيب عند انضمام عضو جديد
        if event.user_joined and globals()['welcome_enabled']:
            user = await event.get_user()
            await event.reply(f"اهلا بك يا [{user.first_name}](tg://user?id={user.id}) في المجموعة! نورتنا ✨")
        # توديع عند مغادرة عضو أو طرده
        elif (event.user_left or event.user_kicked) and globals()['goodbye_enabled']:
            await event.reply("سد الباب وراك.. لا يجينا الهوى! 🚪👋")

    # --- 2. معالج الأوامر الرئيسي (للمالك والمساعدين) ---
    @client.on(events.NewMessage())
    async def admin_handler(event):
        text = event.raw_text
        chat_id = event.chat_id
        sender_id = event.sender_id
        
        # جلب معلومات المالك (صاحب الحساب)
        me = await client.get_me()
        is_owner = (sender_id == me.id)
        is_helper = (sender_id in globals()['helpers_list'])

        # الأمان: إذا لم يكن المرسل مالكاً ولا مساعداً، يتم تجاهل الرسالة
        if not (is_owner or is_helper):
            return

        # دالة الاستجابة الذكية (تعديل لرسالة المالك ورد لرسالة المساعد)
        # هذا يمنع خطأ MessageAuthorRequiredError لأن المساعد لا يملك صلاحية تعديل رسالة غيره
        async def safe_respond(message_text):
            if is_owner:
                try:
                    # المالك يعدل رسالته الخاصة
                    return await event.edit(message_text)
                except Exception:
                    # في حال تعذر التعديل (مثل حذف الرسالة) يرسل رسالة جديدة
                    return await event.respond(message_text)
            else:
                # المساعد يرسل رداً جديداً على الأمر
                return await event.reply(message_text)

        # أوامر تشغيل/إيقاف الترحيب والتوديع (للمالك والمساعدين)
        if text == ".تفعيل_ترحيب":
            globals()['welcome_enabled'] = True
            await safe_respond("✅ تم **تشغيل** الترحيب التلقائي.")

        elif text == ".تعطيل_ترحيب":
            globals()['welcome_enabled'] = False
            await safe_respond("⏸️ تم **إيقاف** الترحيب التلقائي.")

        elif text == ".تفعيل_توديع":
            globals()['goodbye_enabled'] = True
            await safe_respond("✅ تم **تشغيل** التوديع التلقائي.")

        elif text == ".تعطيل_توديع":
            globals()['goodbye_enabled'] = False
            await safe_respond("⏸️ تم **إيقاف** التوديع التلقائي.")

        # --- أ) أوامر المالك فقط (الرفع والتنزيل) ---
        if is_owner:
            if text == ".رفع_مساعد" and event.is_reply:
                reply = await event.get_reply_message()
                r_id = reply.sender_id
                if r_id not in globals()['helpers_list']:
                    globals()['helpers_list'].append(r_id)
                    await safe_respond(f"✅ تم رفع المستخدم [{reply.sender.first_name}](tg://user?id={r_id}) كمساعد في السورس.")
                else:
                    await safe_respond("⚠️ هذا المستخدم مساعد بالفعل في النظام.")
                return

            elif text == ".تنزيل_مساعد" and event.is_reply:
                reply = await event.get_reply_message()
                r_id = reply.sender_id
                if r_id in globals()['helpers_list']:
                    globals()['helpers_list'].remove(r_id)
                    await safe_respond(f"✅ تم تنزيل المساعد [{reply.sender.first_name}](tg://user?id={r_id}) وإلغاء صلاحياته.")
                else:
                    await safe_respond("⚠️ هذا المستخدم ليس مساعداً ليتم تنزيله.")
                return

        # --- ب) أوامر الحماية والإدارة (للمالك والمساعدين) ---

        # 1. أمر التاك العام المطور
        if text == ".تاك_عام":
            if not event.is_group:
                return await safe_respond("⚠️ هذا الأمر يعمل داخل المجموعات فقط.")
            
            await safe_respond("⏳ جاري جمع الأعضاء وبدء المنشن العام...")
            try:
                all_participants = await client.get_participants(chat_id)
                mentions = [f"[{u.first_name}](tg://user?id={u.id})" for u in all_participants if not u.bot]
                
                # حذف رسالة الأمر الأصلية إذا كان المالك هو المرسل لجمالية المنظر
                if is_owner: 
                    await event.delete()
                
                chunk_size = 5 # تقسيم المنشن لرسائل صغيرة لتفادي حظر السبام
                for i in range(0, len(mentions), chunk_size):
                    chunk = mentions[i:i + chunk_size]
                    await client.send_message(chat_id, "📢 نداء لجميع الأعضاء:\n" + " | ".join(chunk))
                    await asyncio.sleep(1.5) # فاصل زمني ضروري للأمان
                return
            except Exception as e:
                await safe_respond(f"❌ حدث خطأ أثناء التاك: {str(e)}")

        # 2. أمر كشف المقيدين والمحظورين
        elif text == ".المقيدين":
            await safe_respond("⏳ جاري جلب قائمة المقيدين والمحظورين...")
            try:
                p_list = await client(GetParticipantsRequest(
                    channel=chat_id,
                    filter=ChannelParticipantsBanned(''),
                    offset=0, limit=100, hash=0
                ))
                if not p_list.participants:
                    return await safe_respond("✅ لا يوجد مقيدين أو محظورين في هذه المجموعة حالياً.")
                
                msg = "**📋 قائمة المقيدين والمحظورين :**\n‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                for p in p_list.users:
                    msg += f"👤 [{p.first_name}](tg://user?id={p.id}) | ايدي: `{p.id}`\n"
                await safe_respond(msg)
            except:
                await safe_respond("❌ فشل جلب القائمة، تأكد من صلاحياتي كأدمن.")

        # 3. أمر إلغاء القيود (بالرد أو بالآيدي)
        elif text.startswith(".الغاء"):
            target_id = None
            if event.is_reply:
                target_id = (await event.get_reply_message()).sender_id
            else:
                parts = text.split(" ")
                if len(parts) > 1:
                    try: 
                        target_id = int(parts[1])
                    except: 
                        return await safe_respond("⚠️ الآيدي يجب أن يكون رقماً صحيحاً.")
            
            if target_id:
                try:
                    await client(EditBannedRequest(chat_id, target_id, ChatBannedRights(until_date=None)))
                    await safe_respond(f"✅ تم إلغاء كافة القيود (حظر/كتم) عن المستخدم: `{target_id}`")
                except:
                    await safe_respond("❌ فشل إلغاء القيود، ربما لست أدمن.")
            else:
                await safe_respond("⚠️ يرجى الرد على الشخص أو كتابة آيديه بعد الأمر.")

        # 4. أوامر الحماية بالرد (طرد، حظر، كتم، تقييد)
        elif event.is_reply:
            reply_msg = await event.get_reply_message()
            target_user_id = reply_msg.sender_id
            
            if text == ".طرد":
                await client.kick_participant(chat_id, target_user_id)
                await safe_respond("🚷 تم طرد المستخدم من المجموعة بنجاح.")
            
            elif text == ".حظر":
                await client(EditBannedRequest(chat_id, target_user_id, ChatBannedRights(until_date=None, view_messages=True)))
                await safe_respond("🚫 تم حظر المستخدم نهائياً من المجموعة.")
            
            elif text == ".كتم":
                await client(EditBannedRequest(chat_id, target_user_id, ChatBannedRights(until_date=None, send_messages=True)))
                await safe_respond("🔇 تم كتم المستخدم بنجاح.")
            
            elif text.startswith(".تقييد "):
                try:
                    hours = int(text.split(" ")[1])
                    until_time = datetime.now() + timedelta(hours=hours)
                    await client(EditBannedRequest(chat_id, target_user_id, ChatBannedRights(until_date=until_time, send_messages=True)))
                    await safe_respond(f"⏳ تم تقييد العضو لمدة {hours} ساعة.")
                except:
                    await safe_respond("⚠️ استخدم: `.تقييد 1` بالرد على الشخص.")
            
            elif text == ".تثبيت":
                await client.pin_message(chat_id, reply_msg.id)
                await safe_respond("📌 تم تثبيت الرسالة بنجاح.")
            
            elif text == ".معلوماته":
                u = reply_msg.sender
                info_msg = f"**👤 الاسم:** {u.first_name}\n**🆔 الايدي:** `{u.id}`\n**📱 اليوزر:** @{u.username if u.username else 'لا يوجد'}"
                await safe_respond(info_msg)

        # 5. أوامر القفل والفتح المتطورة للمجموعة
        lock_map = {
            ".قفل الصور": ChatBannedRights(until_date=None, send_photos=True),
            ".فتح الصور": ChatBannedRights(until_date=None, send_photos=False),
            ".قفل الروابط": ChatBannedRights(until_date=None, embed_links=True),
            ".فتح الروابط": ChatBannedRights(until_date=None, embed_links=False),
            ".قفل الملفات": ChatBannedRights(until_date=None, send_docs=True),
            ".فتح الملفات": ChatBannedRights(until_date=None, send_docs=False),
            ".قفل الاضافه": ChatBannedRights(until_date=None, invite_users=True),
            ".فتح الاضافه": ChatBannedRights(until_date=None, invite_users=False),
            ".قفل الصوتيات": ChatBannedRights(until_date=None, send_media=True),
            ".فتح الصوتيات": ChatBannedRights(until_date=None, send_media=False),
            ".قفل الدردشه": ChatBannedRights(until_date=None, send_messages=True),
            ".فتح الدردشه": ChatBannedRights(until_date=None, send_messages=False),
        }
        
        if text in lock_map:
            try:
                await client(EditChatDefaultBannedRightsRequest(peer=chat_id, banned_rights=lock_map[text]))
                await safe_respond(f"✅ تم تنفيذ أمر {text} بنجاح.")
            except Exception:
                await safe_respond("❌ فشل القفل، تأكد من صلاحياتي كأدمن.")

        elif text == ".قفل التحويل":
            try:
                await client(functions.channels.ToggleNoForwardsRequest(channel=chat_id, enabled=True))
                await safe_respond("🚫 تم منع التحويل وحفظ المحتوى.")
            except Exception:
                await safe_respond("❌ يتطلب صلاحيات منشئ المجموعة.")

        elif text == ".ر":
            try:
                res = await client(functions.messages.ExportChatInviteRequest(peer=chat_id))
                await safe_respond(f"🔗 **رابط المجموعة:**\n{res.link}")
            except Exception:
                await safe_respond("❌ فشل استخراج الرابط.")

        elif text == ".مسح" and event.is_reply:
            reply_msg = await event.get_reply_message()
            msgs_to_delete = [m async for m in client.iter_messages(chat_id, min_id=reply_msg.id - 1)]
            await client.delete_messages(chat_id, msgs_to_delete)
            if is_owner: 
                await event.delete()

        # 6. قائمة المساعدة التفصيلية (.م8)
        elif text == ".م8":
            help_msg = """
**╭───[ 🛡️ سـورس ريـكـو الـحـمـايـة ]───╮**

**👤 الـرتب المـسـموح لهـا :**
◈ ( الـمـالـك + الـمـسـاعـديـن )

**⚙️ أواـمـر الـتـرقـيـة (للمالك) :**
- `.رفع_مساعد` ⇦ لرفع مساعد جديد.
- `.تنزيل_مساعد` ⇦ لتنزيل مساعد.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
**🚫 أواـمـر الـحـمـايـة (بالرد) :**
- `.حظر` ⇦ حظر نهائي من الكروب.
- `.كتم` ⇦ كتم العضو عن الدردشة.
- `.طرد` ⇦ إخراج العضو من الكروب.
- `.تقييد + ساعة` ⇦ كتم مؤقت.
- `.الغاء` ⇦ لفك الحظر/الكتم (رد/ايدي).
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
**🔒 أواـمـر الـقـفـل والـفـتـح :**
- ( الصور - الروابط - الملفات )
- ( الاضافه - الدردشه - الصوتيات )
- `.قفل التحويل` ⇦ منع سرقة المحتوى.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
**🔔 أواـمـر التـرحـيـب والـتـوديـع :**
- `.تفعيل_ترحيب` ⇦ لتشغيل الترحيب التلقائي.
- `.تعطيل_ترحيب` ⇦ لإيقاف الترحيب التلقائي.
- `.تفعيل_توديع` ⇦ لتشغيل التوديع التلقائي.
- `.تعطيل_توديع` ⇦ لإيقاف التوديع التلقائي.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
**📊 أواـمـر الإدارة والـتـنـظـيـم :**
- `.تاك_عام` ⇦ نداء لجميع الأعضاء 📣
- `.المقيدين` ⇦ عرض قائمة المحظورين.
- `.ر` ⇦ استخراج رابط المجموعة.
- `.تثبيت` ⇦ لتثبيت رسالة مهمة.
- `.مسح` ⇦ لتنظيف الشات (بالرد).
- `.معلوماته` ⇦ كشف بيانات العضو.
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
**╰────[ RECO SOURCE @SORS_RECO ]────╯**
"""
            await safe_respond(help_msg)
