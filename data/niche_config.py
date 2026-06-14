NICHE_CONFIG: dict[str, dict] = {
    "grooming": {
        "display_name": "Peluquería Canina",
        "requires_entity": True,
        "entity_label": "mascota",
        "required_fields": ["service_type", "entity_name", "datetime"],
        "services": ["baño", "corte", "baño + corte", "spa canino"],
        "avg_duration_minutes": 120,
    },
    "veterinary": {
        "display_name": "Veterinaria",
        "requires_entity": True,
        "entity_label": "mascota",
        "required_fields": ["reason", "entity_name", "datetime"],
        "services": ["consulta general", "vacunación", "urgencia", "control"],
        "avg_duration_minutes": 30,
    },
    "boarding": {
        "display_name": "Guardería",
        "requires_entity": True,
        "entity_label": "mascota",
        "required_fields": ["checkin_date", "checkout_date", "entity_name"],
        "services": ["guardería día", "guardería noche", "fin de semana"],
        "avg_duration_minutes": None,
    },
    "barbershop": {
        "display_name": "Barbería",
        "requires_entity": False,
        "entity_label": None,
        "required_fields": ["service_type", "datetime"],
        "services": ["corte clásico", "corte + barba", "afeitado", "corte infantil"],
        "avg_duration_minutes": 45,
    },
    "cosmetics": {
        "display_name": "Centro de Estética",
        "requires_entity": False,
        "entity_label": None,
        "required_fields": ["service_type", "datetime"],
        "services": ["facial", "depilación", "manicure", "pedicure", "masaje"],
        "avg_duration_minutes": 60,
    },
    "dental": {
        "display_name": "Centro Odontológico",
        "requires_entity": False,
        "entity_label": None,
        "required_fields": ["reason", "datetime"],
        "services": ["limpieza dental", "consulta", "blanqueamiento", "urgencia", "ortodoncia"],
        "avg_duration_minutes": 45,
    },
    "salon": {
        "display_name": "Salón de Belleza",
        "requires_entity": False,
        "entity_label": None,
        "required_fields": ["service_type", "datetime"],
        "services": ["corte", "tinte", "peinado", "alisado", "keratina"],
        "avg_duration_minutes": 90,
    },
    "medical": {
        "display_name": "Centro Médico",
        "requires_entity": False,
        "entity_label": None,
        "required_fields": ["reason", "datetime"],
        "services": ["consulta general", "control", "urgencia", "examen"],
        "avg_duration_minutes": 30,
    },
}


def get_niche_config(niche: str) -> dict:
    if niche not in NICHE_CONFIG:
        raise ValueError(
            f"Nicho desconocido: '{niche}'. "
            f"Opciones válidas: {list(NICHE_CONFIG.keys())}"
        )
    return NICHE_CONFIG[niche]


def list_niches() -> list[str]:
    return list(NICHE_CONFIG.keys())
