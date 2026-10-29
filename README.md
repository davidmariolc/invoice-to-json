# Invoice to JSON

Proyecto de práctica para explorar **Structured Outputs con JSON Schema**: convertir la imagen de una factura en datos que una aplicación pueda validar y utilizar.

La factura es el caso de uso. El objetivo principal fue practicar cómo definir un contrato de datos, compartirlo con un modelo de IA y comprobar su respuesta antes de mostrarla al usuario.

[Ver aplicación](https://invoice-to-json.vercel.app/) · [API interactiva](https://invoice-to-json.vercel.app/docs)

## Qué se buscó practicar

- Modelar datos anidados con **Pydantic** y generar su **JSON Schema**.
- Configurar **Structured Outputs** con el SDK nativo **`google-genai`**.
- Representar datos desconocidos con `null` y distinguirlos de propiedades ausentes.
- Validar la respuesta del modelo en el backend y el contrato de la API en el frontend.
- Manejar respuestas vacías, incompletas o inválidas, además de errores del proveedor.

La idea que guía el proyecto es esta: **pedir «responde en JSON» no define por sí solo qué datos necesita la aplicación**. Un JSON puede ser sintácticamente válido y aun así contener propiedades inesperadas, omitir campos o representar valores de otra manera. JSON Schema permite expresar esa estructura; la aplicación valida después lo que recibe.

## Cómo funciona

```text
Imagen de factura
  → Validación del archivo
  → Gemini + instrucciones + JSON Schema
  → Validación con Pydantic
  → Respuesta de la API
  → Validación con Zod
  → Visualización del JSON
```

1. El usuario selecciona una imagen JPEG, PNG o WEBP de hasta **4 MB**.
2. FastAPI comprueba su tamaño, formato real e integridad antes de enviarla al modelo.
3. Gemini recibe la imagen, las instrucciones de extracción y el esquema esperado.
4. El backend valida la respuesta y comprueba si el documento fue reconocido como factura, boleta o recibo de venta legible.
5. El frontend valida la respuesta HTTP con Zod y muestra los datos estructurados.

Al abrir la aplicación se muestra una **factura ficticia con su JSON precargado**, identificados como «Ejemplo». Esa demostración es estática: no llama al backend ni consume Gemini. Al seleccionar una imagen propia se limpia el resultado; al quitarla, vuelve el ejemplo.

## Structured Outputs en este proyecto

### 1. Definir el contrato antes de llamar al modelo

Los modelos de [facturas](fastapi/app/features/invoices/schemas.py) describen las partes del documento:

| Modelo | Responsabilidad |
| --- | --- |
| `InvoiceParty` | Nombre, identificador fiscal y dirección del emisor o destinatario. |
| `InvoiceItem` | Descripción, cantidad, precio unitario e importe de una línea. |
| `InvoiceData` | Número, fecha, moneda, partes, productos y totales de la factura. |
| `InvoiceExtraction` | Resultado interno del modelo: `is_invoice` e `invoice`. |
| `InvoiceProcessResponse` | Respuesta pública de la API: `model`, `filename` y `data`. |

En los modelos de extracción, `extra="forbid"` rechaza propiedades adicionales y `allow_inf_nan=False` rechaza valores numéricos no finitos. Los identificadores fiscales y números de factura se mantienen como texto para conservar sus ceros iniciales.

Un campo como `invoice_number: str | None`, sin valor por defecto, **debe estar presente**, pero puede contener `null`. Así se representa la falta de información sin inventar un valor ni cambiar la estructura del resultado.

### 2. Generar el JSON Schema y enviarlo a Gemini

El [servicio de extracción](fastapi/app/features/invoices/service.py) obtiene el esquema directamente del modelo Pydantic:

```python
model, content = generate_text(
    "Lee esta factura y extrae sus datos.",
    system_instruction=EXTRACTION_PROMPT,
    image=contents,
    mime_type=mime_type,
    response_json_schema=InvoiceExtraction.model_json_schema(),
)
```

El [proveedor de Gemini](fastapi/app/ai/providers/gemini.py) configura la generación con el SDK nativo:

```python
types.GenerateContentConfig(
    system_instruction=system_instruction,
    response_mime_type="application/json",
    response_json_schema=response_json_schema,
)
```

Este fragmento corresponde a la extracción de facturas, donde siempre se proporciona un esquema. El modelo configurado en el proyecto es `gemini-3.5-flash-lite`.

El esquema generado utiliza propiedades como `required`, `anyOf`, `additionalProperties`, `$defs` y `$ref` para describir campos obligatorios, valores anulables y objetos anidados. Las descripciones de los campos aportan contexto sobre su interpretación.

### 3. Validar también la respuesta

El backend no entrega directamente el texto generado. Primero lo valida con el mismo modelo que originó el esquema:

```python
extraction = InvoiceExtraction.model_validate_json(content)
```

Si la respuesta no es válida, la API devuelve un error. Si `is_invoice` es `false`, tampoco se presenta como una extracción exitosa. Para un documento aceptado, la API expone `invoice` dentro de `data` y agrega el modelo utilizado y el nombre del archivo.

El frontend aplica una segunda validación con **Zod** sobre esa respuesta HTTP. El esquema de Zod se mantiene de forma independiente: actualmente no se genera automáticamente desde Pydantic.

**Cumplir el esquema no demuestra que los datos sean correctos.** La extracción todavía depende de la legibilidad del documento y de la interpretación del modelo. Las instrucciones piden usar `null` ante información ausente o ambigua y no completar ni calcular importes que no estén impresos. El proyecto no realiza conciliación contable ni validación fiscal.

## Ejemplo de respuesta

Respuesta ilustrativa del endpoint, con los datos ficticios del ejemplo incluido en el frontend:

```json
{
  "model": "gemini-3.5-flash-lite",
  "filename": "factura.png",
  "data": {
    "invoice_number": "DEMO-000123",
    "issue_date": "2026-10-29",
    "currency": "PEN",
    "issuer": {
      "name": "Empresa Ejemplo",
      "tax_id": null,
      "address": null
    },
    "recipient": {
      "name": "Cliente Demo",
      "tax_id": null,
      "address": null
    },
    "items": [
      {
        "description": "Servicio de prueba",
        "quantity": 2,
        "unit_price": 50,
        "amount": 100
      }
    ],
    "subtotal": 100,
    "taxes": 18,
    "total": 118
  }
}
```

Las propiedades usan inglés y `snake_case`; los valores de texto conservan el idioma del documento.

## Stack y organización

| Capa | Tecnologías |
| --- | --- |
| Frontend | React, TypeScript, Vite, Tailwind CSS y shadcn/ui. |
| Formularios y validación del cliente | React Hook Form y Zod. |
| Backend y validación de datos | Python 3.12, FastAPI, Pydantic y Pillow. |
| IA | Gemini mediante `google-genai`. |
| Herramientas y despliegue | uv, pnpm, Ultracite y Vercel Services. |

```text
invoice-to-json/
├── fastapi/
│   ├── app/
│   │   ├── features/invoices/   # Rutas, modelos, extracción, imágenes y prompt
│   │   ├── ai/providers/        # Integración con Gemini
│   │   ├── core/               # Configuración
│   │   └── main.py
│   └── tests/
├── web/
│   └── src/
│       ├── features/invoices/   # Formulario, ejemplo, visor JSON y cliente HTTP
│       ├── components/ui/      # Componentes compartidos
│       └── app.tsx
└── vercel.json                 # Servicios y rutas del despliegue
```

## Ejecutar localmente

Necesitas **Python 3.12**, **uv**, **pnpm**, una versión de **Node.js compatible con las herramientas del frontend** (`^22.22.2 || >=24.15.0`) y una clave de Gemini con acceso al modelo configurado.

### Backend

Desde la raíz del repositorio:

```sh
cd fastapi
uv sync --locked
cp .env.example .env
```

Configura `GEMINI_API_KEY` en `fastapi/.env` y luego inicia el servidor:

```sh
uv run uvicorn app.main:app --reload --port 5001
```

La clave se utiliza exclusivamente en el backend. El archivo `.env` está excluido de Git. Sin clave puedes iniciar la aplicación y ver el ejemplo estático, pero no procesar imágenes con Gemini.

### Frontend

En otra terminal, desde la raíz del repositorio:

```sh
cd web
pnpm install --frozen-lockfile
pnpm dev
```

Abre [la aplicación local](http://localhost:5173/) o [Swagger](http://localhost:5001/docs). Vite reenvía las peticiones `/api` a FastAPI en el puerto `5001`.

## API

### `POST /api/v1/invoices/process`

Recibe un archivo en el campo `file` de un formulario `multipart/form-data`:

```sh
curl -X POST http://localhost:5001/api/v1/invoices/process \
  -F 'file=@/ruta/a/factura.png'
```

| Estado HTTP | Situación |
| --- | --- |
| `200` | Extracción validada. |
| `400` | Imagen vacía, corrupta o con resolución insegura. |
| `413` | Archivo por encima del límite de tamaño. |
| `415` | Tipo de imagen no admitido o formato real distinto al declarado. |
| `422` | Falta el archivo o no se reconoce un documento de venta legible. |
| `502` | Error del proveedor o respuesta vacía, incompleta o incompatible con el esquema. |
| `503` | Falta configurar `GEMINI_API_KEY`. |
| `504` | Tiempo de espera agotado al consultar Gemini. |

Las imágenes enviadas para procesar se transmiten a Gemini. La aplicación no las almacena permanentemente ni guarda un historial de resultados. Cada procesamiento real puede consumir cuota del proveedor.

## Pruebas y comprobaciones

Desde `fastapi/`:

```sh
uv run --locked python -m unittest discover -s tests -v
```

Las pruebas del backend cubren validación de imágenes, envío de la imagen y el esquema al SDK, respuestas inválidas, campos con `null` y traducción de errores a HTTP. Utilizan respuestas simuladas y no hacen llamadas reales a Gemini.

Desde `web/`:

```sh
pnpm check
pnpm build
```

Estos comandos comprueban lint, formato, tipos de TypeScript y compilación. No sustituyen las pruebas de interacción del navegador ni llaman al modelo.

## Despliegue en Vercel

El archivo `vercel.json` utiliza [Vercel Services](https://vercel.com/docs/services), actualmente en beta, para desplegar el frontend de `web/` y el backend de `fastapi/` juntos.

- Usa la raíz del repositorio como **Root Directory**, el preset **Other** para el proyecto y Node.js **24.x**.
- Configura `GEMINI_API_KEY` como secreto en los entornos Preview y Production; no la publiques mediante variables `VITE_*`.
- Las rutas `/api/*`, `/docs`, `/redoc` y `/openapi.json` llegan a FastAPI. Las demás llegan a Vite, con fallback para las rutas del frontend.
- El frontend utiliza URLs relativas, por lo que cada despliegue consulta su propio backend.

Con Vercel CLI, desde la raíz:

```sh
vercel link
vercel
# Tras verificar el Preview:
vercel --prod
```

El límite de imagen de **4 MB** deja margen para el formulario multipart dentro del [máximo de 4,5 MB de Vercel Functions](https://vercel.com/docs/functions/limitations). La función tiene un máximo de 90 segundos y la llamada a Gemini un timeout de 60 segundos, con un único intento por petición.

`.vercelignore` excluye secretos locales, dependencias y archivos generados de las subidas por CLI. Para más detalles, consulta la documentación del [backend](fastapi/README.md) y del [frontend](web/README.md).

## Referencias

- [JSON Schema: qué es un esquema](https://json-schema.org/understanding-json-schema/about).
- [Pydantic: generación de JSON Schema](https://docs.pydantic.dev/latest/concepts/json_schema/).
- [Google Gen AI SDK: configuración y ejemplos](https://googleapis.github.io/python-genai/).
- [FastAPI en Vercel](https://vercel.com/docs/frameworks/backend/fastapi).
- [Backend Python con Vercel Services](https://vercel.com/kb/guide/python-backend-on-vercel).
