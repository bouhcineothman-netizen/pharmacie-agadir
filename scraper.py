from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)
CORS(app)

# Adresses connues par nom de pharmacie
ADRESSES = {
    "Immeubles Assafa": "Près du café KENYA, Hay Al Moammadi, Agadir",
    "El Qods": "Avenue Al Imam Chafii, Agadir",
    "Allal Fassi": "Rue Allal Fassi N°23, ERAC, Bouargane, Agadir",
    "Bousaid": "Cité El Farah, Agadir",
    "Anezi": "Bd Mohamed V, Boutique N°10, Hotel Anezi, Agadir",
    "Du Quartier": "Angle Av. Moulay Abdellah et Rue Sidi Bouknadel, Agadir",
}

@app.route('/pharmacies')
def get_pharmacies():
    try:
        url = "https://pharmacie.omnidoc.ma/liste-des-villes/AGADIR"
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get(url, headers=headers, timeout=10)
        r.encoding = 'utf-8'
        soup = BeautifulSoup(r.text, 'html.parser')

        pharmacies = []
        for h2 in soup.find_all('h2'):
            a = h2.find('a')
            if not a: continue

            full_name = a.text.strip()
            name = full_name.split(' - ')[0].strip()
            href = a.get('href', '')

            lat, lng = None, None
            if 'lat=' in href:
                try:
                    lat = float(href.split('lat=')[1].split('&')[0])
                    lng = float(href.split('lng=')[1])
                except: pass

            tel_tag = h2.find_next('a', href=lambda x: x and 'tel:' in x)
            phone = ''
            if tel_tag:
                phone = tel_tag.get('href', '').replace('tel:', '').strip()

            address = ADRESSES.get(name, 'Agadir')

            if name and lat:
                pharmacies.append({
                    'name': 'Pharmacie ' + name,
                    'address': address,
                    'phone': phone,
                    'lat': lat,
                    'lng': lng,
                    'h24': False
                })

        return jsonify({'status': 'ok', 'data': pharmacies})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    import os
port = int(os.environ.get('PORT', 5000))
app.run(debug=False, host='0.0.0.0', port=port)
