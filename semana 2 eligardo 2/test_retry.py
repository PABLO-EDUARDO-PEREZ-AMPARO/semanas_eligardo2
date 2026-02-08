import unittest
import requests
from unittest.mock import patch, Mock
# Importamos el decorador que acabamos de crear
from retry import with_retry

# Clase dummy para probar el decorador aislado del cliente real
class APIClientDummy:
    @with_retry(max_retries=2, base_delay=0.1)
    def obtener_datos(self):
        return requests.get("http://api-fake.com/data")

class TestRetryModule(unittest.TestCase):
    
    def setUp(self):
        self.dummy = APIClientDummy()

    @patch('requests.get')
    def test_reintento_exitoso_tras_error_servidor(self, mock_get):
        """Prueba que el decorador reintenta en errores 500 y tiene éxito final."""
        print("\n--- TEST: Reintento tras Error 500 ---")
        
        # Configurar secuencia: Falla (500) -> Falla (500) -> Éxito (200)
        mock_500 = Mock()
        mock_500.status_code = 500
        mock_500.raise_for_status.side_effect = requests.HTTPError("Server Error", response=mock_500)
        
        mock_200 = Mock()
        mock_200.status_code = 200
        mock_200.json.return_value = {"status": "ok"}

        # Simulamos que requests.get lanza error las primeras veces
        mock_get.side_effect = [
            requests.exceptions.ConnectionError("Red caída"), 
            mock_200 # Al segundo intento funciona
        ]

        resultado = self.dummy.obtener_datos()
        
        self.assertEqual(resultado.status_code, 200)
        self.assertEqual(mock_get.call_count, 2) # 1 fallo + 1 éxito
        print("✅ Decorador funcionó: Reintentó correctamente.")

    @patch('requests.get')
    def test_no_reintentar_error_cliente(self, mock_get):
        """Prueba que el decorador NO reintenta en errores 404."""
        print("\n--- TEST: No reintentar 404 ---")
        
        mock_404 = Mock()
        mock_404.status_code = 404
        # Simulamos que requests.get devuelve un 404 y raise_for_status lanza el error
        error_404 = requests.HTTPError("Not Found", response=mock_404)
        mock_get.side_effect = error_404 

        # Esperamos que lance el error inmediatamente sin reintentar
        with self.assertRaises(requests.HTTPError):
            self.dummy.obtener_datos()
            
        self.assertEqual(mock_get.call_count, 1) # Solo debió intentar 1 vez
        print("✅ Decorador funcionó: Abortó en error de cliente (404).")

if __name__ == '__main__':
    unittest.main()