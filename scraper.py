from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
CORS(app, origins="*")

@app.route('/pharmacies')
def get_pharmacies():
    try:
        url = "https://agadir.pharmacieenpermanence.ma/"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        pharmacies = []

        # Chercher toutes les pharmacies dans la page
        cards = soup.find_all('div', class_=lambda x: x and 'pharmacie' in x.lower())
        if not cards:
            cards = soup.find_all('article')
        if not cards:
            cards = soup.find_all('div', class_=lambda x: x and 'card' in x.lower())

        for card in cards:
            name = ''
            address = ''
            phone = ''
            lat, lng = None, None

            # Nom
            h = card.find(['h1','h2','h3','h4','strong'])
            if h:
                name = h.get_text(strip=True)

            # Téléphone
            tel = card.find('a', href=lambda x: x and 'tel:' in x)
            if tel:
                phone = tel.get('href','').replace('tel:','').strip()

            # Adresse
            p = card.find('p')
            if p:
                address = p.get_text(strip=True)

            # GPS depuis lien Google Maps
            gmap = card.find('a', href=lambda x: x and 'maps' in str(x))
            if gmap:
                href = gmap.get('href','')
                if 'destination=' in href:
                    try:
                        coords = href.split('destination=')[1].split('&')[0]
                        lat, lng = map(float, coords.split(','))
                    except: pass

            if name and len(name) > 2:
                pharmacies.append({
                    'name': name if 'Pharmacie' in name else 'Pharmacie ' + name,
                    'address': address or 'Agadir',
                    'phone': phone,
                    'lat': lat or 30.4202,
                    'lng': lng or -9.5992,
                    'h24': False
                })

        if not pharmacies:
            return jsonify({'status': 'error', 'message': 'No pharmacies found'})

        return jsonify({'status': 'ok', 'data': pharmacies})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
