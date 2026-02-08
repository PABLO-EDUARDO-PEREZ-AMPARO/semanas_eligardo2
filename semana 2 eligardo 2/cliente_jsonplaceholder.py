from urllib import response
import requests
import json

# 1. CAMBIO CLAVE: Usamos la API pública de pruebas
BASE_URL = "https://jsonplaceholder.typicode.com"
TIMEOUT_SEG = 5

def listar_posts():
    # En lugar de /productos, pedimos /posts
    url = f"{BASE_URL}/posts"
    print(f"📡 Conectando a {url}...")

    try:
        response = requests.get(url, timeout=TIMEOUT_SEG)
        response.raise_for_status()
        posts = response.json()
        
        # Limitamos a 3 para no llenar la consola
        print(f"✅ Éxito! Se descargaron {len(posts)} posts. Mostrando los primeros 3:")
        for post in posts[:3]:
            # Adaptamos los campos: 'title' en vez de 'nombre'
            print(f"   - [ID: {post['id']}] {post['title'][:30]}...")

    except Exception as e:
        print(f"💥 Error: {e}")

def crear_post_simulado():
    url = f"{BASE_URL}/posts"
    print(f"\n🚀 Intentando crear un post...")

    # Datos adaptados a lo que espera JSONPlaceholder
    nuevo_post = {
        "title": "Mi Primer Post desde Python",
        "body": "Esto es una prueba de la API",
        "userId": 1
    }

    try:
        response = requests.post(url, json=nuevo_post, timeout=TIMEOUT_SEG)
        
        
        if response.status_code == 201:
            data = response.json()
            # OJO: JSONPlaceholder te devuelve ID 101 siempre para simular creación
            print(f"✅ ÉXITO: El servidor respondió 201 Created.")
            print(f"   ID asignado: {data['id']}")
            print("   (Nota: En JSONPlaceholder los datos no se guardan realmente, solo se simula)")
        else:
            print(f"❌ Error: {response.status_code}")

    except Exception as e:
        print(f"Error de red: {e}")

if __name__ == "__main__":
    listar_posts()
    crear_post_simulado()

   