import asyncio
import os
from telethon import events, functions, types

# قاموس المهام النشطة: مفتاح القاموس هو ايدي الكروب والقيمة هي المهمة البرمجية
active_auto_tasks = {}

# قاموس لتخزين بيانات النشر الحالية (للأوامر الجديدة)
group_publish_data = {
    "links": [],
    "message": "",
    "delay": 300,
    "count": 0,
    "sent": {},  # عدد الرسائل المرسلة لكل مجموعة
    "tasks": {},  # المهام النشطة
    "last_sent": {}  # آخر وقت تم فيه إرسال رسالة
}

# قاموس مؤقت لتخزين بيانات الأمر الجديد
add_group_data = {}

async def setup_auto(client, admins_list):
    
    @client.on(events.NewMessage(outgoing=True))
    async def auto_handler(event):
        text = event.raw_text
        chat_id = event.chat_id
        me = await client.get_me()

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. أمر التكرار السريع جداً (0.001 ثانية)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if text.startswith(".كرر "):
            try:
                parts = text.split(" ", 2)
                if len(parts) < 3:
                    return await event.edit("⚠️ **عذراً ريكو.. أرسل الأمر هكذا:**\n`.كرر [العدد] [النص]`")
                
                count = int(parts[1])
                msg = parts[2]
                
                await event.delete() # حذف رسالة الأمر للحفاظ على مظهر المحادثة
                
                for _ in range(count):
                    await client.send_message(chat_id, msg)
                    await asyncio.sleep(0.001) # سرعة خيالية ثابتة
            except Exception as e:
                pass

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. أمر النشر التلقائي (عام / خاص / سري)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text.startswith(".تلقائي "):
            try:
                # الصيغة: .تلقائي [الرابط] [العدد] [الثواني] [النص]
                parts = text.split(" ", 4)
                if len(parts) < 5:
                    return await event.edit("⚠️ **نقص في معطيات النشر!**\nالصيغة الصحيحة:\n`.تلقائي [الرابط] [العدد] [الثواني] [الكليشة]`")
                
                link = parts[1]
                count = int(parts[2])
                seconds = int(parts[3])
                message_text = parts[4]

                # فحص شرط الوقت (300 ثانية كحد أدنى)
                if seconds < 300:
                    return await event.edit("⚠️ **تنبيه أمان من سورس ريكو!**\nيجب أن يكون الوقت **300 ثانية** أو أكثر لتجنب حظر حسابك من قبل شركة تلغرام.")

                await event.edit("⏳ **جاري فحص الهدف والاتصال بالخادم...**")

                try:
                    # جلب الكيان (المجموعة) سواء كانت يوزر أو رابط خاص
                    target_entity = await client.get_entity(link)
                    target_chat = target_entity.id
                except Exception as e:
                    return await event.edit(f"❌ **فشل الوصول للرابط!**\nتأكد أنك عضو في المجموعة أو أن الرابط صحيح.\n`{str(e)}` ")

                # رسالة التأكيد (سرية في المحفوظات أو علنية في المجموعات)
                if chat_id == me.id:
                    await event.edit(
                        f"🕵️ **تـم تـفـعـيـل الـنـشـر الـسـري بـنـجـاح**\n"
                        f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                        f"🚀 **الـهـدف :** {target_entity.title}\n"
                        f"🔢 **الـعـدد :** {count} رسالة\n"
                        f"⏱ **الـفـاصـل :** {seconds} ثانية\n"
                        f"‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                        f"✅ سأبدأ النشر الآن من الكواليس.."
                    )
                else:
                    await event.edit(f"✅ **تم بدء النشر التلقائي في هذه المجموعة.**")

                # إذا كانت هناك مهمة قديمة لنفس المجموعة، يتم إيقافها أولاً
                if target_chat in active_auto_tasks:
                    active_auto_tasks[target_chat].cancel()

                # تعريف وظيفة النشر في الخلفية
                async def auto_post_task(t_chat, t_count, t_seconds, t_msg):
                    sent = 0
                    while sent < t_count:
                        try:
                            await client.send_message(t_chat, t_msg)
                            sent += 1
                        except:
                            pass # استمرار المحاولة في حال وجود تقييد بسيط
                        if sent >= t_count: break
                        await asyncio.sleep(t_seconds)
                    
                    if t_chat in active_auto_tasks:
                        del active_auto_tasks[t_chat]

                # تخزين المهمة وتفعيلها
                active_auto_tasks[target_chat] = asyncio.create_task(
                    auto_post_task(target_chat, count, seconds, message_text)
                )

            except Exception as e:
                await event.edit(f"⚠️ **حدث خطأ غير متوقع:**\n`{str(e)}` ")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. أمر إيقاف النشر (ذكي وشامل)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".ايقاف التلقائي":
            # الحالة الأولى: إذا أرسل الأمر في الرسائل المحفوظة (إيقاف شامل)
            if chat_id == me.id:
                if active_auto_tasks:
                    total = len(active_auto_tasks)
                    for t_id in list(active_auto_tasks.keys()):
                        active_auto_tasks[t_id].cancel()
                        del active_auto_tasks[t_id]
                    await event.edit(f"🛑 **تـم إيـقـاف جـمـيـع الـمـهـام!**\nتم إنهاء ({total}) عملية نشر في كافة الكروبات.")
                else:
                    await event.edit("⚠️ **لا توجد أي مهام نشر نشطة حالياً.**")
            
            # الحالة الثانية: إذا أرسل الأمر داخل مجموعة معينة
            else:
                if chat_id in active_auto_tasks:
                    active_auto_tasks[chat_id].cancel()
                    del active_auto_tasks[chat_id]
                    await event.edit("🛑 **تم إيقاف النشر التلقائي في هذه المجموعة فقط.**")
                else:
                    await event.edit("⚠️ **لا يوجد نشر تلقائي نشط في هذه الدردشة.**")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. قائمة المساعدة .م9 (مزخرفة ومنسقة)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".م9":
            help_text = f"""
**╭───[ 📢 قـائـمـة الـنـشـر والـتـكرار ]───╮**

**⚙️ أوامـر الـتـكـرار (السريع) :**
◈ `.كرر` [العدد] [النص]
ـ الوقت ثابت (0.001 ثانية) للهجوم السريع.

**🤖 أوامـر الـنـشـر (التلقائي) :**
◈ `.تلقائي` [الرابط] [العدد] [الثواني] [النص]
ـ يدعم الروابط العامة (@..) والروابط الخاصة.
ـ **ملاحظة:** أقل وقت مسموح هو 300 ثانية.

**🕵️ مـيـزة الـسـريـة الـتـامـة :**
◈ عند إرسال أمر النشر في (الرسائل المحفوظة) سيقوم السورس بالنشر في الهدف المطلوب دون أن تظهر رسائل الأوامر في المجموعة المستهدفة.

**🛑 أوامـر الإيـقـاف :**
◈ أرسل `.ايقاف التلقائي` في المجموعة لإيقافها.
◈ أرسل `.ايقاف التلقائي` في المحفوظة لإيقاف (الكل).

**🆕 أوامـر الـمجـمـوعـات الـمـطـورة :**
◈ `.اضف_مجموعة` ⇦ إضافة مجموعات متعددة للنشر
◈ `.ايقاف_مجموعة` ⇦ إيقاف النشر في جميع المجموعات
◈ `.تغيير_كليشة_مجموعة` ⇦ تغيير الكليشة وإعادة التشغيل
◈ `.حالة_المجموعة` ⇦ عرض تقرير كامل عن حالة النشر
◈ `.تعديل_مجموعة` ⇦ إضافة رابط جديد للمجموعات
◈ `.ازالة_رابط_مجموعة` ⇦ حذف رابط من قائمة النشر

‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
**👤 الـمـطـور : @N_QQ_H**
**🚀 الـقـنـاة : @SORS_RECO**
**╰──────────────╯**
"""
            await event.edit(help_text)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. أمر إضافة مجموعات متعددة للنشر
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".اضف_مجموعة":
            me = await client.get_me()
            if event.sender_id != me.id and event.sender_id not in admins_list:
                return

            user_id = event.sender_id
            add_group_data[user_id] = {
                "links": [],
                "step": "links",
                "message": None,
                "delay": None,
                "count": None
            }

            await event.edit(
                "✅ **تم بدء وضع إضافة مجموعات جديدة.**\n"
                "📬 **أرسل الروابط واحدة تلو الأخرى (إلى 10 روابط).**\n"
                "✍️ **عند الانتهاء أرسل:** `تم`"
            )

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. جمع الروابط والبيانات التفاعلية
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text and event.sender_id in add_group_data and event.out:
            data = add_group_data[event.sender_id]
            current_text = text.strip()

            if data["step"] == "links":
                if current_text == "تم":
                    if not data["links"]:
                        await event.edit("❌ **لم تضف أي روابط! تم الإلغاء.**")
                        del add_group_data[event.sender_id]
                        return
                    data["step"] = "message"
                    await event.edit("📄 **الآن أرسل الكليشة (نص الرسالة):**")
                    return

                if len(data["links"]) >= 10:
                    await event.edit("⚠️ **وصلت للحد الأقصى (10 روابط). أرسل `تم` للمتابعة.**")
                    return

                try:
                    entity = await client.get_entity(current_text)
                    data["links"].append(current_text)
                    await event.edit(f"✅ **تمت إضافة الرابط رقم {len(data['links'])}.**\nأرسل الرابط التالي أو `تم` للمتابعة.")
                except Exception as e:
                    await event.edit(f"❌ **رابط غير صالح!** حاول مرة أخرى.\n`{str(e)}`")

            elif data["step"] == "message":
                data["message"] = current_text
                data["step"] = "delay"
                await event.edit("⏱ **الآن أرسل الوقت بين الرسائل (بالثواني، من 300 إلى 3000):**")

            elif data["step"] == "delay":
                if not current_text.isdigit():
                    await event.edit("⚠️ **يرجى إدخال رقم صحيح (ثواني).**")
                    return
                delay = int(current_text)
                if delay < 300 or delay > 3000:
                    await event.edit("⚠️ **الوقت يجب أن يكون بين 300 و 3000 ثانية.**")
                    return
                data["delay"] = delay
                data["step"] = "count"
                await event.edit("🔢 **أخيراً، أرسل عدد الرسائل لكل مجموعة:**")

            elif data["step"] == "count":
                if not current_text.isdigit():
                    await event.edit("⚠️ **يرجى إدخال رقم صحيح.**")
                    return
                count = int(current_text)
                if count <= 0:
                    await event.edit("⚠️ **عدد الرسائل يجب أن يكون أكبر من 0.**")
                    return

                data["count"] = count
                del add_group_data[event.sender_id]

                # نسخ البيانات إلى النظام الرئيسي
                group_publish_data["links"] = data["links"]
                group_publish_data["message"] = data["message"]
                group_publish_data["delay"] = data["delay"]
                group_publish_data["count"] = data["count"]
                group_publish_data["sent"] = {link: 0 for link in data["links"]}
                group_publish_data["last_sent"] = {}

                # بدء النشر التلقائي
                await event.edit("🚀 **جاري بدء النشر التلقائي في المجموعات...**")
                for link in data["links"]:
                    try:
                        entity = await client.get_entity(link)
                        target_chat = entity.id

                        async def auto_post_task(t_chat, t_count, t_seconds, t_msg):
                            sent = 0
                            while sent < t_count:
                                try:
                                    await client.send_message(t_chat, t_msg)
                                    sent += 1
                                    group_publish_data["sent"][link] = sent
                                    group_publish_data["last_sent"][link] = datetime.now()
                                except:
                                    pass
                                if sent >= t_count:
                                    break
                                await asyncio.sleep(t_seconds)

                        task = asyncio.create_task(
                            auto_post_task(target_chat, count, delay, data["message"])
                        )
                        group_publish_data["tasks"][link] = task

                    except Exception as e:
                        await event.respond(f"❌ **فشل الوصول لـ {link}:**\n`{str(e)}`")

                await event.edit("✅ **تم بدء النشر التلقائي في جميع المجموعات بنجاح!**")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 7. أمر إيقاف النشر في جميع المجموعات
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".ايقاف_مجموعة":
            me = await client.get_me()
            if event.sender_id != me.id and event.sender_id not in admins_list:
                return

            for task in group_publish_data["tasks"].values():
                task.cancel()
            
            group_publish_data["tasks"].clear()
            group_publish_data["sent"].clear()
            group_publish_data["last_sent"].clear()

            await event.edit("🛑 **تم إيقاف النشر في جميع المجموعات.**")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 8. أمر تغيير الكليشة وإعادة التشغيل
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".تغيير_كليشة_مجموعة":
            me = await client.get_me()
            if event.sender_id != me.id and event.sender_id not in admins_list:
                return

            if not group_publish_data["links"]:
                await event.edit("⚠️ **لا توجد مجموعات محفوظة لتغيير الكليشة.**")
                return

            await event.edit("📄 **أرسل الكليشة الجديدة الآن:**")

            async with client.conversation(event.chat_id, timeout=60) as conv:
                msg = await conv.get_response()
                new_message = msg.raw_text

                group_publish_data["message"] = new_message
                group_publish_data["sent"] = {link: 0 for link in group_publish_data["links"]}

                # إعادة تشغيل النشر
                for link in group_publish_data["links"]:
                    try:
                        entity = await client.get_entity(link)
                        target_chat = entity.id

                        async def auto_post_task(t_chat, t_count, t_seconds, t_msg):
                            sent = 0
                            while sent < t_count:
                                try:
                                    await client.send_message(t_chat, t_msg)
                                    sent += 1
                                    group_publish_data["sent"][link] = sent
                                    group_publish_data["last_sent"][link] = datetime.now()
                                except:
                                    pass
                                if sent >= t_count:
                                    break
                                await asyncio.sleep(t_seconds)

                        task = asyncio.create_task(
                            auto_post_task(target_chat, group_publish_data["count"], group_publish_data["delay"], new_message)
                        )
                        group_publish_data["tasks"][link] = task

                    except Exception as e:
                        await event.respond(f"❌ **فشل إعادة التشغيل لـ {link}:**\n`{str(e)}`")

                await event.edit("✅ **تم تغيير الكليشة وإعادة تشغيل النشر في جميع المجموعات.**")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 9. أمر حالة النشر التفصيلية
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".حالة_المجموعة":
            me = await client.get_me()
            if event.sender_id != me.id and event.sender_id not in admins_list:
                return

            if not group_publish_data["links"]:
                await event.edit("📭 **لا توجد مجموعات نشطة حالياً.**")
                return

            msg = "**📊 حالة النشر التلقائي في المجموعات:**\n‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
            total_sent = 0

            for link in group_publish_data["links"]:
                try:
                    entity = await client.get_entity(link)
                    name = entity.title
                    sent = group_publish_data["sent"].get(link, 0)
                    total = group_publish_data["count"]
                    remaining = total - sent
                    last = group_publish_data["last_sent"].get(link)
                    next_in = group_publish_data["delay"] if last else 0

                    msg += f"🔹 **{name}**\n" \
                           f"├ رابط: `{link}`\n" \
                           f"├ تم الإرسال: `{sent}/{total}`\n" \
                           f"├ المتبقي: `{remaining}`\n" \
                           f"├ الوقت بين الرسائل: `{group_publish_data['delay']} ثانية`\n" \
                           f"└ التالية خلال: `{next_in} ثانية`\n\n"

                    total_sent += sent
                except Exception as e:
                    msg += f"❌ **خطأ في الوصول لـ {link}:**\n`{str(e)}`\n\n"

            msg += f"📈 **إجمالي الرسائل المرسلة:** `{total_sent}`\n" \
                   f"📋 **عدد المجموعات:** `{len(group_publish_data['links'])}`"

            await event.edit(msg)

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 10. أمر إضافة رابط جديد
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".تعديل_مجموعة":
            me = await client.get_me()
            if event.sender_id != me.id and event.sender_id not in admins_list:
                return

            await event.edit("🔗 **أرسل الرابط الجديد الآن:**")

            async with client.conversation(event.chat_id, timeout=60) as conv:
                msg = await conv.get_response()
                new_link = msg.raw_text.strip()

                try:
                    entity = await client.get_entity(new_link)
                    target_chat = entity.id

                    if new_link in group_publish_data["links"]:
                        await event.edit("⚠️ **هذا الرابط موجود بالفعل.**")
                        return

                    group_publish_data["links"].append(new_link)
                    group_publish_data["sent"][new_link] = 0

                    # بدء النشر لهذا الرابط
                    async def auto_post_task(t_chat, t_count, t_seconds, t_msg):
                        sent = 0
                        while sent < t_count:
                            try:
                                await client.send_message(t_chat, t_msg)
                                sent += 1
                                group_publish_data["sent"][new_link] = sent
                                group_publish_data["last_sent"][new_link] = datetime.now()
                            except:
                                pass
                            if sent >= t_count:
                                break
                            await asyncio.sleep(t_seconds)

                    task = asyncio.create_task(
                        auto_post_task(target_chat, group_publish_data["count"], group_publish_data["delay"], group_publish_data["message"])
                    )
                    group_publish_data["tasks"][new_link] = task

                    await event.edit(f"✅ **تمت إضافة الرابط وبدء النشر:** `{new_link}`")

                except Exception as e:
                    await event.edit(f"❌ **رابط غير صالح:**\n`{str(e)}`")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 11. أمر حذف رابط
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text == ".ازالة_رابط_مجموعة":
            me = await client.get_me()
            if event.sender_id != me.id and event.sender_id not in admins_list:
                return

            await event.edit("❌ **أرسل الرابط المراد حذفه:**")

            async with client.conversation(event.chat_id, timeout=60) as conv:
                msg = await conv.get_response()
                link_to_remove = msg.raw_text.strip()

                if link_to_remove not in group_publish_data["links"]:
                    await event.edit("⚠️ **هذا الرابط غير موجود في القائمة.**")
                    return

                # إيقاف المهمة إذا كانت نشطة
                if link_to_remove in group_publish_data["tasks"]:
                    group_publish_data["tasks"][link_to_remove].cancel()
                    del group_publish_data["tasks"][link_to_remove]

                group_publish_data["links"].remove(link_to_remove)
                group_publish_data["sent"].pop(link_to_remove, None)
                group_publish_data["last_sent"].pop(link_to_remove, None)

                await event.edit(f"✅ **تم حذف الرابط وإيقاف النشر:** `{link_to_remove}`")
