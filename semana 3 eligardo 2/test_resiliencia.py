import unittest
import requests
from unittest.mock import patch, Mock
from cliente_ecomarket import EcoMarketClient, ErrorNegocio

class TestResiliencia(unittest.TestCase):
    
    def setUp(self):
        self.cliente = EcoMarketClient("http://api-fake.com", "token-dummy")

    @patch('requests.Session.request') 
    def test_reintento_exitoso_tras_fallo_500(self, mock_request):
        print("\n--- TEST: Recuperación tras error de servidor ---")
        
        # 1. Error 500
        mock_error = Mock()
        mock_error.status_code = 500
        mock_error.raise_for_status.side_effect = requests.HTTPError("Error 500", response=mock_error)

        # 2. Éxito (Debe tener los campos que exige tu modelo Producto)
        mock_exito = Mock()
        mock_exito.status_code = 200
        mock_exito.json.return_value = {
            "id": "1", 
            "nombre": "Miel", 
            "precio": 10.0, 
            "categoria": "miel",
            "stock": 50,      # Asumo que tu modelo Pydantic pide esto
            "disponible": True
        }

        # Secuencia: Falla -> Falla -> Éxito
        mock_request.side_effect = [
            requests.exceptions.ConnectionError("Caída red"), 
            mock_error.raise_for_status.side_effect,
            mock_exito
        ]

        # Ejecutar
        prod = self.cliente.obtener_producto("1")
        
        self.assertIsNotNone(prod)
        self.assertEqual(prod.nombre, "Miel")
        self.assertEqual(mock_request.call_count, 3) # Verifica que reintentó
        print("✅ Reintentos funcionando correctamente.")

    @patch('requests.Session.request')
    def test_no_reintentar_404(self, mock_request):
        print("\n--- TEST: No reintentar en 404 ---")
        
        # Respuesta 404
        mock_404 = Mock()
        mock_404.status_code = 404
        # IMPORTANTE: Si es 404, tu código _request devuelve None antes de procesar JSON
        mock_request.return_value = mock_404

        resultado = self.cliente.obtener_producto("999")
        
        self.assertIsNone(resultado)
        self.assertEqual(mock_request.call_count, 1) # Solo 1 intento
        print("✅ 404 manejado correctamente sin reintentos.")

if __name__ == '__main__':
    unittest.main()