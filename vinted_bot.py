import requests
from bs4 import BeautifulSoup
import time
import os

# ==== KONFIGURACJA ====
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CHAT_ID = os.environ["CHAT_ID"]

SEARCH_URLS = [
    "https://www.vinted.pl/vetements?search_text=bleach%20manga",
    "https://www.vinted.pl/vetements?search_text=bleach%20funko"
]

CHECK_INTERVAL = 300  # 5 minut
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "pl-PL,pl;q=0.9"  # wymuszenie polskiego serwera
}

seen_items = set()


def send_telegram_message(title, price, url, image_url):
    caption = f"<b>{title}</b>\n💰 {price}\n🔗 <a href='{url}'>Zobacz ofertę</a>"
    api_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    payload = {
        "chat_id": CHAT_ID,
        "photo": image_url,
        "caption": caption,
        "parse_mode": "HTML"
    }
    try:
        r = requests.post(api_url, data=payload, timeout=10)
        if not r.ok:
            print("Błąd wysyłania do Telegram:", r.text)
    except Exception as e:
        print("Wyjątek wysyłania do Telegram:", e)


def get_listings(search_url):
    try:
        r = requests.get(search_url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        items = []
        for link_tag in soup.select('a[href^="/items/"]'):
            href = link_tag.get("href")
            if not href:
                continue
            full_url = "https://www.vinted.pl" + href.split("?")[0]
            if full_url in seen_items:
                continue

            item_details = get_offer_details(full_url)
            if item_details:
                items.append((full_url, *item_details))
        return items
    except Exception as e:
        print("Błąd pobierania listy:", e)
        return []


def get_offer_details(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        title = soup.select_one('meta[property="og:title"]')
        title = title.get("content") if title else "Brak tytułu"

        image = soup.select_one('meta[property="og:image"]')
        image = image.get("content") if image else ""

        price_meta = soup.select_one('meta[property="product:price:amount"]')
        price = price_meta.get("content") + " zł" if price_meta else "Brak ceny"

        return title, price, image
    except Exception as e:
        print("Błąd pobierania szczegółów:", e)
        return None


def main():
    print("Bot Vinted uruchomiony. Oczekiwanie na nowe oferty...")
    while True:
        for url in SEARCH_URLS:
            new_items = get_listings(url)
            for full_url, title, price, image in new_items:
                seen_items.add(full_url)
                send_telegram_message(title, price, full_url, image)
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
