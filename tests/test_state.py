import pytest
from app.agent.state import ConversationState, ConversationStateMachine


class TestConversationState:
    def test_all_states_defined(self):
        expected = [
            "idle", "collecting_consent", "collecting_name", "collecting_rut",
            "collecting_phone", "collecting_email", "collecting_service",
            "collecting_entity", "collecting_datetime", "confirming",
            "scheduled", "cancelled", "escalated",
        ]
        for state in expected:
            assert ConversationState(state) is not None


class TestConversationStateMachine:
    def setup_method(self):
        self.sm = ConversationStateMachine()

    def test_idle_new_client_goes_to_consent(self):
        next_state = self.sm.next_state("idle", client_registered=False, context={})
        assert next_state == "collecting_consent"

    def test_idle_registered_client_goes_to_service(self):
        next_state = self.sm.next_state("idle", client_registered=True, context={})
        assert next_state == "collecting_service"

    def test_consent_accepted_goes_to_name(self):
        next_state = self.sm.next_state(
            "collecting_consent", client_registered=False, context={"consent": True}
        )
        assert next_state == "collecting_name"

    def test_consent_not_accepted_stays_in_consent(self):
        next_state = self.sm.next_state(
            "collecting_consent", client_registered=False, context={}
        )
        assert next_state == "collecting_consent"

    def test_name_goes_to_rut(self):
        assert self.sm.next_state("collecting_name", False, {}) == "collecting_rut"

    def test_rut_goes_to_phone(self):
        assert self.sm.next_state("collecting_rut", False, {}) == "collecting_phone"

    def test_phone_goes_to_email(self):
        assert self.sm.next_state("collecting_phone", False, {}) == "collecting_email"

    def test_email_goes_to_service(self):
        assert self.sm.next_state("collecting_email", False, {}) == "collecting_service"

    def test_service_goes_to_entity_when_niche_requires_it(self):
        next_state = self.sm.next_state(
            "collecting_service", False, {}, requires_entity=True
        )
        assert next_state == "collecting_entity"

    def test_service_skips_entity_when_niche_does_not_require_it(self):
        next_state = self.sm.next_state(
            "collecting_service", False, {}, requires_entity=False
        )
        assert next_state == "collecting_datetime"

    def test_entity_goes_to_datetime(self):
        assert self.sm.next_state("collecting_entity", False, {}) == "collecting_datetime"

    def test_datetime_goes_to_confirming(self):
        assert self.sm.next_state("collecting_datetime", False, {}) == "confirming"

    def test_get_prompt_for_consent_contains_tenant_name(self):
        prompt = self.sm.get_prompt("collecting_consent", tenant_name="PetShop Demo")
        assert "PetShop Demo" in prompt

    def test_get_prompt_for_service_contains_services(self):
        prompt = self.sm.get_prompt("collecting_service", services="baño, corte, spa")
        assert "baño" in prompt

    def test_get_prompt_for_entity_uses_entity_label(self):
        prompt = self.sm.get_prompt("collecting_entity", entity_label="mascota")
        assert "mascota" in prompt.lower()

    def test_get_prompt_for_name_mentions_nombre(self):
        prompt = self.sm.get_prompt("collecting_name")
        assert "nombre" in prompt.lower()
