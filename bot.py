import telebot
from telebot import types
import json
import os
from datetime import datetime, time
import threading
import time as t
import requests

TOKEN = "8044949537:AAGL3VXx6UFQgdS01pSMzLYnXIMG4zzc3aE"
bot = telebot.TeleBot(TOKEN)

# JSON fayllar
DATA_FILE_RASM = "rasmlar.json"
DATA_FILE_VIDEO = "videolar.json"
LIMIT_FILE = "limit.json"
PREMIUM_FILE = "premium.json"
TOLOV_FILE = "tolovlar.json"

# Premium narx
PREMIUM_NARX = 50000
PREMIUM_KARTA = "9860 3501 4110 5725"

# JSON fayllarni yuklash
def load_json(filename):
    try:
        if os.path.exists(filename):
            with open(filename, "r", encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"{filename} yuklashda xato: {e}")
    return {}

def save_json(filename, data):
    try:
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"{filename} saqlashda xato: {e}")
        return False

# Ma'lumotlarni yuklash
rasmlar = load_json(DATA_FILE_RASM)
videolar = load_json(DATA_FILE_VIDEO)
limits = load_json(LIMIT_FILE)
premium_users = load_json(PREMIUM_FILE)
tolovlar = load_json(TOLOV_FILE)

# ESKI XABARLARNI O'CHIRISH FUNKSIYASI
def clear_chat(message, delete_count=10):
    try:
        chat_id = message.chat.id
        message_id = message.message_id
        
        # Oldingi xabarlarni o'chirish
        for i in range(1, delete_count + 1):
            try:
                bot.delete_message(chat_id, message_id - i)
            except Exception as e:
                # Xabarni o'chirishda xato bo'lsa, davom et
                continue
    except Exception as e:
        print(f"Xabarlarni o'chirishda xato: {e}")

# Foydalanuvchi limitini olish
def get_user_limit(user_id):
    user_id = str(user_id)
    if user_id in premium_users:
        return "♾️ Cheksiz (Premium)"
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id in limits and limits[user_id]["date"] == today:
        used = limits[user_id]["count"]
        return f"{used}/5 (Kunlik)"
    else:
        return "0/5 (Kunlik)"

# Limitni tekshirish
def check_limit(user_id):
    user_id = str(user_id)
    
    # Premium foydalanuvchilar uchun cheklov yo'q
    if user_id in premium_users:
        return True
    
    # Vaqtni tekshirish (05:00 - 23:59)
    now = datetime.now().time()
    start_time = time(5, 0)
    end_time = time(23, 59, 59)
    
    if now < start_time or now > end_time:
        return False
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in limits or limits[user_id]["date"] != today:
        limits[user_id] = {"date": today, "count": 0}
        save_json(LIMIT_FILE, limits)
    
    return limits[user_id]["count"] < 5

def increment_limit(user_id):
    user_id = str(user_id)
    if user_id in premium_users:
        return
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user_id not in limits or limits[user_id]["date"] != today:
        limits[user_id] = {"date": today, "count": 0}
    
    limits[user_id]["count"] += 1
    save_json(LIMIT_FILE, limits)

# O'chirish va premium sozlash
pending_delete = {}
premium_pending = {}
user_states = {}

# MENYUGA QAYTISH FUNKSIYASI
def return_to_menu(message):
    user_id = str(message.from_user.id)
    user_states[user_id] = "menu"
    
    # 1 soniya kutib, keyin menyuga qaytish
    t.sleep(1)
    start(message)

# /start komandasi
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = str(message.from_user.id)
        user_states[user_id] = "menu"
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        # Klaviatura yaratish
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        
        if user_id in premium_users:
            btn1 = types.KeyboardButton("📷 Rasm saqlash")
            btn2 = types.KeyboardButton("🎥 Video saqlash")
            btn3 = types.KeyboardButton("📁 Mening fayllarim")
            btn4 = types.KeyboardButton("🗑️ Fayl o'chirish")
            btn5 = types.KeyboardButton("📊 Mening limitim")
            btn6 = types.KeyboardButton("💎 Premium (Active)")
            
            markup.add(btn1, btn2)
            markup.add(btn3, btn4)
            markup.add(btn5, btn6)
        else:
            btn1 = types.KeyboardButton("📷 Rasm saqlash")
            btn2 = types.KeyboardButton("🎥 Video saqlash")
            btn3 = types.KeyboardButton("📁 Mening fayllarim")
            btn4 = types.KeyboardButton("🗑️ Fayl o'chirish")
            btn5 = types.KeyboardButton("📊 Mening limitim")
            btn6 = types.KeyboardButton("💎 Premium")
            
            markup.add(btn1, btn2)
            markup.add(btn3, btn4)
            markup.add(btn5, btn6)
        
        status = "💎 PREMIUM" if user_id in premium_users else "🆓 Oddiy"
        welcome_text = (
            f"🎉 *Xotiraga Saqla Botiga Xush Kelibsiz!*\n\n"
            f"👤 Sizning holatingiz: {status}\n"
            f"📊 Limit: {get_user_limit(user_id)}\n\n"
            f"*Bot imkoniyatlari:*\n"
            f"• 📷 Rasm saqlash\n"
            f"• 🎥 Video saqlash\n"
            f"• 📁 Fayllarni ko'rish\n"
            f"• 🗑️ Fayllarni o'chirish\n"
            f"• 💎 Premium imkoniyatlari\n\n"
            f"Quyidagi tugmalardan foydalaning:"
        )
        
        bot.send_message(
            message.chat.id, 
            welcome_text,
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Start funksiyasida xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# 📷 Rasm saqlash tugmasi
@bot.message_handler(func=lambda message: message.text == "📷 Rasm saqlash")
def rasm_saqlash(message):
    try:
        user_id = str(message.from_user.id)
        user_states[user_id] = "waiting_photo"
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if not check_limit(user_id):
            error_text = (
                "❌ *Kunlik limit tugadi!*\n\n"
                "Ertaga soat 05:00 da yangilanadi.\n"
                "💎 Premium sotib olish orqali cheksiz foydalaning!"
            )
            bot.send_message(message.chat.id, error_text, parse_mode='Markdown')
            user_states[user_id] = "menu"
            t.sleep(3)
            return_to_menu(message)
            return
        
        if user_id in premium_users:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
            btn1 = types.KeyboardButton("📸 1 ta rasm")
            btn2 = types.KeyboardButton("📸 10 ta rasm")
            btn3 = types.KeyboardButton("⬅️ Ortga")
            
            markup.add(btn1, btn2)
            markup.add(btn3)
            
            bot.send_message(
                message.chat.id, 
                "📸 *Nechta rasm yuklamoqchisiz?*\n\n"
                "💎 *Premium imkoniyati:* Bir vaqtda 10 ta rasm yuklash",
                reply_markup=markup, 
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id, 
                "📸 *Rasm yuboring...*\n\n"
                "ℹ️ Iltimos, bitta rasm yuboring. "
                "Rasm qabul qilingandan so'ng unga nom berasiz.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        print(f"Rasm saqlashda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Premium: Rasm sonini tanlash
@bot.message_handler(func=lambda message: message.text in ["📸 1 ta rasm", "📸 10 ta rasm"])
def premium_rasm_soni(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if message.text == "📸 1 ta rasm":
            user_states[user_id] = "waiting_single_photo"
            bot.send_message(
                message.chat.id, 
                "📸 *1 ta rasm yuboring...*\n\n"
                "ℹ️ Iltimos, bitta rasm yuboring.",
                parse_mode='Markdown'
            )
        else:
            user_states[user_id] = "waiting_multiple_photos"
            if user_id not in rasmlar:
                rasmlar[user_id] = {}
            rasmlar[user_id]['temp_photos'] = []
            save_json(DATA_FILE_RASM, rasmlar)
            bot.send_message(
                message.chat.id, 
                "📸 *10 ta rasm yuboring...*\n\n"
                "ℹ️ Iltimos, 10 ta rasm yuboring. "
                "Barcha rasmlar qabul qilingandan so'ng ularga umumiy nom berasiz.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        print(f"Rasm sonini tanlashda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Rasm qabul qilish
@bot.message_handler(content_types=['photo'])
def get_photo(message):
    try:
        user_id = str(message.from_user.id)
        
        current_state = user_states.get(user_id)
        if current_state not in ["waiting_photo", "waiting_single_photo", "waiting_multiple_photos"]:
            return
        
        if not check_limit(user_id):
            bot.send_message(
                message.chat.id, 
                "❌ *Kunlik limit tugadi!*\n\n"
                "Ertaga soat 05:00 da yangilanadi.",
                parse_mode='Markdown'
            )
            user_states[user_id] = "menu"
            t.sleep(2)
            return_to_menu(message)
            return
        
        file_id = message.photo[-1].file_id
        
        if current_state == "waiting_multiple_photos":
            if user_id not in rasmlar:
                rasmlar[user_id] = {}
            if 'temp_photos' not in rasmlar[user_id]:
                rasmlar[user_id]['temp_photos'] = []
            
            rasmlar[user_id]['temp_photos'].append(file_id)
            save_json(DATA_FILE_RASM, rasmlar)
            
            count = len(rasmlar[user_id]['temp_photos'])
            if count < 10:
                bot.send_message(
                    message.chat.id, 
                    f"✅ *Rasm {count}/10 qabul qilindi!*\n\n"
                    f"ℹ️ {10 - count} ta rasm qoldi.",
                    parse_mode='Markdown'
                )
            else:
                user_states[user_id] = "waiting_photo_name"
                bot.send_message(
                    message.chat.id, 
                    "✅ *10 ta rasm qabul qilindi!*\n\n"
                    "📝 Iltimos, rasmlarga nom bering:",
                    parse_mode='Markdown'
                )
        else:
            user_states[user_id] = "waiting_photo_name"
            user_states[f"{user_id}_last_photo"] = file_id
            bot.send_message(
                message.chat.id, 
                "✅ *Rasm qabul qilindi!*\n\n"
                "📝 Iltimos, rasmga nom bering:",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        print(f"Rasm qabul qilishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Rasm qabul qilishda xatolik. Iltimos, qaytadan urinib ko'ring.")

# Rasm nomini saqlash
@bot.message_handler(func=lambda message: user_states.get(str(message.from_user.id)) == "waiting_photo_name")
def save_photo_name(message):
    try:
        user_id = str(message.from_user.id)
        nom = message.text.strip()
        
        if not nom:
            bot.send_message(message.chat.id, "❌ Iltimos, nom kiriting!")
            return
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if user_id not in rasmlar:
            rasmlar[user_id] = {}
        
        if user_id in rasmlar and 'temp_photos' in rasmlar[user_id]:
            temp_photos = rasmlar[user_id]['temp_photos']
            
            # Har bir rasmga alohida nom berish
            for i, file_id in enumerate(temp_photos):
                rasmlar[user_id][f"{nom}_{i+1}"] = file_id
            
            del rasmlar[user_id]['temp_photos']
            save_json(DATA_FILE_RASM, rasmlar)
            increment_limit(user_id)
            
            bot.send_message(
                message.chat.id, 
                f"✅ *{len(temp_photos)} ta rasm saqlandi!*\n\n"
                f"📂 Asosiy nom: *{nom}*\n"
                f"📊 Rasmlar: *{nom}_1, {nom}_2, ...*\n\n"
                f"💾 Saqlangan fayllaringizni 'Mening fayllarim' bo'limida ko'rishingiz mumkin.",
                parse_mode='Markdown'
            )
        
        elif f"{user_id}_last_photo" in user_states:
            file_id = user_states[f"{user_id}_last_photo"]
            rasmlar[user_id][nom] = file_id
            save_json(DATA_FILE_RASM, rasmlar)
            increment_limit(user_id)
            
            if f"{user_id}_last_photo" in user_states:
                del user_states[f"{user_id}_last_photo"]
            
            bot.send_message(
                message.chat.id, 
                f"✅ *Rasm saqlandi!*\n\n"
                f"📂 Nomi: *{nom}*\n"
                f"💾 Saqlangan fayllaringizni 'Mening fayllarim' bo'limida ko'rishingiz mumkin.",
                parse_mode='Markdown'
            )
        
        user_states[user_id] = "menu"
        
        # 2 soniya kutib, keyin menyuga qaytish
        t.sleep(2)
        return_to_menu(message)
        
    except Exception as e:
        print(f"Rasm nomini saqlashda xato: {e}")
        bot.send_message(message.chat.id, "❌ Rasm nomini saqlashda xatolik. Iltimos, qaytadan urinib ko'ring.")

# 🎥 Video saqlash tugmasi
@bot.message_handler(func=lambda message: message.text == "🎥 Video saqlash")
def video_saqlash(message):
    try:
        user_id = str(message.from_user.id)
        user_states[user_id] = "waiting_video"
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if not check_limit(user_id):
            bot.send_message(
                message.chat.id, 
                "❌ *Kunlik limit tugadi!*\n\n"
                "Ertaga soat 05:00 da yangilanadi.",
                parse_mode='Markdown'
            )
            user_states[user_id] = "menu"
            t.sleep(2)
            return_to_menu(message)
            return
        
        bot.send_message(
            message.chat.id, 
            "🎥 *Video yuboring...*\n\n"
            "ℹ️ Iltimos, video fayl yuboring. "
            "Video qabul qilingandan so'ng unga nom berasiz.\n\n"
            "📝 *Eslatma:* Videoning hajmi katta bo'lmasligi tavsiya etiladi.",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Video saqlashda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Video qabul qilish
@bot.message_handler(content_types=['video'])
def get_video(message):
    try:
        user_id = str(message.from_user.id)
        
        if user_states.get(user_id) != "waiting_video":
            return
        
        if not check_limit(user_id):
            bot.send_message(
                message.chat.id, 
                "❌ *Kunlik limit tugadi!*\n\n"
                "Ertaga soat 05:00 da yangilanadi.",
                parse_mode='Markdown'
            )
            user_states[user_id] = "menu"
            t.sleep(2)
            return_to_menu(message)
            return
        
        file_id = message.video.file_id
        user_states[user_id] = "waiting_video_name"
        user_states[f"{user_id}_last_video"] = file_id
        
        bot.send_message(
            message.chat.id, 
            "✅ *Video qabul qilindi!*\n\n"
            "📝 Iltimos, videoga nom bering:",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Video qabul qilishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Video qabul qilishda xatolik. Iltimos, qaytadan urinib ko'ring.")

# Video nomini saqlash
@bot.message_handler(func=lambda message: user_states.get(str(message.from_user.id)) == "waiting_video_name")
def save_video_name(message):
    try:
        user_id = str(message.from_user.id)
        nom = message.text.strip()
        
        if not nom:
            bot.send_message(message.chat.id, "❌ Iltimos, nom kiriting!")
            return
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if user_id not in videolar:
            videolar[user_id] = {}
        
        if f"{user_id}_last_video" in user_states:
            file_id = user_states[f"{user_id}_last_video"]
            videolar[user_id][nom] = file_id
            save_json(DATA_FILE_VIDEO, videolar)
            increment_limit(user_id)
            
            del user_states[f"{user_id}_last_video"]
            
            bot.send_message(
                message.chat.id, 
                f"✅ *Video saqlandi!*\n\n"
                f"📂 Nomi: *{nom}*\n"
                f"💾 Saqlangan fayllaringizni 'Mening fayllarim' bo'limida ko'rishingiz mumkin.",
                parse_mode='Markdown'
            )
        
        user_states[user_id] = "menu"
        
        # 2 soniya kutib, keyin menyuga qaytish
        t.sleep(2)
        return_to_menu(message)
        
    except Exception as e:
        print(f"Video nomini saqlashda xato: {e}")
        bot.send_message(message.chat.id, "❌ Video nomini saqlashda xatolik. Iltimos, qaytadan urinib ko'ring.")

# 📁 Mening fayllarim tugmasi
@bot.message_handler(func=lambda message: message.text == "📁 Mening fayllarim")
def mening_fayllarim(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        # Rasmlarni qo'shish
        if user_id in rasmlar and any(key != 'temp_photos' for key in rasmlar[user_id].keys()):
            rasm_keys = [k for k in rasmlar[user_id].keys() if k != 'temp_photos']
            for nom in rasm_keys:
                markup.row(f"📸 {nom}")
        
        # Videolarni qo'shish
        if user_id in videolar and videolar[user_id]:
            for nom in videolar[user_id]:
                markup.row(f"🎥 {nom}")
        
        markup.row("⬅️ Ortga")
        
        if len(markup.keyboard) > 1:
            total_files = len([k for k in rasmlar.get(user_id, {}).keys() if k != 'temp_photos']) + len(videolar.get(user_id, {}))
            
            bot.send_message(
                message.chat.id, 
                f"📁 *Saqlangan fayllaringiz:*\n\n"
                f"📊 Jami fayllar: *{total_files} ta*\n"
                f"📸 Rasmlar: *{len([k for k in rasmlar.get(user_id, {}).keys() if k != 'temp_photos'])} ta*\n"
                f"🎥 Videolar: *{len(videolar.get(user_id, {}))} ta*\n\n"
                f"Quyidagi fayllardan birini tanlang:",
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id, 
                "📭 *Hech qanday saqlangan fayl topilmadi!*\n\n"
                "ℹ️ Fayl saqlash uchun:\n"
                "• '📷 Rasm saqlash' - rasmlarni saqlash\n"
                "• '🎥 Video saqlash' - videolarni saqlash",
                parse_mode='Markdown'
            )
            t.sleep(3)
            return_to_menu(message)
            
    except Exception as e:
        print(f"Fayllarni ko'rsatishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Faylni ko'rsatish
@bot.message_handler(func=lambda message: message.text.startswith(("📸 ", "🎥 ")))
def show_file_by_name(message):
    try:
        user_id = str(message.from_user.id)
        file_type = "📸" if message.text.startswith("📸 ") else "🎥"
        file_name = message.text[2:]
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if file_type == "📸":
            if user_id in rasmlar and file_name in rasmlar[user_id]:
                file_id = rasmlar[user_id][file_name]
                try:
                    bot.send_photo(
                        message.chat.id, 
                        file_id, 
                        caption=f"📸 *{file_name}*\n\n💾 Saqlangan rasm",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    bot.send_message(
                        message.chat.id, 
                        f"❌ Rasmni yuborishda xato: {str(e)}\n\n"
                        f"ℹ️ Rasm o'chirilgan yoki xatolik yuz bergan.",
                        parse_mode='Markdown'
                    )
            else:
                bot.send_message(
                    message.chat.id, 
                    f"❌ *{file_name}* nomli rasm topilmadi!\n\n"
                    f"ℹ️ Fayl o'chirilgan yoki nomi o'zgartirilgan.",
                    parse_mode='Markdown'
                )
        else:
            if user_id in videolar and file_name in videolar[user_id]:
                file_id = videolar[user_id][file_name]
                try:
                    bot.send_video(
                        message.chat.id, 
                        file_id, 
                        caption=f"🎥 *{file_name}*\n\n💾 Saqlangan video",
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    bot.send_message(
                        message.chat.id, 
                        f"❌ Videoni yuborishda xato: {str(e)}\n\n"
                        f"ℹ️ Video o'chirilgan yoki xatolik yuz bergan.",
                        parse_mode='Markdown'
                    )
            else:
                bot.send_message(
                    message.chat.id, 
                    f"❌ *{file_name}* nomli video topilmadi!\n\n"
                    f"ℹ️ Fayl o'chirilgan yoki nomi o'zgartirilgan.",
                    parse_mode='Markdown'
                )
        
        t.sleep(3)
        return_to_menu(message)
        
    except Exception as e:
        print(f"Faylni ko'rsatishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# 🗑️ Fayl o'chirish tugmasi
@bot.message_handler(func=lambda message: message.text == "🗑️ Fayl o'chirish")
def fayl_ochirish(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        
        # Rasmlarni qo'shish
        if user_id in rasmlar and any(key != 'temp_photos' for key in rasmlar[user_id]):
            for nom in [k for k in rasmlar[user_id].keys() if k != 'temp_photos']:
                markup.row(f"🗑️ {nom}")
        
        # Videolarni qo'shish
        if user_id in videolar and videolar[user_id]:
            for nom in videolar[user_id]:
                markup.row(f"🗑️ {nom}")
        
        markup.row("⬅️ Ortga")
        
        if markup.keyboard:
            total_files = len([k for k in rasmlar.get(user_id, {}).keys() if k != 'temp_photos']) + len(videolar.get(user_id, {}))
            
            bot.send_message(
                message.chat.id, 
                f"🗑️ *O'chirmoqchi bo'lgan faylni tanlang:*\n\n"
                f"📊 Jami fayllar: *{total_files} ta*\n"
                f"⚠️ Diqqat: O'chirilgan fayllarni qayta tiklab bo'lmaydi!",
                reply_markup=markup,
                parse_mode='Markdown'
            )
        else:
            bot.send_message(
                message.chat.id, 
                "❌ *O'chirish uchun fayl topilmadi!*\n\n"
                "ℹ️ Hozircha saqlangan fayllaringiz yo'q.",
                parse_mode='Markdown'
            )
            t.sleep(2)
            return_to_menu(message)
            
    except Exception as e:
        print(f"Fayl o'chirishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Fayl o'chirish tasdiq
@bot.message_handler(func=lambda message: message.text.startswith("🗑️ "))
def confirm_delete(message):
    try:
        user_id = str(message.from_user.id)
        fayl_nomi = message.text[3:]
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        # Fayl turini aniqlash
        fayl_turi = "unknown"
        if user_id in rasmlar and fayl_nomi in rasmlar[user_id]:
            fayl_turi = "rasm"
        elif user_id in videolar and fayl_nomi in videolar[user_id]:
            fayl_turi = "video"
        else:
            bot.send_message(
                message.chat.id, 
                f"❌ *{fayl_nomi}* topilmadi!\n\n"
                f"ℹ️ Fayl o'chirilgan yoki nomi o'zgartirilgan.",
                parse_mode='Markdown'
            )
            t.sleep(2)
            return_to_menu(message)
            return
        
        pending_delete[user_id] = {"nomi": fayl_nomi, "turi": fayl_turi}
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("✅ Ha", "❌ Yo'q")
        
        bot.send_message(
            message.chat.id, 
            f"❓ *{fayl_nomi}* ni rostdan ham o'chirmoqchimisiz?\n\n"
            f"⚠️ *Diqqat:* Bu amalni bekor qilib bo'lmaydi!",
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"Fayl o'chirish tasdiqida xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# O'chirish tasdiqlash
@bot.message_handler(func=lambda message: message.text in ["✅ Ha", "❌ Yo'q"])
def execute_delete(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if user_id not in pending_delete:
            return_to_menu(message)
            return
        
        if message.text == "✅ Ha":
            fayl_nomi = pending_delete[user_id]["nomi"]
            fayl_turi = pending_delete[user_id]["turi"]
            
            if fayl_turi == "rasm" and user_id in rasmlar and fayl_nomi in rasmlar[user_id]:
                del rasmlar[user_id][fayl_nomi]
                if save_json(DATA_FILE_RASM, rasmlar):
                    bot.send_message(
                        message.chat.id, 
                        f"✅ *{fayl_nomi}* rasmi o'chirildi!\n\n"
                        f"🗑️ Fayl muvaffaqiyatli o'chirildi.",
                        parse_mode='Markdown'
                    )
                    print(f"✅ {user_id} foydalanuvchi {fayl_nomi} rasmini o'chirdi")
                else:
                    bot.send_message(
                        message.chat.id, 
                        f"❌ Rasm o'chirishda xato!\n\n"
                        f"ℹ️ Iltimos, keyinroq qayta urinib ko'ring.",
                        parse_mode='Markdown'
                    )
                    
            elif fayl_turi == "video" and user_id in videolar and fayl_nomi in videolar[user_id]:
                del videolar[user_id][fayl_nomi]
                if save_json(DATA_FILE_VIDEO, videolar):
                    bot.send_message(
                        message.chat.id, 
                        f"✅ *{fayl_nomi}* videosi o'chirildi!\n\n"
                        f"🗑️ Fayl muvaffaqiyatli o'chirildi.",
                        parse_mode='Markdown'
                    )
                    print(f"✅ {user_id} foydalanuvchi {fayl_nomi} videosini o'chirdi")
                else:
                    bot.send_message(
                        message.chat.id, 
                        f"❌ Video o'chirishda xato!\n\n"
                        f"ℹ️ Iltimos, keyinroq qayta urinib ko'ring.",
                        parse_mode='Markdown'
                    )
            else:
                bot.send_message(
                    message.chat.id, 
                    f"❌ *{fayl_nomi}* topilmadi!\n\n"
                    f"ℹ️ Fayl avval o'chirilgan bo'lishi mumkin.",
                    parse_mode='Markdown'
                )
        
        del pending_delete[user_id]
        
        # 2 soniya kutib, keyin menyuga qaytish
        t.sleep(2)
        return_to_menu(message)
        
    except Exception as e:
        print(f"O'chirish amalida xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# 📊 Mening limitim tugmasi
@bot.message_handler(func=lambda message: message.text == "📊 Mening limitim")
def mening_limitim(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        now = datetime.now()
        limit_text = get_user_limit(user_id)
        
        tomorrow_5am = datetime(now.year, now.month, now.day + 1, 5, 0)
        time_left = tomorrow_5am - now
        
        hours = time_left.seconds // 3600
        minutes = (time_left.seconds % 3600) // 60
        
        if user_id in premium_users:
            status_info = "💎 *PREMIUM foydalanuvchi*\n• ♾️ Cheksiz fayl saqlash\n• 📸 10 ta rasm bir vaqtda"
        else:
            status_info = "🆓 *Oddiy foydalanuvchi*\n• 📊 Kunlik 5 ta fayl\n• 📸 1 ta rasm bir vaqtda"
        
        bot.send_message(
            message.chat.id,
            f"📊 *Sizning limitlaringiz:*\n\n"
            f"{status_info}\n\n"
            f"📈 Joriy limit: {limit_text}\n"
            f"⏰ Keyingi yangilanish: {hours} soat {minutes} daqiqadan keyin\n\n"
            f"🕒 *Ish vaqti:* 05:00 - 00:00\n"
            f"💡 *Eslatma:* Limit har kuni soat 05:00 da yangilanadi",
            parse_mode='Markdown'
        )
        
        t.sleep(4)
        return_to_menu(message)
        
    except Exception as e:
        print(f"Limit ko'rsatishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# 💎 Premium tugmasi
@bot.message_handler(func=lambda message: message.text in ["💎 Premium", "💎 Premium (Active)"])
def premium_info(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if user_id in premium_users:
            premium_data = premium_users[user_id]
            sana = premium_data.get("sana", "Noma'lum")
            ism = premium_data.get("ism", "Noma'lum")
            
            bot.send_message(
                message.chat.id, 
                f"💎 *Sizda Premium aktiv!*\n\n"
                f"👤 Ism: {ism}\n"
                f"📅 Faollashtirilgan: {sana}\n\n"
                f"✨ *Premium imkoniyatlari:*\n"
                f"• ♾️ Cheksiz fayl saqlash\n"
                f"• 📸 Bir vaqtda 10 ta rasm yuklash\n"
                f"• 🚀 Tezkor yuklash\n"
                f"• ⭐ Barcha cheklovlarsiz",
                parse_mode='Markdown'
            )
            t.sleep(3)
            return_to_menu(message)
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row("💳 To'lov qildim", "⬅️ Ortga")
            
            bot.send_message(
                message.chat.id,
                f"💎 *Premium sotib olish*\n\n"
                f"💰 Narxi: *{PREMIUM_NARX:,} so'm*\n"
                f"💳 Karta raqami: `{PREMIUM_KARTA}`\n\n"
                f"✨ *Premium imkoniyatlari:*\n"
                f"• ♾️ Cheksiz fayl saqlash\n"
                f"• 📸 Bir vaqtda 10 ta rasm yuklash\n"
                f"• 🚀 Tezkor yuklash\n"
                f"• ⭐ Barcha cheklovlarsiz\n"
                f"• 🕒 24/7 doimiy ishlash\n\n"
                f"💸 To'lov qilganingizdan so'ng *To'lov qildim* tugmasini bosing.\n"
                f"📞 To'lovni tasdiqlash uchun: @DonaterYT95",
                reply_markup=markup,
                parse_mode='Markdown'
            )
            
    except Exception as e:
        print(f"Premium info xatosi: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# To'lov tasdiq
@bot.message_handler(func=lambda message: message.text == "💳 To'lov qildim")
def tolov_tasdiq(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        premium_pending[user_id] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.row("✅ Tasdiqlash", "❌ Bekor qilish")
        
        bot.send_message(
            message.chat.id,
            "🔍 *To'lovni tekshirish*\n\n"
            "To'lov ma'lumotlari:\n"
            f"💳 Karta: `{PREMIUM_KARTA}`\n"
            f"💰 Summa: *{PREMIUM_NARX:,} so'm*\n"
            f"👤 Foydalanuvchi: {message.from_user.first_name}\n"
            f"🆔 ID: {user_id}\n\n"
            "To'lov qilganingizni tasdiqlaysizmi?\n\n"
            "⚠️ *Diqqat:* Noto'g'ri ma'lumot kiritilsa, premium aktivlanmaydi!",
            reply_markup=markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        print(f"To'lov tasdiq xatosi: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# To'lovni tasdiqlash
@bot.message_handler(func=lambda message: message.text in ["✅ Tasdiqlash", "❌ Bekor qilish"])
def tolov_natija(message):
    try:
        user_id = str(message.from_user.id)
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        if user_id not in premium_pending:
            return_to_menu(message)
            return
        
        if message.text == "✅ Tasdiqlash":
            premium_users[user_id] = {
                "sana": premium_pending[user_id],
                "ism": message.from_user.first_name,
                "username": message.from_user.username or "Noma'lum"
            }
            save_json(PREMIUM_FILE, premium_users)
            
            tolov_id = f"tolov_{int(t.time())}"
            tolovlar[tolov_id] = {
                "user_id": user_id,
                "sana": premium_pending[user_id],
                "summa": PREMIUM_NARX,
                "ism": message.from_user.first_name,
                "username": message.from_user.username or "Noma'lum"
            }
            save_json(TOLOV_FILE, tolovlar)
            
            bot.send_message(
                message.chat.id, 
                "🎉 *Tabriklaymiz! Premium aktiv qilindi!*\n\n"
                "✨ *Endi sizda quyidagi imkoniyatlar mavjud:*\n"
                "• ♾️ Cheksiz fayl saqlash\n"
                "• 📸 Bir vaqtda 10 ta rasm yuklash\n"
                "• 🚀 Tezkor yuklash\n"
                "• ⭐ Barcha cheklovlarsiz\n\n"
                "💎 Premium holatingiz yangilandi!",
                parse_mode='Markdown'
            )
            
            # Adminlarga xabar berish
            admin_xabar = (
                f"💎 *Yangi Premium foydalanuvchi!*\n\n"
                f"👤 Ism: {message.from_user.first_name}\n"
                f"🔗 Username: @{message.from_user.username or 'Noma'lum'}\n"
                f"🆔 ID: {user_id}\n"
                f"💰 Summa: {PREMIUM_NARX:,} so'm\n"
                f"📅 Sana: {premium_pending[user_id]}"
            )
            # Bu yerda admin ID sini qo'shishingiz kerak
            # bot.send_message(ADMIN_ID, admin_xabar, parse_mode='Markdown')
            
        else:
            bot.send_message(
                message.chat.id, 
                "❌ To'lov bekor qilindi.\n\n"
                "ℹ️ Agar to'lov qilgan bo'lsangiz, @DonaterYT95 ga murojaat qiling.",
                parse_mode='Markdown'
            )
        
        del premium_pending[user_id]
        
        # 2 soniya kutib, keyin menyuga qaytish
        t.sleep(2)
        return_to_menu(message)
        
    except Exception as e:
        print(f"To'lov natijasida xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Ortga qaytish
@bot.message_handler(func=lambda message: message.text == "⬅️ Ortga")
def ortga(message):
    try:
        user_id = str(message.from_user.id)
        user_states[user_id] = "menu"
        
        # Eski xabarlarni tozalash
        clear_chat(message)
        
        start(message)
        
    except Exception as e:
        print(f"Ortga qaytishda xato: {e}")
        bot.send_message(message.chat.id, "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.")

# Boshqa xabarlar
@bot.message_handler(func=lambda message: True)
def echo(message):
    try:
        user_id = str(message.from_user.id)
        if user_states.get(user_id) not in ["waiting_photo_name", "waiting_video_name"]:
            bot.send_message(
                message.chat.id, 
                "🤖 *Iltimos, menyudan tugmalarni tanlang!*\n\n"
                "ℹ️ Agar menyu ko'rinmasa, /start buyrug'ini yuboring.",
                parse_mode='Markdown'
            )
            t.sleep(2)
            return_to_menu(message)
            
    except Exception as e:
        print(f"Echo funksiyasida xato: {e}")

# Botni faol saqlash funksiyasi
def keep_alive():
    while True:
        try:
            requests.get("https://DonaterYT95.pythonanywhere.com", timeout=10)
            print(f"✅ Ping: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            print(f"❌ Ping xatosi: {e}")
        
        t.sleep(600)  # 10 daqiqa

# Background da ping qilish
ping_thread = threading.Thread(target=keep_alive, daemon=True)
ping_thread.start()

# Xatoliklar uchun global exception handler
def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    print(f"❌ Global xato: {exc_type.__name__}: {exc_value}")

# Exception handler ni o'rnatish
import sys
sys.excepthook = handle_exception

print("🚀 Bot ishga tushdi...")
print("📊 Yuklangan ma'lumotlar:")
print(f"   📸 Rasmlar: {len(rasmlar)} foydalanuvchi")
print(f"   🎥 Videolar: {len(videolar)} foydalanuvchi") 
print(f"   💎 Premium: {len(premium_users)} foydalanuvchi")
print(f"   📈 Limits: {len(limits)} foydalanuvchi")
print("⏰ Bot ishlamoqda...")

try:
    bot.polling(none_stop=True, timeout=60)
except Exception as e:
    print(f"❌ Botda kritik xato: {e}")
    print("🔄 Bot qayta ishga tushirilmoqda...")
    t.sleep(10)
    # Qayta ishga tushirish
    os.execv(sys.executable, ['python'] + sys.argv)
