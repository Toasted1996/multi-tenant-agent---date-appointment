Ñ# Especificación de Diseño: Agente de Agendamiento Multi-Tenant para Mascotas

**Fecha:** 2026-05-18  
**Versión:** 1.0  
**Estado:** Aprobado

---

## 1. Resumen del Proyecto

Sistema de agente conversacional en Telegram (extensible a WhatsApp) que permite a negocios del nicho de mascotas —peluquerías caninas, guarderías y veterinarias— automatizar la atención al cliente. El agente gestiona el ciclo completo: registro de clientes, agendamiento de citas, preguntas frecuentes, recordatorios automáticos y escalación a operadores humanos.

La arquitectura es **multi-tenant** desde el día 1: múltiples negocios operan sobre la misma plataforma con datos completamente aislados entre sí.

---

## 2. Decisiones de Diseño

| Decisión | Elección | Razón |
|---|---|---|
| Mensajería inicial | Telegram | API gratuita, sin aprobación Meta, ideal para demo |
| Arquitectura | Monolítico con capas de abstracción | Simple, educativo, extensible |
| LLM | Ollama (local, llama3.2) | Sin costo de API para demo, swappable |
| Backend | Python + FastAPI | Ecosistema IA, soporte asíncrono |
| Base de datos | Supabase (PostgreSQL) | Panel visual, RLS nativo, free tier permanente |
| Calendarios | Google Calendar + Calendly | Abstracción para múltiples proveedores |
| Despliegue demo | Ollama local + ngrok | Gratis, sin servidor |
| Multi-tenancy | Sí, desde el día 1 | Escalabilidad comercial |
| Compliance | Ley 19.628 / 21.719 Chile | Diferenciador de mercado y obligación legal |

---

## 3. Arquitectura del Sistema

### 3.1 Estructura de Capas

El sistema se organiza en 4 capas de abstracción independientes. Cambiar de proveedor en cualquier capa (por ejemplo, de Ollama a Claude, o de Telegram a WhatsApp) solo requiere agregar una nueva implementación de la clase abstracta correspondiente, sin modificar la lógica del agente.

```
Full_mascotas_demo/
├── app/
│   ├── messaging/              # Capa de mensajería
│   │   ├── base.py             # BaseMessenger (abstracto)
│   │   ├── telegram.py         # TelegramMessenger
│   │   └── whatsapp.py         # WhatsAppMessenger (stub futuro)
│   ├── llm/                    # Capa de LLM
│   │   ├── base.py             # BaseLLM (abstracto)
│   │   └── ollama.py           # OllamaLLM
│   ├── calendar/               # Capa de calendario
│   │   ├── base.py             # BaseCalendar (abstracto)
│   │   ├── google.py           # GoogleCalendarProvider
│   │   └── calendly.py         # CalendlyProvider
│   ├── agent/                  # Núcleo del agente
│   │   ├── core.py             # Orquestador principal
│   │   ├── intent.py           # Clasificación de intenciones
│   │   ├── entities.py         # Extracción de fechas, servicios, PII
│   │   ├── state.py            # Máquina de estados por conversación
│   │   └── escalation.py       # Lógica de escalación humana
│   ├── notifications/
│   │   └── scheduler.py        # Recordatorios automáticos (APScheduler)
│   └── security/
│       └── middleware.py       # Validación webhook, cifrado Fernet
├── data/
│   └── niche_config.py         # Configuración por nicho
├── config/
│   └── settings.py             # Variables de entorno
├── main.py                     # FastAPI entry point
└── .env                        # Secrets locales (nunca en git)
```

### 3.2 Flujo de Datos Principal

```
Usuario Telegram
    → ngrok (expone webhook local)
    → FastAPI /webhook/{secret_token}
        → Validación HMAC-SHA256 (firma Telegram)
        → Identificación de tenant por bot token
    → Agent Core
        → Cargar estado conversación (Supabase)
        → LLM extrae intención + entidades
        → Máquina de estados decide acción
        → Ejecutar acción (preguntar / consultar calendario / agendar / FAQ / escalar)
        → Guardar estado actualizado (Supabase)
    → Messaging Layer
        → Enviar respuesta al usuario
```

---

## 4. Núcleo del Agente

### 4.1 Intenciones Reconocidas

| Intención | Ejemplo de mensaje del usuario |
|---|---|
| `SCHEDULE_APPOINTMENT` | "Quiero agendar para el viernes a las 3pm" |
| `CHECK_AVAILABILITY` | "¿Tienen disponible el lunes por la tarde?" |
| `CANCEL_APPOINTMENT` | "Necesito cancelar mi cita de mañana" |
| `FAQ_QUERY` | "¿Cuánto cuesta el baño con corte?" |
| `HUMAN_ESCALATION` | "Quiero hablar con alguien", "necesito ayuda urgente" |
| `GREETING` | "Hola", "Buenos días" |
| `DELETE_MY_DATA` | "Quiero que borren mis datos" |
| `OUT_OF_SCOPE` | Cualquier consulta fuera del dominio del negocio |

### 4.2 Máquina de Estados de Conversación

```
idle
  └─→ collecting_consent        (primera vez: mostrar aviso de privacidad)
        └─→ collecting_name
              └─→ collecting_rut
                    └─→ collecting_phone
                          └─→ collecting_email
                                └─→ collecting_service
                                      └─→ collecting_pet
                                            └─→ collecting_datetime
                                                  └─→ confirming
                                                        ├─→ scheduled   ✓
                                                        ├─→ cancelled
                                                        └─→ escalated   → humano
```

Una vez el cliente está registrado, el flujo salta directamente a `collecting_service`.

### 4.3 Prompt del Sistema al LLM

```
Eres el asistente virtual de {tenant.name}, un negocio de {tenant.niche}
ubicado en Chile. Tu rol es:
1. Registrar clientes nuevos (nombre, RUT, teléfono, email)
2. Agendar citas verificando disponibilidad en el calendario
3. Responder preguntas frecuentes sobre el negocio
4. Derivar a un humano cuando sea necesario

Extrae siempre del mensaje del usuario:
- Intención principal
- Fecha y hora (convierte expresiones relativas a fechas absolutas)
- Servicio solicitado
- Nombre de la mascota

Pregunta un dato a la vez. Responde siempre en español, de forma
amable y concisa. Nunca inventes disponibilidad — siempre consulta
el calendario antes de confirmar.
```

### 4.4 Configuración por Nicho (Extensible)

```python
NICHE_CONFIG = {
    "grooming": {
        "required_fields": ["service_type", "pet", "datetime"],
        "services": ["baño", "corte", "baño + corte", "spa"],
        "avg_duration_minutes": 120,
    },
    "veterinary": {
        "required_fields": ["reason", "pet", "datetime"],
        "services": ["consulta general", "vacunación", "urgencia", "control"],
        "avg_duration_minutes": 30,
    },
    "boarding": {
        "required_fields": ["checkin_date", "checkout_date", "pet"],
        "services": ["guardería día", "guardería noche", "fin de semana"],
        "avg_duration_minutes": None,
    }
}
```

Agregar un nuevo nicho es añadir una entrada a este diccionario.

---

## 5. Base de Datos Multi-Tenant (Supabase)

### 5.1 Principio Central

**Toda tabla tiene `tenant_id` como primera referencia.** Supabase Row Level Security (RLS) garantiza aislamiento a nivel de base de datos — ningún bug en el código de Python puede filtrar datos entre tenants.

### 5.2 Esquema Completo

```sql
-- Eje central del sistema
tenants
  id UUID PK
  name TEXT
  niche TEXT                    -- grooming | veterinary | boarding
  plan_tier TEXT                -- free | pro
  telegram_bot_token TEXT       -- cifrado con Fernet
  escalation_contact TEXT       -- usuario Telegram del operador
  created_at TIMESTAMPTZ

-- Personas que administran un negocio
tenant_users
  id UUID PK
  tenant_id UUID → tenants
  auth_user_id UUID → Supabase Auth
  role TEXT                     -- owner | staff

-- Usuarios finales (clientes del negocio)
clients
  id UUID PK
  tenant_id UUID → tenants
  telegram_user_id BIGINT       -- capturado automáticamente
  name TEXT
  rut_encrypted TEXT            -- cifrado con Fernet
  phone_encrypted TEXT          -- cifrado con Fernet
  email_encrypted TEXT          -- cifrado con Fernet
  consent_accepted_at TIMESTAMPTZ
  consent_version TEXT
  created_at TIMESTAMPTZ

-- Mascotas de cada cliente
pets
  id UUID PK
  tenant_id UUID → tenants
  client_id UUID → clients
  name TEXT
  species TEXT
  breed TEXT
  notes TEXT

-- Citas agendadas
appointments
  id UUID PK
  tenant_id UUID → tenants
  client_id UUID → clients
  pet_id UUID → pets
  datetime_start TIMESTAMPTZ
  datetime_end TIMESTAMPTZ
  service_type TEXT
  status TEXT                   -- pending | confirmed | cancelled
  calendar_event_id TEXT        -- ID externo en Google Calendar / Calendly

-- Estado activo de cada conversación
conversations
  id UUID PK
  tenant_id UUID → tenants
  client_id UUID → clients
  state TEXT                    -- ver máquina de estados
  context_json JSONB            -- datos parciales recolectados
  updated_at TIMESTAMPTZ

-- Base de conocimiento por negocio
faqs
  id UUID PK
  tenant_id UUID → tenants
  question TEXT
  answer TEXT
  embedding_vector VECTOR       -- para búsqueda semántica (futuro)

-- Recordatorios automáticos
reminders
  id UUID PK
  tenant_id UUID → tenants
  appointment_id UUID → appointments
  send_at TIMESTAMPTZ
  sent BOOLEAN
  message_template TEXT

-- Escalaciones a operador humano
escalations
  id UUID PK
  tenant_id UUID → tenants
  conversation_id UUID → conversations
  reason TEXT
  resolved BOOLEAN
  created_at TIMESTAMPTZ

-- Credenciales de calendario por tenant
calendar_integrations
  id UUID PK
  tenant_id UUID → tenants
  provider TEXT                 -- google | calendly
  credentials_encrypted TEXT    -- OAuth tokens, cifrados con Fernet
  is_active BOOLEAN
```

### 5.3 RLS Policy (aplicada a todas las tablas)

```sql
CREATE POLICY "tenant_isolation" ON appointments
  FOR ALL USING (tenant_id = (auth.jwt() ->> 'tenant_id')::UUID);
```

---

## 6. Seguridad

### 6.1 Capas de Seguridad

| Capa | Mecanismo |
|---|---|
| Webhook Telegram | Validación HMAC-SHA256 en cada request |
| PII en reposo | Cifrado `cryptography.Fernet` (AES-128) |
| Aislamiento de datos | Supabase RLS por tenant_id |
| Secrets | Variables de entorno en `.env`, nunca en código |
| Endpoint webhook | Token secreto en URL, solo conocido por Telegram |
| Datos mínimos | Solo estado activo, no historial completo de mensajes |
| Abuso | Rate limiting: máx. mensajes por usuario/minuto |

### 6.2 Variables de Entorno Requeridas

```
TELEGRAM_BOT_TOKEN=
TELEGRAM_SECRET_TOKEN=         # Token secreto para validar webhook
SUPABASE_URL=
SUPABASE_KEY=
FERNET_ENCRYPTION_KEY=         # Generado con Fernet.generate_key()
NGROK_AUTH_TOKEN=
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
```

---

## 7. Compliance Legal (Chile)

### Ley 19.628 / Ley 21.719 de Protección de Datos Personales

| Requisito | Implementación |
|---|---|
| Consentimiento informado | Mensaje explícito antes de recolectar datos; registro con timestamp y versión |
| Finalidad declarada | El bot informa para qué se usarán los datos |
| Datos mínimos necesarios | Solo se almacena lo necesario para agendar |
| Derecho a eliminación | Comando "borren mis datos" anonimiza toda PII del cliente |
| Seguridad en el tratamiento | Cifrado en reposo, RLS, secrets en entorno |

### Mensaje de Consentimiento

```
"Antes de continuar, necesito tu autorización para guardar tus datos
personales (nombre, RUT, teléfono, correo electrónico) con el fin
exclusivo de gestionar tus citas en {negocio.name}.

Tus datos son almacenados de forma segura y cifrada, y no serán
compartidos con terceros.

¿Aceptas los términos? Responde SÍ para continuar."
```

---

## 8. Notificaciones y Escalación

### 8.1 Recordatorios Automáticos

- **24 horas antes**: aviso de la cita con detalles
- **2 horas antes**: solicitud de confirmación de asistencia (SÍ / NO)
- Si el cliente responde NO: cita cancelada, slot liberado en Google Calendar

### 8.2 Escalación a Humano

Se activa cuando:
1. El cliente escribe "quiero hablar con alguien" o similar
2. El agente no entiende la consulta después de 2 intentos consecutivos
3. Se detecta urgencia ("está herido", "urgente", "emergencia")

Flujo:
1. Bot informa al cliente que será contactado pronto
2. Operador recibe notificación en Telegram con resumen de la conversación
3. Conversación marcada como `escalated` en Supabase
4. Operador resuelve y marca como `resolved`

---

## 9. Stack Técnico

| Componente | Tecnología | Versión recomendada |
|---|---|---|
| Framework API | FastAPI | 0.110+ |
| LLM local | Ollama (llama3.2) | Latest |
| Base de datos | Supabase Python Client | 2.x |
| Cifrado | cryptography (Fernet) | 42+ |
| Calendario Google | google-api-python-client | 2.x |
| Calendario Calendly | requests (REST API) | 2.x |
| Mensajería Telegram | python-telegram-bot | 21.x |
| Scheduler | APScheduler | 3.x |
| Tunnel local | ngrok | 3.x |
| Env vars | python-dotenv | 1.x |
| Servidor ASGI | uvicorn | 0.29+ |

---

## 10. Despliegue del Demo

```bash
# 1. LLM local
ollama pull llama3.2
ollama run llama3.2

# 2. Aplicación Python
uvicorn main:app --port 8000 --reload

# 3. Exponer con ngrok
ngrok http 8000 --domain=tu-subdominio.ngrok-free.app

# 4. Registrar webhook en Telegram
curl -X POST "https://api.telegram.org/bot{TOKEN}/setWebhook" \
  -d "url=https://tu-subdominio.ngrok-free.app/webhook/{SECRET_TOKEN}"
```

---

## 11. Verificación del Demo (Checklist)

- [ ] Escribir "Hola" → saludo personalizado con nombre del negocio
- [ ] Solicitar cita → agente recolecta datos uno a uno (consentimiento → nombre → RUT → ...)
- [ ] Agente consulta Google Calendar → confirma disponibilidad real
- [ ] Cita confirmada aparece en Supabase (`appointments`) y en Google Calendar
- [ ] Recordatorio agendado visible en tabla `reminders`
- [ ] Escribir "quiero hablar con alguien" → escalación notifica al operador
- [ ] Escribir "borren mis datos" → PII eliminada o anonimizada en `clients`
- [ ] Repetir flujo con un segundo tenant → datos completamente aislados
- [ ] Intentar acceder a datos de tenant 1 desde tenant 2 → bloqueado por RLS

---

## 12. Extensiones Futuras (fuera del alcance del demo)

- Integración con WhatsApp Business API (capa `whatsapp.py` ya preparada)
- Cambio de LLM a Claude API o Groq (capa `llm/` preparada para ello)
- Panel de administración web para configurar FAQ, horarios y servicios
- Búsqueda semántica en FAQ con embeddings (`embedding_vector` en `faqs`)
- Multi-idioma (español / inglés)
- Tier de pago por tenant (`plan_tier` en `tenants`)
- Reportes de ocupación y análisis de demanda por nicho
