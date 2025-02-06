from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime, timedelta
import asyncio
import re

# Ayarlar
TOKEN = "--------------"
URL = 'https://kultur.istanbul/etkinlikler/#events'

# Tarih ve saat regex patternleri
DATE_PATTERN = r'\d{2}-\d{2}-\d{4}'
TIME_PATTERN = r'\d{2}:\d{2}'

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text.lower()
    
    if user_message == "bugun hangi etkinlik var":
        events = await asyncio.get_event_loop().run_in_executor(None, scrape_events)
        today = datetime.now().date()
        
        response = "🎉 İşte bugünün etkinlikleri:\n\n"
        event_count = 0
        
        for event in events:
            start_date, end_date = parse_dates(event['date'])
            if not start_date or not end_date:
                continue
            
            if start_date.date() <= today <= end_date.date():
                event_count += 1
                tags = " | ".join(event['tags'])
                date_display = format_date_display(start_date, end_date)
                
                response += (
                    f"🎤 **{event['name']}**\n"
                    f"🗓️ {date_display}\n"
                    f"📍 {event['location']}\n"
                    f"🏷️ {event['type']} | {tags}\n\n"
                )
        
        if event_count == 0:
            await update.message.reply_text("🚨 Bugün için etkinlik bulunamadı!")
        else:
            await update.message.reply_text(response, parse_mode="Markdown")
            
    else:
        await update.message.reply_text("Merhaba! Güncel etkinlikler için 'bugun hangi etkinlik var' yazabilirsin 😊")

def scrape_events():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome(options=options)
    driver.get(URL)
    
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "wpem-event-box-col"))
        )
    except Exception as e:
        print(f"Element yükleme hatası: {str(e)}")
        driver.quit()
        return []
    
    elements = driver.find_elements(By.CLASS_NAME, "wpem-event-box-col")
    events = []
    
    for element in elements:
        try:
            event = parse_event(element)
            if event['date'] and event['location']:
                events.append(event)
        except Exception as e:
            print(f"Etkinlik ayrıştırma hatası: {str(e)}")
            continue
    
    driver.quit()
    return events

def parse_event(element):
    text = element.text.split('\n')
    event = {
        'name': text[0],
        'date': None,
        'location': None,
        'type': None,
        'tags': []
    }
    
    current_field = 'date'
    for line in text[1:]:
        line = line.strip()
        
        if re.search(DATE_PATTERN, line):
            event['date'] = line
            current_field = 'location'
        elif current_field == 'location':
            event['location'] = line
            current_field = 'type'
        elif current_field == 'type' and line:
            event['type'] = line
            current_field = 'tags'
        elif current_field == 'tags' and line:
            # Birleşik etiketleri ayır (Örnek: "Atölye & EğitimÜcretsiz")
            tags = re.findall(
                r'[A-Z][a-zİÇŞĞÜÖıçşğüö]+(?:[\s&]+[A-Z][a-zİÇŞĞÜÖıçşğüö]+)*', 
                line
            )
            event['tags'].extend(tags)
    
    return event

def parse_dates(date_str):
    try:
        parts = date_str.split(' - ')
        start_str = parts[0].strip()
        end_str = parts[1].strip() if len(parts) > 1 else start_str

        def parse_single_date(date_str):
            if re.search(TIME_PATTERN, date_str):
                return datetime.strptime(date_str, "%d-%m-%Y %H:%M")
            return datetime.strptime(date_str, "%d-%m-%Y") + timedelta(hours=23, minutes=59)

        start_date = parse_single_date(start_str)
        
        try:
            end_date = parse_single_date(end_str)
        except ValueError:
            if re.search(DATE_PATTERN, end_str):
                end_date = datetime.strptime(end_str, "%d-%m-%Y") + timedelta(hours=23, minutes=59)
            else:
                end_date = start_date.replace(
                    hour=int(end_str.split(':')[0]),
                    minute=int(end_str.split(':')[1])
                )

        return start_date, end_date
    
    except Exception as e:
        print(f"Tarih ayrıştırma hatası: {date_str} - {str(e)}")
        return None, None

def format_date_display(start, end):
    if start.date() == end.date():
        if start.time() == end.time():
            return start.strftime("%d-%m-%Y %H:%M")
        return f"{start.strftime('%d-%m-%Y %H:%M')} - {end.strftime('%H:%M')}"
    return f"{start.strftime('%d-%m-%Y %H:%M')} - {end.strftime('%d-%m-%Y %H:%M')}"

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot aktif! CTRL+C ile durdurabilirsiniz...")
    app.run_polling()

if __name__ == "__main__":
    main()