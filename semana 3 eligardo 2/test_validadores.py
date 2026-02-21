import unittest
from validadores import validar_producto, ValidationError

class TestValidacionesEcoMarket(unittest.TestCase):

    def setUp(self):
        """Este método se ejecuta antes de cada test. Prepara un dato válido base."""
        self.producto_base = {
            "id": 1,
            "nombre": "Manzana",
            "precio": 25.50,
            "categoria": "frutas",
            "productor": {"id": 10, "nombre": "Huerta A"},
            "disponible": True,
            "creado_en": "2024-01-01T12:00:00Z"
        }

    # --- LOS 5 CASOS DE FALLO REQUERIDOS ---

    def test_fallo_campo_requerido(self):
        """Caso 1: Debe fallar si falta un campo obligatorio (ej. precio)"""
        del self.producto_base["precio"]
        
        # assertRaises verifica que la función lance la excepción ValidationError
        with self.assertRaises(ValidationError) as cm:
            validar_producto(self.producto_base)
        print(f"✅ Test 1 Pasó: Detectó falta de campo -> {cm.exception}")

    def test_fallo_tipo_dato(self):
        """Caso 2: Debe fallar si el tipo de dato es incorrecto (ej. precio es texto)"""
        self.producto_base["precio"] = "veinte pesos" # Debería ser float
        
        with self.assertRaises(ValidationError) as cm:
            validar_producto(self.producto_base)
        print(f"✅ Test 2 Pasó: Detectó tipo incorrecto -> {cm.exception}")

    def test_fallo_regla_negocio_precio(self):
        """Caso 3: Debe fallar si el precio es negativo o cero"""
        self.producto_base["precio"] = -50.0
        
        with self.assertRaises(ValidationError) as cm:
            validar_producto(self.producto_base)
        print(f"✅ Test 3 Pasó: Detectó precio negativo -> {cm.exception}")

    def test_fallo_categoria_invalida(self):
        """Caso 4: Debe fallar si la categoría no está permitida"""
        self.producto_base["categoria"] = "electronica" # No existe en EcoMarket
        
        with self.assertRaises(ValidationError) as cm:
            validar_producto(self.producto_base)
        print(f"✅ Test 4 Pasó: Detectó categoría inválida -> {cm.exception}")

    def test_fallo_productor_incompleto(self):
        """Caso 5: Debe fallar si el objeto anidado productor está incompleto"""
        self.producto_base["productor"] = {"solo_id": 1} # Le falta el nombre
        
        with self.assertRaises(ValidationError) as cm:
            validar_producto(self.producto_base)
        print(f"✅ Test 5 Pasó: Detectó productor incompleto -> {cm.exception}")

    # --- CASO DE ÉXITO (Para confirmar que sí funciona cuando todo está bien) ---
    def test_exito_producto_valido(self):
        """Caso Extra: Un producto válido no debe lanzar error"""
        resultado = validar_producto(self.producto_base)
        self.assertEqual(resultado["nombre"], "Manzana")
        print("✅ Test Extra Pasó: Producto válido aceptado correctamente.")

if __name__ == '__main__':
    print("\n--- 🧪 EJECUTANDO SUITE DE PRUEBAS DE VALIDACIÓN ---")
    # verbosity=2 nos da más detalles en la terminal
    unittest.main(verbosity=2)