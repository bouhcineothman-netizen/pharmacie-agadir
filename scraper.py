from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__)
CORS(app, origins="*")

def scrape_omnidoc():
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
        parent = h2.find_parent()
        address = 'Agadir'
        if parent:
            p = parent.find('p')
            if p: address = p.get_text(strip=True)
        gmap = h2.find_next('a', href=lambda x: x and 'google.com/maps' in str(x))
        if gmap and not lat:
            gmap_href = gmap.get('href', '')
            if 'destination=' in gmap_href:
                try:
                    coords = gmap_href.split('destination=')[1].split('&')[0]
                    lat, lng = map(float, coords.split(','))
                except: pass
        tel_tag = h2.find_next('a', href=lambda x: x and 'tel:' in x)
        phone = ''
        if tel_tag:
            phone = tel_tag.get('href', '').replace('tel:', '').strip()
        if name and lat:
            pharmacies.append({'name': 'Pharmacie ' + name, 'address': address, 'phone': phone, 'lat': lat, 'lng': lng, 'h24': False})
    return pharmacies

def scrape_permanence():
    url = "https://agadir.pharmacieenpermanence.ma/"
    headers = {'User-Agent': 'Mozilla/5.0'}
    r = requests.get(url, headers=headers, timeout=10)
    r.encoding = 'utf-8'
    soup = BeautifulSoup(r.text, 'html.parser')
    pharmacies = []
    cards = soup.find_all('div', class_=lambda x: x and 'card' in x.lower())
    if not cards:
        cards = soup.find_all('article')
    for card in cards:
        name = ''
        h = card.find(['h1','h2','h3','h4','strong'])
        if h: name = h.get_text(strip=True)
        tel = card.find('a', href=lambda x: x and 'tel:' in x)
        phone = tel.get('href','').replace('tel:','').strip() if tel else ''
        gmap = card.find('a', href=lambda x: x and 'maps' in str(x))
        lat, lng = 30.4202, -9.5992
        if gmap:
            href = gmap.get('href','')
            if 'destination=' in href:
                try:
                    coords = href.split('destination=')[1].split('&')[0]
                    lat, lng = map(float, coords.split(','))
                except: pass
        if name and len(name) > 2:
            pharmacies.append({'name': name if 'Pharmacie' in name else 'Pharmacie ' + name, 'address': 'Agadir', 'phone': phone, 'lat': lat, 'lng': lng, 'h24': False})
    return pharmacies

@app.route('/pharmacies')
def get_pharmacies():
    try:
        all_pharmacies = scrape_omnidoc()
        
        # Ajouter celles de permanence qui ne sont pas déjà dans omnidoc
        permanence = scrape_permanence()
        noms_existants = [p['name'].lower() for p in all_pharmacies]
        for p in permanence:
            if p['name'].lower() not in noms_existants:
                all_pharmacies.append(p)
                noms_existants.append(p['name'].lower())
        
        return jsonify({'status': 'ok', 'data': all_pharmacies})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=False, host='0.0.0.0', port=port)
