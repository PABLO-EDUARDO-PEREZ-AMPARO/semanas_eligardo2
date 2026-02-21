import os

# Especificación OpenAPI 3.0 para EcoMarket
openapi_spec = """
openapi: 3.0.3
info:
  title: EcoMarket API
  description: API para la gestión de productos orgánicos entre productores y consumidores.
  version: 1.0.0
  contact:
    name: Equipo de Desarrollo EcoMarket
    email: dev@ecomarket.com

servers:
  - url: https://api.ecomarket.com/v1
    description: Servidor de Producción
  - url: http://localhost:8000/v1
    description: Servidor de Desarrollo Local

components:
  securitySchemes:
    # Definimos la seguridad: Token Bearer JWT
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT

  schemas:
    # Esquema para errores estándar
    Error:
      type: object
      properties:
        code:
          type: integer
          example: 400
        message:
          type: string
          example: "Datos de entrada inválidos"
        details:
          type: string
          example: "El campo 'precio' no puede ser negativo"

    # Esquema base (campos compartidos)
    ProductoBase:
      type: object
      required:
        - nombre
        - precio
        - categoria
        - productor_id
      properties:
        nombre:
          type: string
          minLength: 3
          maxLength: 100
          example: "Miel Orgánica de Yucatán"
        descripcion:
          type: string
          nullable: true
          example: "Miel 100% pura de abeja melipona, cosecha 2025."
        precio:
          type: number
          format: double
          minimum: 0.01
          # Restricción de decimales se maneja lógicamente, pero se documenta en description
          description: Precio unitario en moneda local (2 decimales).
          example: 150.50
        categoria:
          type: string
          enum: [frutas, verduras, lacteos, miel, conservas]
          example: "miel"
        productor_id:
          type: string
          format: uuid
          description: ID único del productor dueño del producto.
          example: "550e8400-e29b-41d4-a716-446655440000"
        disponible:
          type: boolean
          default: true
          example: true

    # Esquema para CREAR (Input) - No lleva ID ni fechas
    ProductoInput:
      allOf:
        - $ref: '#/components/schemas/ProductoBase'

    # Esquema para RESPUESTAS (Output) - Incluye ID y fechas
    ProductoOutput:
      allOf:
        - $ref: '#/components/schemas/ProductoBase'
        - type: object
          properties:
            id:
              type: string
              format: uuid
              readOnly: true
              example: "a1b2c3d4-e5f6-7890-1234-56789abcdef0"
            creado_en:
              type: string
              format: date-time
              readOnly: true
              example: "2023-10-27T10:00:00Z"

paths:
  /productos:
    get:
      summary: Listar productos disponibles
      description: Obtiene una lista paginada de productos. Permite filtrar por categoría y productor.
      operationId: getProducts
      parameters:
        - name: categoria
          in: query
          description: Filtrar por categoría de producto.
          required: false
          schema:
            type: string
            enum: [frutas, verduras, lacteos, miel, conservas]
        - name: productor_id
          in: query
          description: Filtrar productos de un productor específico.
          required: false
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Lista de productos obtenida exitosamente.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/ProductoOutput'
        '400':
          description: Parámetros de filtro inválidos.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                code: 400
                message: "Categoría inválida"
                details: "La categoría 'electrónica' no es permitida."

    post:
      summary: Crear un nuevo producto
      description: Registra un nuevo producto en el catálogo. Requiere autenticación de productor.
      operationId: createProduct
      security:
        - bearerAuth: []
      requestBody:
        description: Datos del producto a crear.
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ProductoInput'
      responses:
        '201':
          description: Producto creado exitosamente.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProductoOutput'
        '400':
          description: Error de validación en los datos enviados (JSON mal formado o reglas de negocio).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                code: 400
                message: "Precio inválido"
                details: "El precio debe ser mayor a 0."
        '401':
          description: No autorizado (Token faltante o inválido).
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                code: 401
                message: "Token expirado o inválido"

  /productos/{id}:
    get:
      summary: Ver detalle de un producto
      description: Obtiene la información completa de un producto específico por su ID.
      operationId: getProductById
      parameters:
        - name: id
          in: path
          description: ID único del producto.
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Detalle del producto encontrado.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ProductoOutput'
        '404':
          description: Producto no encontrado.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Error'
              example:
                code: 404
                message: "Recurso no encontrado"
                details: "El producto con ID a1b2c3d4... no existe."
"""

def save_openapi_file():
    filename = "ecomarket_openapi.yaml"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(openapi_spec)
        print(f"✅ Éxito: El contrato API ha sido generado en '{filename}'")
        print("📋 Siguiente paso: Carga este archivo en https://editor.swagger.io/ para visualizarlo.")
    except Exception as e:
        print(f"❌ Error al guardar el archivo: {e}")

if __name__ == "__main__":
    save_openapi_file()