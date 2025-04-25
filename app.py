from flask import Flask, render_template, request, redirect, url_for
from openai import AzureOpenAI
import os
import requests
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
                  No text, no branding, logos, or any extra elements. \
                  Only a clean and aesthetically pleasing artistic background."

        for _ in range(3):
            result = client.images.generate(
                model="dalle3",
                prompt=prompt,
                n=1
            )

            # Fix: result.data[0].url olarak erişim sağlanır
            image_url = result.data[0].url  # Bu şekilde doğru erişim sağlanır
            background_urls.append(image_url)

        return render_template('select_background.html', background_urls=background_urls)

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

        # Arka plan resmini indir
        response = requests.get(background_url)
        if response.status_code == 200:
            background_image = Image.open(requests.get(background_url, stream=True).raw)
        else:
            return "Failed to fetch background image", 500

        card_width, card_height = 1024, 640
        background_image = background_image.resize((card_width, card_height))

        card = Image.new("RGB", (card_width, card_height), "white")
        card.paste(background_image, (0, 0))

        draw = ImageDraw.Draw(card)

        try:
            font = ImageFont.truetype("arialbd.ttf", 50)  # Arial Bold fontu
        except IOError:
            font = ImageFont.load_default()  # Eğer Arial Bold yoksa varsayılan fontu kullan

        # Yazı yerleşimleri
        draw.text((80, 450), card_number, fill="white", font=font)  # Kart Numarası
        draw.text((80, 500), cardholder_name.upper(), fill="white", font=font)  # Kart Sahibinin Adı
        draw.text((80, 550), f"EXP: {expiry_date}", fill="white", font=font)  # Son Kullanma Tarihi 

        output_path = "static/final_card.png"
        card.save(output_path)

        return render_template('result.html', final_card_url=output_path,
                               card_number=card_number, expiry_date=expiry_date, cardholder_name=cardholder_name)

    except Exception as e:
        return f"An error occurred: {e}", 500

if __name__ == '__main__':
    app.run(debug=True)


print(result)
