from models import Event
from repositories.event import EventRepository
from security.permissions import Permission, require_permission
from utils.validators import validate_string_not_empty


class EventService:
    def __init__(self, event_repository: EventRepository):
        self.repository = event_repository

    def get_event(self, event_id):
        return self.repository.find_by_id(event_id)

    def create_event(self, event_data, current_user):
        require_permission(current_user, Permission.CREATE_EVENT)

        name = validate_string_not_empty(event_data["name"], "name")
        customer_id = validate_string_not_empty(
            event_data["customer_id"], "customer_id"
        )
        contract_id = event_data.get("contract_id")
        location = event_data.get("location", "")
        attendees = event_data.get("attendees", 0)
        notes = event_data.get("notes", "")

        event = Event(
            name=name,
            customer_id=int(customer_id),
            contract_id=int(contract_id) if contract_id else None,
            support_contact_id=current_user.id,
            location=location,
            attendees=int(attendees),
            notes=notes
        )

        return self.repository.create(event)

    def update_event(self, event_id, event_data, current_user):
        require_permission(current_user, Permission.UPDATE_EVENT)

        name = validate_string_not_empty(event_data["name"], "name")
        customer_id = validate_string_not_empty(
            event_data["customer_id"], "customer_id"
        )
        contract_id = event_data.get("contract_id")
        location = event_data.get("location", "")
        attendees = event_data.get("attendees", 0)
        notes = event_data.get("notes", "")

        event = Event(
            id=event_id,
            name=name,
            customer_id=int(customer_id),
            contract_id=int(contract_id) if contract_id else None,
            support_contact_id=current_user.id,
            location=location,
            attendees=int(attendees),
            notes=notes
        )

        return self.repository.update(event)

    def delete_event(self, event_id, current_user):
        require_permission(current_user, Permission.DELETE_EVENT)
        return self.repository.delete(event_id)

    def list_events(self):
        return self.repository.list_all()
