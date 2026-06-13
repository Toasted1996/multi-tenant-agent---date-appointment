-- Schema multi-tenant para el agente de agendamiento
-- Ejecutar en: Supabase → SQL Editor → Run

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Negocios (tenants)
CREATE TABLE tenants (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  niche           TEXT NOT NULL CHECK (niche IN ('grooming','veterinary','boarding','barbershop','cosmetics','dental','salon','medical')),
  plan_tier       TEXT NOT NULL DEFAULT 'free' CHECK (plan_tier IN ('free','pro')),
  telegram_bot_token  TEXT NOT NULL,
  escalation_contact  TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Usuarios administradores de cada tenant
CREATE TABLE tenant_users (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  auth_user_id UUID REFERENCES auth.users(id),
  role        TEXT NOT NULL DEFAULT 'staff' CHECK (role IN ('owner','staff'))
);

-- Clientes finales de cada negocio
CREATE TABLE clients (
  id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id        UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  telegram_user_id BIGINT NOT NULL,
  name             TEXT NOT NULL,
  rut_encrypted    TEXT,
  phone_encrypted  TEXT,
  email_encrypted  TEXT,
  consent_accepted_at TIMESTAMPTZ,
  consent_version  TEXT DEFAULT '1.0',
  created_at       TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(tenant_id, telegram_user_id)
);

-- Entidades por cliente (mascota para vet/grooming; vacío para barbería/dental)
CREATE TABLE entities (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  name        TEXT NOT NULL,
  entity_type TEXT,   -- 'dog', 'cat', 'patient', etc.
  breed       TEXT,
  notes       TEXT
);

-- Citas
CREATE TABLE appointments (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  entity_id       UUID REFERENCES entities(id),  -- null para nichos sin entidad
  datetime_start  TIMESTAMPTZ NOT NULL,
  datetime_end    TIMESTAMPTZ NOT NULL,
  service_type    TEXT NOT NULL,
  status          TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','confirmed','cancelled')),
  calendar_event_id TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Estado de conversaciones activas (una por cliente por tenant)
CREATE TABLE conversations (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id   UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  client_id   UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
  state       TEXT NOT NULL DEFAULT 'idle',
  context_json JSONB DEFAULT '{}',
  updated_at  TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE(tenant_id, client_id)
);

-- Preguntas frecuentes por negocio
CREATE TABLE faqs (
  id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  question  TEXT NOT NULL,
  answer    TEXT NOT NULL
);

-- Recordatorios automáticos
CREATE TABLE reminders (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  appointment_id  UUID NOT NULL REFERENCES appointments(id) ON DELETE CASCADE,
  send_at         TIMESTAMPTZ NOT NULL,
  sent            BOOLEAN DEFAULT FALSE,
  message_template TEXT NOT NULL
);

-- Escalaciones a humano
CREATE TABLE escalations (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  reason          TEXT,
  resolved        BOOLEAN DEFAULT FALSE,
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Integraciones de calendario por tenant
CREATE TABLE calendar_integrations (
  id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id            UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  provider             TEXT NOT NULL CHECK (provider IN ('google','calendly')),
  credentials_encrypted TEXT NOT NULL,
  is_active            BOOLEAN DEFAULT TRUE,
  UNIQUE(tenant_id, provider)
);

-- Habilitar RLS en todas las tablas
ALTER TABLE tenants               ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_users          ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients               ENABLE ROW LEVEL SECURITY;
ALTER TABLE entities              ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments          ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations         ENABLE ROW LEVEL SECURITY;
ALTER TABLE faqs                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders             ENABLE ROW LEVEL SECURITY;
ALTER TABLE escalations           ENABLE ROW LEVEL SECURITY;
ALTER TABLE calendar_integrations ENABLE ROW LEVEL SECURITY;
