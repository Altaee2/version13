import asyncio
import random
from telethon import events, functions, types

async def setup_fun(client, admins_list):

    @client.on(events.NewMessage(outgoing=True))
    async def fun_handler(event):
        me = await client.get_me()
        text = event.raw_text

        # 1. قائمة المساعدة م7
        if text == ".م7":
            help_text = """
**- قـائـمـة أوامـر الـتـسـلـيـة 🎭 (م7)**
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
**☣️ أوامـر الـرعـب والـهـكـر :**
- `.هاك` ⇦ الـهـجـوم الـعـمـلاق 💀
- `.اختراق` | `.اختراق1` ⇦ وهمي
- `.هكر` | `.هعر` ⇦ فـيروس / فشل

**💍 درامـا الـزواج والـطـلاق :**
- `.زواج` ⇦ عـقـد قـران مـبارك 👰🤵
- `.طلاق` ⇦ انـفـصـال رسـمـي 👞
- `.خيانه` ⇦ كـشـف الـخـمـط 🐍

**🎨 الـمـيـديـا والـحـركـات :**
- `.تحويل` ⇦ مـلصق لـصورة 🖼
- `.قمر` ⇦ الـقـمر الـمـتـحرك 🌚
- `.قلب` ⇦ نـبـض الـقـلـوب ❤️‍🔥

**🎲 ألعاب الـتـسـلـيـة والـرد :**
- `.نرد` | `.هدف` | `.سهم` | `.بولينج` 🎮
- `.رفع مطي` | `.كشف` | `.حب` 🎭
‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉
🦅 **SORS RECO : @SORS_RECO_BOT**
"""
            await event.edit(help_text)


        # 2. أوامر الألعاب والحركات (تعمل تلقائياً)
        elif text == ".نرد":
            await event.delete()
            await client.send_file(event.chat_id, types.InputMediaDice(emoticon="🎲"))

        elif text == ".هدف":
            await event.delete()
            await client.send_file(event.chat_id, types.InputMediaDice(emoticon="⚽"))

        elif text == ".سهم":
            await event.delete()
            await client.send_file(event.chat_id, types.InputMediaDice(emoticon="🎯"))

        elif text == ".بولينج":
            await event.delete()
            await client.send_file(event.chat_id, types.InputMediaDice(emoticon="🎳"))

        elif text == ".قمار":
            await event.delete()
            await client.send_file(event.chat_id, types.InputMediaDice(emoticon="🎰"))

        elif text == ".لعبة":
            await event.edit(f"**اختياري هو: {random.choice(['💎 حجر', '📄 ورقة', '✂️ مقص'])}**")

        elif text == ".قمر":
            moons = ["🌑", "🌒", "🌓", "🌔", "🌕", "🌖", "🌗", "🌘", "🌑"]
            for m in moons:
                await event.edit(m)
                await asyncio.sleep(0.2)
            await event.edit("🌚 **نورت السهرة!**")

        elif text == ".قلب":
            hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "💖"]
            for h in hearts:
                await event.edit(h)
                await asyncio.sleep(0.3)
            await event.edit("💖 **I LOVE YOU** 💖")

        # 3. أمر الهكر العام (طلب الفدية)
        elif text == ".هكر":
            await event.edit("⚠️ **System Security Breach Detected...**")
            await asyncio.sleep(1)
            hack_steps = [
                "📡 Connecting to Proxy: [88.241.10.3]...",
                "💉 Injecting Trojan.Win32.Rico.a...",
                "📁 Accessing Private Folders...",
                "💾 Copying Database (3.4 GB)...",
                "🔒 ALL FILES HAVE BEEN ENCRYPTED!"
            ]
            for step in hack_steps:
                await event.edit(f"☣️ **HACKING IN PROGRESS**\n`{step}`")
                await asyncio.sleep(0.8)
            await event.edit("""
**🚨 تـم تـشـفـيـر جـهـازك بـالـكـامـل! 🚨**
━━━━━━━━━━━━━━━━━━
💰 **لإلغاء التشفير:**
يجب إرسال مبلغ **500$ اسيا** إلى المطور @N_QQ_H
أمامك **24 ساعة** فقط قبل مسح البيانات نهائياً!
━━━━━━━━━━━━━━━━━━
""")

        # 4. أوامر تتطلب الرد (Reply)
        elif event.is_reply:
            reply = await event.get_reply_message()

            # اختراق مطول مرعب
            if text.startswith(".اختراق1"):
                await event.edit("📡 **[SYSTEM]: Initializing Deep-Core Attack...**")
                await asyncio.sleep(2)
                steps = [
                    "🔍 Scanning for vulnerabilities...",
                    "🛡 Bypass Firewall: [██░░░░░░░░] 20%",
                    "🔓 Exploit Found: (CVE-2026-9912)",
                    "🧬 Brute-forcing Encryption: [████░░░░░░] 40%",
                    "📥 Accessing Internal Memory: [██████░░░░] 60%",
                    "🎭 Spoofing User Identity...",
                    "💾 Downloading Personal Data: [████████░░] 80%",
                    "📸 Activating Microphone & Camera...",
                    "📊 Finalizing Injection: [██████████] 100%",
                    "💀 **ALL SYSTEMS COMPROMISED.**"
                ]
                for step in steps:
                    await event.edit(f"☠️ **[HACKER MODE ACTIVE]**\n`{step}`")
                    await asyncio.sleep(1.5)
                await event.edit(f"🔥 **تـم تدمـيـر الحسـاب بنـجاح!**\nالضحية: `{reply.sender_id}`\nالحالة: **تحت السيطرة الكاملة ✅**")

            # اختراق سريع
            elif text.startswith(".اختراق"):
                await event.edit("📡 **جاري سحب بيانات الضحية...**")
                await asyncio.sleep(1)
                steps = [
                    f"👤 Target ID: `{reply.sender_id}`",
                    "🔓 Password Cracking: [SUCCESS]",
                    "📍 Location: Baghdad, Iraq",
                    "📸 Accessing Camera: [LIVE ON]"
                ]
                for s in steps:
                    await event.edit(f"⚠️ **ATTACKING...**\n`{s}`")
                    await asyncio.sleep(0.7)
                await event.edit("💀 **تم الاختراق! الضحية الآن تحت سيطرتك.**")

            # فشل الاختراق (هعر)
            elif text.startswith(".هعر"):
                await event.edit("☣️ **محاولة اختراق النظام الدفاعي...**")
                await asyncio.sleep(1.5)
                fail_steps = [
                    "📡 محاولة كسر جدار الحماية...",
                    "⚠️ تحذير: تم اكتشاف محاولة الدخول!",
                    "🛡 نظام الحماية مفعل حالياً.",
                    "🚫 ERROR: Access Denied!"
                ]
                for s in fail_steps:
                    await event.edit(f"⚙️ **جاري الاختراق:**\n`{s}`")
                    await asyncio.sleep(1.2)
                await event.edit("❌ **فـشـل الاخـتـراق!**\nنظام حماية المستخدم قوي جداً تم صد الهجوم.")

            # تحويل ملصق لصورة
            elif text == ".تحويل" and reply.sticker:
                await event.edit("🔄 جاري التحويل...")
                path = await reply.download_media()
                await client.send_file(event.chat_id, path, reply_to=reply.id)
                await event.delete()

            # أوامر الرد التقليدية
            elif text == ".حب":
                await event.edit(f"❤️ نسبة الحب هي **{random.randint(0, 100)}%**")
            elif text == ".رفع مطي":
                await event.edit("🐴 تم رفعه مطي بالحظيرة بنجاح!")
            elif text == ".طرد":
                await event.edit("👞 تم طرده بنعال طيارة برة المجموعة!")
            elif text == ".كشف":
                res = random.choice(["كاذب 🤥", "صادق ✅", "نص نص 🤔", "جذاب درجة أولى 🤡"])
                await event.edit(f"🔍 نتيجة جهاز كشف الكذب: **{res}**")
            # --- أمر الهاك العملاق (دقيقتين من الرعب) ---
            elif text.startswith(".هاك"):
                await event.edit("⚠️ **[CRITICAL]: SYSTEM OVERRIDE INITIATED...**")
                await asyncio.sleep(3)
                
                mega_hack = [
                    "📡 Connecting to Global Satellites... [OK]",
                    "🔐 Bypassing Telegram Cloud Encryption...",
                    "🕵️ Tracking User IP: [192.168.0.104]...",
                    "📡 Signal Found: Baghdad/Al-Mansour",
                    "💾 Accessing Private Gallery... [2%]",
                    "📊 Loading Data: [█▒▒▒▒▒▒▒▒▒] 10%",
                    "💾 Accessing Private Gallery... [15%]",
                    "⚠️ FIREWALL DETECTED: [Attempting Bypass]",
                    "🛡️ Injecting Malicious Script: (Rico_V6.py)",
                    "✅ Firewall Destroyed. Accessing System Root...",
                    "📊 Loading Data: [███▒▒▒▒▒▒▒] 30%",
                    "📱 Device Model: [iPhone 15 Pro Max] Found.",
                    "📸 Opening Front Camera... [SUCCESS]",
                    "🖼️ Capturing Screen... [DONE]",
                    "📊 Loading Data: [█████▒▒▒▒▒] 50%",
                    "📂 Fetching Saved Passwords (Google/FB/IG)...",
                    "🔑 142 Passwords Found. Saving to Server...",
                    "🛰️ Linking with International Hacker Servers...",
                    "📊 Loading Data: [███████▒▒▒] 75%",
                    "🧬 Extracting Biometric Data (FaceID/TouchID)...",
                    "🚨 WARNING: Device Temperature Rising!",
                    "🔌 Overclocking Processor... [SUCCESS]",
                    "📊 Loading Data: [█████████▒] 90%",
                    "📥 Finalizing Data Transfer: (14.2 GB)...",
                    "💥 Injecting Fatal System Virus...",
                    "📊 Loading Data: [██████████] 100%",
                    "💀 **SYSTEM IS NOW UNDER RECO CONTROL.**"
                ]

                for step in mega_hack:
                    # إضافة إيموجيات هكر عشوائية لزيادة الرعب
                    hacker_icons = random.choice(["☣️", "💀", "💻", "🛰️", "⚙️", "🔥"])
                    await event.edit(f"{hacker_icons} **[ULTRA HACK ACTIVE]** {hacker_icons}\n`{step}`")
                    # تأخير 4 ثواني بين كل خطوة لضمان وصول الوقت لدقيقتين
                    await asyncio.sleep(4.5)

                await event.edit(f"""
**🔥 تـم اخـتـراق الـهـدف بـنـجـاح كـامـل 🔥**
━━━━━━━━━━━━━━━━━━
👤 الضحية: [{reply.sender.first_name}](tg://user?id={reply.sender_id})
🆔 الايدي: `{reply.sender_id}`
━━━━━━━━━━━━━━━━━━
☠️ **جاري مسح الذاكرة الداخلية...**
☠️ **جاري تعطيل مداخل الشحن...**
☠️ **جاري رفع الملفات للسيرفر...**

💸 **الخيار الوحيد للنجاة:**
تواصل مع المطور @N_QQ_H لفك التشفير.
━━━━━━━━━━━━━━━━━━
**BYE BYE YOUR SYSTEM! 💀**
""")
            # --- أمر الزواج (.زواج) ---
            elif text == ".زواج":
                reply = await event.get_reply_message()
                me = await client.get_me()
                # أسماء الزوجين
                user1 = f"[{me.first_name}](tg://user?id={me.id})"
                user2 = f"[{reply.sender.first_name}](tg://user?id={reply.sender_id})"
                
                marriage_text = f"""
**💍 تـم عـقـد الـقـران بـنـجـاح! 💍**
━━━━━━━━━━━━━━━━━━
👰 **الـعـروس:** {user2}
🤵 **الـعـريـس:** {user1}

🎊 الـف مـبـروك لـلـعـرسـان الـحـلويـن!
✨ بارك الله لكما وبارك عليكما وجمع بينكما في خير.
━━━━━━━━━━━━━━━━━━
🎶 *جاري تحضير الكيك والدي جي...* 💃🕺
"""
                await event.edit(marriage_text)

            # --- أمر الطلاق (.طلاق) ---
            elif text == ".طلاق":
                reply = await event.get_reply_message()
                me = await client.get_me()
                user2 = f"[{reply.sender.first_name}](tg://user?id={reply.sender_id})"
                
                divorce_reasons = [
                    "لأنك ما تغسل مواعين 🍽️",
                    "لأنك تنام هواي وتنسى الطلبات 💤",
                    "بسبب الخيانة الزوجية مع سورس ثاني 💔",
                    "لأنك تصرف فلوسنا على شدات ببجي 🎮",
                    "ماكو توافق كيميائي بيننا! 🧪"
                ]
                
                divorce_text = f"""
**💔 ورقة طـلاق رسـمـيـة 💔**
━━━━━━━━━━━━━━━━━━
لقد قرر الطرف الأول الانفصال عن:
👤 {user2}

⚠️ **السبب:** {random.choice(divorce_reasons)}
⚖️ الـحـالـة: أنـتِ طـالـق طـالـق طـالـق! 👞
━━━━━━━━━━━━━━━━━━
👋 باي باي.. درب السد ما يرد!
"""
                await event.edit(divorce_text)
            # --- أمر الخيانة (.خيانه) ---
            elif text == ".خيانه":
                reply = await event.get_reply_message()
                me = await client.get_me()
                
                # أسماء الأطراف
                victim = f"[{me.first_name}](tg://user?id={me.id})"
                traitor = f"[{reply.sender.first_name}](tg://user?id={reply.sender_id})"
                
                betrayal_scenes = [
                    "شفتك بالحديقة وية سورس ثاني! 🌳🐍",
                    "ليش راد على ستوري غيري ومنطيني بلوك؟ 📱💔",
                    "البوت كلي كلشي، طلعت تحجي وية المطور من وراي! 🕵️‍♂️",
                    "لكيت صورتك بملفات سورس ثاني، هاي خيانة عظمى! 📂🚫"
                ]
                
                betrayal_text = f"""
**🔥 بـلاغ خـيـانـة عـظـمـى! 🔥**
━━━━━━━━━━━━━━━━━━
👤 الضحية: {victim}
🐍 الخائن: {traitor}

📢 **تـصـريـح الـضـحـيـة:**
"{random.choice(betrayal_scenes)}"

⚖️ **قـرار الـمـحـكـمـة الـعـلـيـا لـسـورس ريـكـو:**
بناءً على الأدلة القاطعة، قررنا فسخ العلاقة فوراً ورمي الخائن خارج أسوار قلوبنا! 👞💨
━━━━━━━━━━━━━━━━━━
💔 انـتـهـت الـقـصـة.. يـا لـلأسـف!
"""
                await event.edit(betrayal_text)
