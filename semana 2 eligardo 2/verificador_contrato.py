import yaml
import inspect
import re
from typing import Dict, List
from cliente_ecomarket import EcoMarketClient  # Asegúrate que este import funcione

class ContractAuditor:
    def __init__(self, openapi_path: str, client_class: type):
        self.openapi_path = openapi_path
        self.client_class = client_class
        self.spec = self._load_spec()
        self.client_methods = [m[0] for m in inspect.getmembers(client_class, predicate=inspect.isfunction)]

    def _load_spec(self) -> dict:
        with open(self.openapi_path, 'r') as f:
            return yaml.safe_load(f)

    def _map_operation_to_method(self, operation_id: str) -> str:
        """
        Intenta mapear el operationId del YAML al nombre de función Python.
        Ej: listar_productos -> listar_productos (Directo)
        """
        # Aquí podrías agregar lógica de conversión si tus nombres difieren (camelCase a snake_case)
        return operation_id.replace('-', '_')

    def verify(self):
        print(f"🕵️  AUDITORÍA DE CONTRATO: {self.spec['info']['title']} v{self.spec['info']['version']}")
        print("="*60)
        
        paths = self.spec.get('paths', {})
        total_checks = 0
        passed = 0
        
        for path, methods in paths.items():
            for method_http, details in methods.items():
                operation_id = details.get('operationId')
                if not operation_id:
                    print(f"⚠️  SKIP: {method_http.upper()} {path} no tiene 'operationId'")
                    continue

                py_method_name = self._map_operation_to_method(operation_id)
                print(f"\n🔍 Revisando Endpoint: {method_http.upper()} {path}")
                print(f"   Expecting method: {py_method_name}(...)")

                # 1. Verificar Existencia
                if py_method_name not in self.client_methods:
                    print(f"   ❌ FALTANTE: El cliente no tiene el método '{py_method_name}'")
                    continue

                # 2. Verificar Argumentos (Path Params)
                path_params = re.findall(r'\{(\w+)\}', path)
                func_sig = inspect.signature(getattr(self.client_class, py_method_name))
                func_args = list(func_sig.parameters.keys())
                
                # Excluir 'self'
                missing_args = [p for p in path_params if p not in func_args and f"{p}_p" not in func_args]
                
                if missing_args:
                    print(f"   ⚠️  PARCIAL: Método existe, pero faltan argumentos para path params: {missing_args}")
                else:
                    print(f"   ✅ CONFORMIDAD: Método implementado y firma coincide.")
                    passed += 1
                
                # 3. Análisis de Códigos de Respuesta (Heurística básica leyendo docstring o código fuente)
                source_code = inspect.getsource(getattr(self.client_class, py_method_name))
                defined_responses = details.get('responses', {}).keys()
                
                print("   📊 Cobertura de Respuestas:")
                for code in defined_responses:
                    if code == '200' or code == '201':
                        continue # El happy path se asume
                    
                    # Buscamos si el código maneja la excepción o el status code
                    if code in source_code or "raise_for_status" in source_code:
                         print(f"      🔹 {code}: Detectado manejo en código source.")
                    else:
                         print(f"      ⚠️ {code}: No se detectó manejo explícito en el código fuente.")
                
                total_checks += 1

        print("\n" + "="*60)
        print(f"RESUMEN: {passed}/{total_checks} Endpoints implementados correctamente.")

if __name__ == "__main__":
    auditor = ContractAuditor("openapi.yaml", EcoMarketClient)
    auditor.verify()