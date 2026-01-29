import asyncio
import random
import requests
import json
from datetime import datetime
from telethon import events, functions, types

# 📜 قائمة الرسائل العشوائية للترحيب
WELCOME_MSGS = [
    "✨ **أهلاً وسهلاً بالجميع في رحاب هذا الجروب!**",
    "💎 **هذا الجروب تم إنشاؤه خصيصاً لراحتكم وتواصلكم.**",
    "🎉 **مرحباً بكم في عالمكم الجديد.. نورتونا!**",
    "⚡️ **تم إنشاء هذا الجروب بواسطة سورس ريكو المطور.**",
    "🌟 **بوجودكم تكتمل الفرحة.. أهلاً بكم.**",
    "🚀 **انطلقوا الآن وشاركونا إبداعاتكم.**"
]

# 🧠 نظام المحركات العشرة الخارق (Sequential Multi-Engine)
async def get_super_ai_response(prompt):
    # قائمة بـ 10 روابط ومحركات مختلفة (عالمية وبديلة)
    engines = [
        f"https://sandipbaruwal.onrender.com/gpt?prompt={prompt}",
        f"https://api.vyturex.com/chatgpt?prompt={prompt}",
        f"https://darkness.ashlynn.workers.dev/chat?q={prompt}",
        f"https://api.freegpt4.0.workers.dev/?q={prompt}",
        f"https://api.dicebear.com/7.x/bottts/svg", # تمويه (تجاهل)
        f"https://api.simsimi.vn/v1/simtalk?text={prompt}&lc=ar",
        f"https://hercai.onrender.com/v3/hercai?question={prompt}",
        f"https://api.popcat.xyz/chatbot?msg={prompt}",
        f"https://api.api-ninjas.com/v1/chatgpt?text={prompt}",
        f"https://aivurex.onrender.com/gpt?prompt={prompt}"
    ]
    
    loop = asyncio.get_event_loop()
    for url in engines:
        try:
            # تقليل وقت الانتظار لكل محرك لزيادة السرعة
            response = await loop.run_in_executor(None, lambda: requests.get(url, timeout=5))
            if response.status_code == 200:
                res_data = response.json()
                # البحث عن الجواب في القواميس المختلفة
                answer = (res_data.get("answer") or res_data.get("gpt") or 
                          res_data.get("response") or res_data.get("reply") or 
                          res_data.get("out") or res_data.get("message"))
                if answer and len(str(answer)) > 2:
                    return answer
        except:
            continue # إذا فشل المحرك الحالي، جرب المحرك التالي فوراً
    return None

async def setup_extra_menus(client, admins_list):

    @client.on(events.NewMessage)
    async def extra_handler(event):
        text = event.raw_text
        me = await client.get_me()
        
        # حماية: المالك والمساعدين فقط
        if event.sender_id != me.id and event.sender_id not in admins_list:
            return

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. قائمة المساعدة (م10)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        if text == ".م10":
            help_m10 = (
                "⚙️ **أوامـر الـذكـاء والـصـنـع (م10) :**\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "• `.ذكاء` + سؤالك : ذكاء اصطناعي (10 محركات).\n"
                "• `.صنع` + العدد : إنشاء سوبر كروبات وأرشفتها.\n"
                "• `.بوت` [الاسم] [اليوزر] : صنع بوت عبر بوت فاذر.\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "💡 **مثال لصنع بوت:** `.بوت ريكو reco_bot`\n"
                "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                "📡 **Channel:** @SORS_RECO"
            )
            await event.edit(help_m10)
            return


        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. أمر الذكاء الاصطناعي (.ذكاء) - النسخة الخارقة
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text.startswith(".ذكاء "):
            try:
                prompt = text.split(" ", 1)[1]
                await event.edit("🚀 **ريكو يشغل المحركات العشرة...**")
                
                answer = await get_super_ai_response(prompt)
                
                if answer:
                    await event.edit(f"🤖 **إجابة ذكاء ريكو الاصطناعي:**\n\n{answer}")
                else:
                    await event.edit("⚠️ **عذراً ريكو، جميع المحركات الـ 10 مشغولة حالياً.**")
            except Exception as e:
                await event.edit(f"❌ **خطأ غير متوقع:** `{str(e)}` ")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. أمر صنع السوبر كروبات (الدالة الأصلية)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        elif text.startswith(".صنع"):
            try:
                parts = text.split(" ")
                if len(parts) < 2:
                    return await event.edit("⚠️ **يرجى تحديد عدد الكروبات.. مثال: `.صنع_كروبات 5`**")
                
                count = int(parts[1])
                if count > 50:
                    return await event.edit("⚠️ **عذراً ريكو، الحد الأقصى للإنشاء هو 50 كروب.**")
                
                await event.edit(f"⚙️ **بدأت المهمة.. جاري إنشاء ({count}) سوبر كروب.**")
                date_now = datetime.now().strftime("%Y/%m/%d")
                
                for i in range(1, count + 1):
                    group_title = f"كروب {i} - {date_now}"
                    
                    try:
                        # إنشاء القناة وتحويلها لسوبر كروب
                        result = await client(functions.channels.CreateChannelRequest(
                            title=group_title,
                            about="تم الإنشاء تلقائياً بواسطة سورس ريكو المطور ⚡️",
                            megagroup=True
                        ))
                        
                        channel_peer = result.chats[0].id
                        
                        # إرسال 7 رسائل ترحيبية عشوائية
                        for _ in range(7):
                            await client.send_message(channel_peer, random.choice(WELCOME_MSGS))
                            await asyncio.sleep(0.4)
                        
                        # استخراج الرابط
                        invite_link = await client(functions.messages.ExportChatInviteRequest(peer=channel_peer))
                        
                        # إرسال المعلومات للمحفوظات
                        log_msg = f"""
**👑 تم إنشاء سوبر كروب {i}/{count} بنجاح!**
━━━━━━━━━━━━━━━━━━━
📦 **الاسـم:** {group_title}
🔗 **الرابط:** {invite_link.link}
📅 **التاريخ:** {date_now}
━━━━━━━━━━━━━━━━━━━
"""
                        await client.send_message("me", log_msg)
                        
                        # انتظار 30 ثانية لتجنب "FloodWait"
                        if i < count:
                            await asyncio.sleep(30)
                            
                    except Exception as e:
                        await client.send_message("me", f"❌ **توقفت العملية عند الكروب رقم {i} بسبب:**\n`{str(e)}` ")
                        break 

                await client.send_message("me", "🏁 **اكتملت عملية إنشاء الكروبات بنجاح.**")
                
            except ValueError:
                await event.edit("⚠️ **يرجى إدخال أرقام فقط.**")
            except Exception as e:
                await event.edit(f"⚠️ **خطأ عام:** `{str(e)}` ")





        elif text.startswith(".بوت "):
            try:
                # تقسيم النص لأخذ الاسم واليوزر
                # طريقة الكتابة: .بوت اسم_البوت @يوزر_البوت
                input_data = text.split(" ", 2)
                
                if len(input_data) < 3:
                    return await event.edit("⚠️ **نقص في المعلومات!**\n💡 اكتب: `.بوت` [الاسم] [اليوزر]\nمثال: `.بوت ريكو reco_bot`")
                
                bot_name = input_data[1]
                bot_username = input_data[2].replace("@", "").strip()
                
                if not bot_username.lower().endswith("bot"):
                    return await event.edit("❌ **خطأ:** يوزر البوت لازم ينتهي بكلمة `bot`.")

                await event.edit(f"⏳ **جاري إنشاء البوت عبر بوت فاذر...**\n🏷 الاسم: `{bot_name}`\n👤 اليوزر: `@{bot_username}`")

                async with client.conversation("@BotFather", timeout=60) as conv:
                    # بدء العملية
                    await conv.send_message("/newbot")
                    await asyncio.sleep(1.5)
                    
                    # إرسال الاسم
                    await conv.send_message(bot_name)
                    await asyncio.sleep(1.5)
                    resp = await conv.get_response()
                    
                    if "Sorry" in resp.text or "invalid" in resp.text:
                        return await event.edit("❌ **رفض بوت فاذر هذا الاسم، حاول مرة أخرى باسم مختلف.**")

                    # إرسال اليوزر
                    await conv.send_message(bot_username)
                    await asyncio.sleep(1.5)
                    resp = await conv.get_response()
                    
                    if "already taken" in resp.text.lower():
                        return await event.edit("❌ **هذا اليوزر محجوز! جرب يوزراً آخر.**")
                    
                    if "Done!" in resp.text:
                        # استخراج التوكن
                        import re
                        token_match = re.search(r'\d+:[A-Za-z0-9_-]+', resp.text)
                        token = token_match.group(0) if token_match else "لم يتم العثور على التوكن"
                        
                        created_at = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        result_msg = (
                            "✅ **تم إنشاء بوتك بنجاح من سورس ريكو!**\n"
                            "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                            f"📦 **اسم البوت:** `{bot_name}`\n"
                            f"👤 **يوزر البوت:** `@{bot_username}`\n"
                            f"🔑 **التوكن:**\n`{token}`\n"
                            f"📅 **وقت الإنشاء:** `{created_at}`\n"
                            "‏┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉┉\n"
                            "📡 **Channel:** @SORS_RECO"
                        )
                        await event.respond(result_msg)
                        await client.send_message("me", f"🚨 **معلومات بوتك الجديد:**\n\n{result_msg}")
                        await event.delete()
                    else:
                        await event.edit(f"❌ **فشل الطلب:**\n{resp.text[:100]}")

            except Exception as e:
                await event.edit(f"❌ **حدث خطأ:**\n`{str(e)}` ")
