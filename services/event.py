from models import Event
from repositories.event import EventRepository
from utils.permissions import Permission, require_permission
from utils.validators import (validate_string_not_empty, validate_date,
                              validate_non_negative_integer, ValidationError)


class EventService:
    def __init__(self, event_repository: EventRepository):
        self.repository = event_repository

    def get_event(self, event_id):
        return self.repository.find_by_id(event_id)

    def create_event(self, event_data, current_user):
        require_permission(current_user, Permission.CREATE_EVENT)

        # Valide required fields
        name = validate_string_not_empty(event_data["name"], "name")
        customer_id = validate_string_not_empty(
            event_data["customer_id"], "customer_id"
        )

        # Validation optional fields with appropriate types
        contract_id = event_data.get("contract_id")
        location = event_data.get("location", "")
        attendees = validate_non_negative_integer(
            event_data.get("attendees", 0), "attendees"
        )
        notes = event_data.get("notes", "")

        # Validation dates
        date_start = event_data.get("date_start")
        date_end = event_data.get("date_end")
        if date_start:
            date_start = validate_date(date_start, "date_start")
        if date_end:
            date_end = validate_date(date_end, "date_end")

        # Validation date_end >= date_start
        if date_start and date_end and date_end < date_start:
            raise ValidationError("End date cannot be before start date")

        # Relation with the support_contact
        if current_user['role'] in ['management', 'admin']:
            support_contact_id = event_data.get(
                "support_contact_id", current_user['id']
                )
        else:
            support_contact_id = current_user['id']

        # Validation IDs
        try:
            customer_id = int(customer_id)
            support_contact_id = int(support_contact_id)
            if contract_id:
                contract_id = int(contract_id)
        except (ValueError, TypeError):
            raise ValidationError("All ID fields must be valid integers")

        event = Event(
            name=name,
            customer_id=customer_id,
            contract_id=contract_id,
            support_contact_id=support_contact_id,
            location=location,
            attendees=attendees,
            date_start=date_start,
            date_end=date_end,
            notes=notes
        )

        return self.repository.create(event)

    def update_event(self, event_id, event_data, current_user):
        require_permission(current_user, Permission.UPDATE_EVENT)

        # Validation required fields
        name = validate_string_not_empty(event_data["name"], "name")
        customer_id = validate_string_not_empty(
            event_data["customer_id"], "customer_id"
        )

        # Validation optional fields with appropriate types
        contract_id = event_data.get("contract_id")
        location = event_data.get("location", "")
        attendees = validate_non_negative_integer(
            event_data.get("attendees", 0), "attendees"
        )
        notes = event_data.get("notes", "")

        # Validation dates
        date_start = event_data.get("date_start")
        date_end = event_data.get("date_end")
        if date_start:
            date_start = validate_date(date_start, "date_start")
        if date_end:
            date_end = validate_date(date_end, "date_end")

        # Validation  date_end >= date_start
        if date_start and date_end and date_end < date_start:
            raise ValidationError("End date cannot be before start date")

        # Relation with the support_contact
        if current_user['role'] in ['management', 'admin']:
            support_contact_id = (
                event_data.get("support_contact_id", current_user['id'])
                )
        else:
            support_contact_id = current_user['id']

        # Validation IDs
        try:
            customer_id = int(customer_id)
            support_contact_id = int(support_contact_id)
            if contract_id:
                contract_id = int(contract_id)
        except (ValueError, TypeError):
            raise ValidationError("All ID fields must be valid integers")

        event = Event(
            id=event_id,
            name=name,
            customer_id=customer_id,
            contract_id=contract_id,
            support_contact_id=support_contact_id,
            location=location,
            attendees=attendees,
            date_start=date_start,
            date_end=date_end,
            notes=notes
        )

        return self.repository.update(event)

    def delete_event(self, event_id, current_user):
        require_permission(current_user, Permission.DELETE_EVENT)
        return self.repository.delete(event_id)

    def list_events(self, current_user):
        """ list of all events by role and permissions"""
        require_permission(current_user, Permission.READ_EVENT)
        if current_user['role'] in ['management', 'sales', 'admin']:
            # managment see all events
            return self.repository.get_all()
        elif current_user['role'] == 'support':
            # support see only assignated event
            return self.repository.find_by_support_contact(current_user['id'])
        else:
            return []
