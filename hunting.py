import asyncio
import random
import string
from telethon import events, functions, types, errors

# قاموس المهام: يضمن عدم تداخل العمليات ويسمح بإيقافها بدقة
active_hunting_tasks = {}
chars_letters = string.ascii_lowercase
chars_digits = string.digits

async def setup_hunting(client, admins_list):
    
    # --- المحرك الأساسي (يعمل في الخلفية بشكل مستقل) ---
    async def hunting_engine(mode, target_user=None, event=None):
        attempts = 0
        channel_id = None
        # تحديد مفتاح المهمة للإدارة
        task_key = target_user if target_user else mode
        
        while task_key in active_hunting_tasks:
            attempts += 1
            try:
                # 1. تحديد اليوزر (محدد أو عشوائي)
                if target_user:
                    current_user = target_user
                else:
                    # نظام الفواصل الذي طلبته (a_1_z) مع دمج الأحرف والأرقام
                    all_chars = chars_letters + chars_digits
                    if mode == "triple":
                        current_user = f"{random.choice(all_chars)}_{random.choice(all_chars)}_{random.choice(all_chars)}"
                    elif mode == "quad":
                        current_user = f"{random.choice(all_chars)}_{random.choice(all_chars)}_{random.choice(all_chars)}_{random.choice(all_chars)}"
                    else:
                        current_user = f"{random.choice(all_chars)}_{random.choice(all_chars)}_{random.choice(all_chars)}_{random.choice(all_chars)}_{random.choice(all_chars)}"

                # 2. الفحص الذكي (فحص المتاحية)
                try:
                    await client(functions.contacts.ResolveUsernameRequest(username=current_user))
                    # إذا لم يحدث خطأ، يعني اليوزر مأخوذ
                    await asyncio.sleep(1 if target_user else 0.4) 
                    continue
                except (errors.UsernameNotOccupiedError, errors.UsernameInvalidError, Exception):
                    # هنا اليوزر متاح للاقتناص
                    
                    # 3. إنشاء قناة (مرة واحدة فقط للمهمة)
                    if not channel_id:
                        created = await client(functions.channels.CreateChannelRequest(
                            title=f"Reco Hunt: @{current_user}",
                            about="تم الصيد بواسطة سورس ريكو المطور",
                            megagroup=False
                        ))
                        channel_id = created.chats[0].id

                    # 4. التثبيت (Update Username)
                    await client(functions.channels.UpdateUsernameRequest(
                        channel=channel_id,
                        username=current_user
                    ))
                    
                    # 5. إرسال كليشة النجاح
                    success_msg = f"""
✨ **تـم الاقتـناص بنـجاح!** ✨
━━━━━━━━━━━━━━━━━
💎 **اليوزر المصيد:** @{current_user}
🔢 **عدد المحاولات:** {attempts}
📡 **نوع العملية:** {mode if not target_user else "تثبيت محدد"}
✅ **الرابط:** [اضغط هنا للقناة](t.me/{current_user})
━━━━━━━━━━━━━━━━━
🔹 **سورس ريكو المطور**
"""
                    await client.send_message("me", success_msg)
                    if event: await event.respond(success_msg)
                    
                    # إيقاف المهمة إذا كان يوزر محدد، أو الاستمرار إذا كان عشوائي
                    if target_user:
                        active_hunting_tasks.pop(task_key, None)
                        break
                    else:
                        channel_id = None # لتوليد قناة جديدة لليوزر القادم

            except errors.FloodWaitError as e:
                # معالجة حظر التليجرام المؤقت (يصبر ثم يكمل تلقائياً)
                await asyncio.sleep(e.seconds + 1)
            except Exception as e:
                # معالجة الأخطاء الجانبية (مثل امتلاء القنوات العامة)
                if "CHANNELS_ADMIN_PUBLIC_TOO_MUCH" in str(e):
                    await client.send_message("me", "⚠️ تنبيه: حسابك ممتلئ بالقنوات العامة، لا يمكنني إنشاء قناة جديدة.")
                    active_hunting_tasks.pop(task_key, None)
                    break
                await asyncio.sleep(2)

    @client.on(events.NewMessage(outgoing=True))
    async def hunting_handler(event):
        me = await client.get_me()
        if event.sender_id != me.id and event.sender_id not in admins_list: return
        
        text = event.raw_text

        # --- 1. قائمة المساعدة م6 (كاملة دون اختصار) ---
        if text == ".م6":
            menu_text = (
                "**- قـائـمـة أوامـر الصـيد والتـثبـيـت 🎯**\n"
                "━━━━━━━━━━━━━━━━━\n"
                "- صـيد يوزر : `.صيد` + اليوزر\n"
                "- تثـبيـت تيربـو : `.تثبيت` + اليوزر\n"
                "- فـحص يوزر : `.فحص` + اليوزر\n"
                "━━━━━━━━━━━━━━━━━\n"
                "**- أوامـر الصـيد العـشوائـي (تيربو) 🚀**\n"
                "- صيد ثلاثيات : `.صيد_ثلاثيات`\n"
                "- صيد رباعيات : `.صيد_رباعيات`\n"
                "- صيد خماسيات : `.صيد_خماسيات`\n"
                "━━━━━━━━━━━━━━━━━\n"
                "**- صـيد بوتات الـتليجـرام 🤖**\n"
                "- صيد بوت ثلاثي : `.صيد_بوت_ثلاثي` \n"
                "━━━━━━━━━━━━━━━━━\n"
                "- إيقاف العمليات : `.ايقاف الصيد`\n"
                "- حـالة الصيد : `.حالة الصيد`\n"
                "━━━━━━━━━━━━━━━━━\n"
                "💡 *ملاحظة:* التثبيت يقوم بإنشاء قناة تلقائياً ومحاولة حجز اليوزر بها كل ثانية.\n"
            )
            await event.edit(menu_text)

        # --- 2. أوامر الصيد والتثبيت المحدد ---
        elif text.startswith((".صيد ", ".تثبيت ")):
            user = text.split(" ", 1)[1].replace("@", "").strip()
            if user in active_hunting_tasks: return await event.edit(f"⚠️ جاري العمل على @{user}...")
            await event.edit(f"🚀 **بدأ التثبيت التيربو لـ @{user}...**")
            active_hunting_tasks[user] = asyncio.create_task(hunting_engine("fixed", target_user=user, event=event))

        # --- 3. أوامر الصيد العشوائي ---
        elif text in [".صيد_ثلاثيات", ".صيد_رباعيات", ".صيد_خماسيات"]:
            mode = "triple" if "ثلاثيات" in text else "quad" if "رباعيات" in text else "penta"
            if mode in active_hunting_tasks: return await event.edit("⚠️ هذه العملية نشطة بالفعل.")
            await event.edit(f"⚙️ **بدأ الصيد العشوائي ({mode})..**")
            active_hunting_tasks[mode] = asyncio.create_task(hunting_engine(mode, event=event))

        # --- 4. أمر صيد بوتات ثلاثية مطور (هجين + كتم) ---
        elif text == ".صيد_بوت_ثلاثي":
            if "bot_hunting" in active_hunting_tasks:
                return await event.edit("⚠️ **عملية صيد البوتات تعمل بالفعل!**")
            
            await event.edit("🤖 **بدأ صيد بوتات ثلاثية هجينة...**\n🔕 **تم كتم BotFather تلقائياً لتجنب الإزعاج.**")
            
            # كتم بوت فاذر تلقائياً
            try:
                await client(functions.account.UpdateNotifySettingsRequest(
                    peer="@BotFather",
                    settings=types.InputPeerNotifySettings(mute_until=2147483647)
                ))
            except: pass

            active_hunting_tasks["bot_hunting"] = True 

            while "bot_hunting" in active_hunting_tasks:
                try:
                    # توليد يوزر هجين (رقمين وحرف أو حرفين ورقم)
                    mode_choice = random.choice(["2n1c", "1n2c"])
                    if mode_choice == "2n1c":
                        part = random.sample(chars_digits, 2) + random.sample(chars_letters, 1)
                    else:
                        part = random.sample(chars_letters, 2) + random.sample(chars_digits, 1)
                    
                    random.shuffle(part)
                    bot_username = f"{''.join(part).upper()}_BOT"
                    bot_name = "صيد ريكو"

                    async with client.conversation("@BotFather") as conv:
                        await conv.send_message("/newbot")
                        await conv.get_response()
                        await conv.send_message(bot_name)
                        await conv.get_response()
                        await conv.send_message(bot_username)
                        resp = await conv.get_response()

                        if "Done!" in resp.text:
                            await client.send_message("me", f"✅ **مبروك! تم صيد بوت ثلاثي نادر:**\n\n👤 يوزر البوت: @{bot_username}\n{resp.text}")
                            await event.respond(f"🎯 **تم صيد يوزر متاح بنجاح!**\nالبيانات في الرسائل المحفوظة: @{bot_username}")
                            active_hunting_tasks.pop("bot_hunting", None)
                            break
                        elif "sorry" in resp.text.lower() or "taken" in resp.text.lower():
                            pass
                        else:
                            await client.send_message("me", f"⚠️ **تنبيه من بوت فاذر:**\n{resp.text}")

                except Exception as e:
                    print(f"Error in Bot Hunting: {e}")
                
                await asyncio.sleep(10)

        # --- 5. أمر الفحص ---
        elif text.startswith(".فحص "):
            user = text.split(" ", 1)[1].replace("@", "").strip()
            await event.edit(f"🔍 **جاري فحص @{user}...**")
            try:
                await client(functions.contacts.ResolveUsernameRequest(username=user))
                await event.edit(f"✖️ **المستخدم @{user} مأخوذ.**")
            except:
                await event.edit(f"✅ **المستخدم @{user} متاح للاقتناص!**")

        # --- 6. إيقاف العمليات وحالة الصيد ---
        elif text == ".ايقاف الصيد":
            for task in list(active_hunting_tasks.values()):
                if isinstance(task, asyncio.Task):
                    task.cancel()
            active_hunting_tasks.clear()
            await event.edit("🛑 **تم إيقاف كافة العمليات بنجاح.**")

        elif text == ".حالة الصيد":
            if not active_hunting_tasks: 
                await event.edit("📊 **لا توجد عمليات جارية حالياً.**")
            else:
                msg = "🔎 **العمليات النشطة حالياً:**\n" + "\n".join([f"• {k}" for k in active_hunting_tasks.keys()])
                await event.edit(msg)
