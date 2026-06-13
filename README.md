# Agente Multi-Tenant de Agendamiento

Agente conversacional en Telegram que permite a **cualquier negocio que agenda horas** (barberías, veterinarias, dentistas, peluquerías caninas, salones de belleza, etc.) gestionar citas automáticamente vía chat.

---

## ¿Qué hace este proyecto?

- Un cliente escribe por Telegram al bot del negocio
- El agente conversa con el cliente, recopila su nombre, datos de contacto y preferencia de hora
- Verifica disponibilidad en Google Calendar y crea la cita automáticamente
- Envía recordatorios automáticos antes de la cita
- Si no puede resolver algo, escala a un humano del negocio

Todo esto funciona para **múltiples negocios simultáneamente** (multi-tenant): cada negocio tiene su propio bot de Telegram y sus propios clientes, aislados entre sí.

---

## Arquitectura

```
Telegram (usuario) ──► FastAPI webhook ──► AgentCore
                                               │
                      ┌────────────────────────┼───────────────────────┐
                      ▼                        ▼                       ▼
               IntentClassifier          EntityExtractor      StateMachine
                      │                        │
                      └──────────┬─────────────┘
                                 ▼
                            OllamaLLM (llama3.2 local)
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              Supabase    GoogleCalendar   TelegramMessenger
```

**4 capas de abstracción independientes:**

| Capa | Abstracción | Implementación actual |
|---|---|---|
| Mensajería | `BaseMessenger` | Telegram |
| LLM | `BaseLLM` | Ollama (llama3.2) |
| Calendario | `BaseCalendar` | Google Calendar |
| Base de datos | Supabase SDK | PostgreSQL + RLS |

Agregar WhatsApp o cambiar a GPT-4 solo requiere una nueva clase, sin tocar la lógica del agente.

---

## Tech Stack

| Tecnología | Uso |
|---|---|
| Python 3.11+ | Lenguaje base |
| FastAPI | Servidor webhook |
| Supabase (PostgreSQL) | Base de datos multi-tenant con RLS |
| Ollama + llama3.2 | LLM local (clasificación y extracción) |
| python-telegram-bot 21.x | Mensajería |
| cryptography (Fernet) | Cifrado PII (RUT, teléfono, email) |
| APScheduler | Recordatorios automáticos |
| ngrok | Túnel para webhook en desarrollo |
| pytest + pytest-asyncio | Tests |

---

## Nichos soportados

| Nicho | `niche` value | Requiere entidad (mascota/paciente) |
|---|---|---|
| Peluquería Canina | `grooming` | Sí (mascota) |
| Veterinaria | `veterinary` | Sí (mascota) |
| Guardería de mascotas | `boarding` | Sí (mascota) |
| Barbería | `barbershop` | No |
| Centro de Estética | `cosmetics` | No |
| Centro Odontológico | `dental` | No |
| Salón de Belleza | `salon` | No |
| Centro Médico | `medical` | No |

---

## Estado de Implementación

| Tarea | Componente | Estado |
|---|---|---|
| Tarea 1 | Estructura de directorios, dependencias, git | ✅ Completada |
| Tarea 2 | `config/settings.py` + fixtures de test | ✅ Completada |
| Tarea 3 | Schema Supabase + `app/db.py` | ✅ Completada |
| Tarea 4 | Cifrado Fernet + validación webhook + rate limiter | ✅ Completada |
| Tarea 5 | Capa de mensajería Telegram + FastAPI | ⏳ Pendiente |
| Tarea 6 | Capa LLM (OllamaLLM) + configuración de nichos | ⏳ Pendiente |
| Tarea 7 | Google Calendar + Calendly (stub) | ⏳ Pendiente |
| Tarea 8 | Clasificador de intenciones + extractor de entidades | ⏳ Pendiente |
| Tarea 9 | Máquina de estados + AgentCore (orquestador) | ⏳ Pendiente |
| Tarea 10 | Notificaciones y recordatorios automáticos | ⏳ Pendiente |
| Tarea 11 | ngrok + webhook + demo en vivo | ⏳ Pendiente |

---

## Instalación

```bash
# 1. Clonar y crear entorno virtual
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
copy .env.example .env
# Editar .env con tus valores reales

# 4. Ejecutar tests
pytest -v

# 5. Levantar servidor
uvicorn main:app --port 8000 --reload
```

---

## Variables de entorno

| Variable | Descripción | Obligatoria |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Token del bot de Telegram (@BotFather) | Sí |
| `TELEGRAM_SECRET_TOKEN` | Token secreto para validar webhooks | Sí |
| `SUPABASE_URL` | URL del proyecto Supabase | Sí |
| `SUPABASE_KEY` | Clave anon/service de Supabase | Sí |
| `FERNET_ENCRYPTION_KEY` | Clave Fernet para cifrar PII | Sí |
| `OLLAMA_BASE_URL` | URL de Ollama (default: localhost:11434) | No |
| `OLLAMA_MODEL` | Modelo Ollama (default: llama3.2) | No |
| `NGROK_AUTH_TOKEN` | Token de ngrok para desarrollo | No |
| `RATE_LIMIT_PER_MINUTE` | Límite de mensajes por minuto (default: 10) | No |

---

## Seguridad y privacidad

- **Cifrado Fernet**: RUT, teléfono y email se cifran en reposo antes de guardar en Supabase
- **Row Level Security**: cada tenant solo puede acceder a sus propios datos
- **Validación HMAC**: cada webhook de Telegram es verificado con firma SHA-256
- **Rate limiting**: máximo de mensajes por minuto por usuario para prevenir abuso
- **Consentimiento explícito**: el bot solicita autorización antes de guardar datos personales
- **Derecho al olvido**: el usuario puede pedir eliminación de sus datos en cualquier momento

---

## Estructura de archivos

```
Full_mascotas_demo/
├── app/
│   ├── messaging/         # Capa de mensajería (Telegram, etc.)
│   ├── llm/               # Capa LLM (Ollama, etc.)
│   ├── calendar/          # Capa de calendario (Google, Calendly)
│   ├── agent/             # Lógica del agente (intent, entities, state, core)
│   ├── notifications/     # Recordatorios automáticos
│   └── security/          # Cifrado Fernet + validación webhook
├── config/
│   └── settings.py        # Variables de entorno con Pydantic Settings
├── data/
│   └── niche_config.py    # Configuración por nicho de negocio
├── db/
│   └── schema.sql         # Schema SQL para Supabase
├── tests/                 # Suite de tests TDD
├── main.py                # Entry point FastAPI
└── requirements.txt
```
