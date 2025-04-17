from flask import Flask, render_template, request, redirect, url_for
from openai import AzureOpenAI
import os
import requests
import json
from PIL import Image, ImageDraw, ImageFont

# Azure OpenAI istemcisi
client = AzureOpenAI(
    api_version="2024-02-01",
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_options', methods=['POST'])
def generate_options():
    """ Kullanıcıdan alınan sanatçı ve tarz bilgisine göre 3 farklı arka plan oluşturur. """
    try:
        artist = request.form.get('artist')
        style = request.form.get('style')

        if not artist or not style:
            return "Both artist and style are required!", 400

        background_urls = []
        prompt = f"A {style} inspired abstract background in the style of {artist}. \
                  The design should fit within a size (aspect ratio 1.6:1). \
                  No text, no branding, logos, or no any extra elements. \
                  Only a clean and aesthetically pleasing artistic background ."

        for _ in range(3):
            result = client.images.generate(
                model="dalle3",
                prompt=prompt,
                n=1
            )
            json_response = json.loads(result.model_dump_json())
            image_url = json_response["data"][0]["url"]
            background_urls.append(image_url)

        return render_template('select_background.html', background_urls=background_urls, artist=artist, style=style)

    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/select_background', methods=['POST'])
def select_background():
    """ Kullanıcının seçtiği arka planı alıp `card_details.html` sayfasına yönlendirir. """
    try:
        selected_background = request.form.get('selected_background')

        if not selected_background:
            return "Please select a background!", 400

        return render_template('card_details.html', background_url=selected_background)

    except Exception as e:
        return f"An error occurred: {e}", 500

@app.route('/generate_final_card', methods=['POST'])
def generate_final_card():
    """ Kullanıcının girdiği bilgileri alarak kart tasarımını tamamlar ve indirilebilir hale getirir. """
    try:
        background_url = request.form.get('background_url')
        cardholder_name = request.form.get('cardholder_name')
        card_number = request.form.get('card_number')
        expiry_date = request.form.get('expiry_date')

        if not background_url or not cardholder_name or not card_number or not expiry_date:
            return "All fields are required!", 400

        # Arka plan resmini indir
        response = requests.get(background_url)
        background_image = Image.open(requests.get(background_url, stream=True).raw)

        # **Kredi Kartı Boyutu (1024x640 px)**
        card_width, card_height = 1024, 640
        background_image = background_image.resize((card_width, card_height))

        # **Kart Tasarımı Oluştur**
        card = Image.new("RGB", (card_width, card_height), "white")
        card.paste(background_image, (0, 0))

        # **Yazı Ekleme**
        draw = ImageDraw.Draw(card)

        try:
            font = ImageFont.truetype("arial.ttf", 40)  # Windows için Arial kullanılıyor
        except IOError:
            font = ImageFont.load_default()  # Eğer Arial yoksa varsayılan fontu kullan

        # **Bilgileri Kartın Üzerine Yerleştirme**
        draw.text((80, 500), card_number, fill="white", font=font)  # Kart Numarası
        draw.text((80, 560), f"EXP: {expiry_date}", fill="white", font=font)  # Son Kullanma Tarihi
        draw.text((80, 620), cardholder_name.upper(), fill="white", font=font)  # Kart Sahibinin Adı

        # **Kartı Kaydet**
        output_path = "static/final_card.png"
        card.save(output_path)

        return render_template('result.html', final_card_url=output_path)

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)
