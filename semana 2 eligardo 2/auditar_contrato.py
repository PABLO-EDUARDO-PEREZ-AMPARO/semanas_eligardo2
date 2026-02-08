import yaml
import inspect
import sys  # <--- IMPORTANTE
from cliente_ecomarket import EcoMarketClient

# --- SOLUCIÓN AL ERROR DE WINDOWS ---
# Esto fuerza a que la salida sea UTF-8, permitiendo emojis en consola y archivos
sys.stdout.reconfigure(encoding='utf-8') 
# ------------------------------------

def auditar():
    # 1. Cargar Contrato
    with open("openapi.yaml", "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    # 2. Obtener métodos del cliente
    metodos_cliente = [m[0] for m in inspect.getmembers(EcoMarketClient, predicate=inspect.isfunction)]
    
    print(f"📋 AUDITORÍA DE CONTRATO: {spec['info']['title']}")
    print("="*60)
    
    conformidad = 0
    total = 0

    # 3. Iterar por endpoints
    for path, verbs in spec['paths'].items():
        for verb, detail in verbs.items():
            if verb == 'parameters': continue
            
            total += 1
            op_id = detail.get('operationId')
            
            # Lógica para mapear YAML -> Python
            if op_id:
                nombre_funcion = op_id
            else:
                # Mapeo manual si falta operationId en YAML
                mapa_manual = {
                    'put': 'actualizar_producto_total',
                    'patch': 'actualizar_producto_parcial',
                    'delete': 'eliminar_producto'
                }
                nombre_funcion = mapa_manual.get(verb, f"{verb}_{path.replace('/', '_')}")

            print(f"Endpoint: {verb.upper()} {path}")
            
            if nombre_funcion in metodos_cliente:
                print(f"  ✅ OK: Función found '{nombre_funcion}'")
                conformidad += 1
            else:
                print(f"  ❌ FALTA: Se esperaba '{nombre_funcion}' en el cliente")

    print("="*60)
    score = (conformidad / total) * 100
    print(f"RESULTADO FINAL: {score:.0f}% DE CONFORMIDAD")
    
    if score == 100:
        print("🎉 ¡Entregable Aprobado!")
    else:
        print("⚠️  Revisar faltantes.")

if __name__ == "__main__":
    auditar()