from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os
import re

app = Flask(__name__)
CORS(app, origins="*")

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

            # Adresse
            parent = h2.find_parent()
            address = 'Agadir'
            if parent:
                p = parent.find('p')
                if p:
                    address = p.get_text(strip=True)

            # Téléphone
            tel_tag = h2.find_next('a', href=lambda x: x and 'tel:' in x)
            phone = ''
            if tel_tag:
                phone = tel_tag.get('href', '').replace('tel:', '').strip()

            # GPS depuis lien Google Maps
            if not lat:
                gmap = h2.find_next('a', href=lambda x: x and 'google.com/maps' in str(x))
                if gmap:
                    gmap_href = gmap.get('href', '')
                    if 'destination=' in gmap_href:
                        try:
                            coords = gmap_href.split('destination=')[1].split('&')[0]
                            lat, lng = map(float, coords.split(','))
                        except: pass

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
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
