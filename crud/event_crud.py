from typing import Optional

from sqlalchemy.orm import sessionmaker

from config import engine
from models import Employee, Event
from permissions import (Permission, PermissionError,
                         can_update_own_assigned_event, require_permission)
from validators import (ValidationError, validate_date_order,
                        validate_positive_integer, validate_string_not_empty)

Session = sessionmaker(bind=engine)


def create_event(
    contract_id,
    customer_id,
    support_contact_id,
    name,
    date_start,
    date_end,
    location,
    attendees,
    notes=None,
    current_user: Optional[Employee] = None,
):
    """
    Creates a new event

    Args:
        contract_id: Associated contract's ID
        customer_id: Customer's ID
        support_contact_id: Support contact's ID
        name: Event name
        date_start: Start date
        date_end: End date
        location: Location
        attendees: Number of attendees
        notes: Notes (optional)
        current_user: The employee performing the action (for permission checking)

    Returns:
        The created event

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    # Check permissions
    if current_user:
        require_permission(current_user, Permission.CREATE_EVENT)

    # Validate data
    name = validate_string_not_empty(name, "event name")
    location = validate_string_not_empty(location, "location")
    attendees = validate_positive_integer(attendees, "number of attendees")
    validate_date_order(date_start, date_end, "start date", "end date")

    session = Session()
    try:
        event = Event(
            contract_id=contract_id,
            customer_id=customer_id,
            support_contact_id=support_contact_id,
            name=name,
            date_start=date_start,
            date_end=date_end,
            location=location,
            attendees=attendees,
            notes=notes,
        )
        session.add(event)
        session.commit()
        print(f"Event '{name}' created with id {event.id}.")
        return event
    except Exception as e:
        session.rollback()
        print(f"Error creating event: {e}")
        raise
    finally:
        session.close()


def get_all_events(current_user: Optional[Employee] = None):
    """
    Retrieves all events

    Args:
        current_user: The employee performing the action (for permission checking)

    Returns:
        List of events

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions
    if current_user:
        require_permission(current_user, Permission.READ_EVENT)

    session = Session()
    try:
        events = session.query(Event).all()
        for e in events:
            print(e.id, e.name, e.date_start, e.location, e.attendees)
        return events
    finally:
        session.close()


def update_event(event_id, current_user: Optional[Employee] = None, **kwargs):
    """
    Updates an event

    Args:
        event_id: ID of the event to update
        current_user: The employee performing the action (for permission checking)
        **kwargs: Fields to update

    Returns:
        The updated event

    Raises:
        PermissionError: If the user doesn't have permission
        ValidationError: If the data is invalid
    """
    session = Session()
    try:
        event = session.get(Event, event_id)
        if event:
            # Check permissions
            if current_user:
                # Assigned support or management can update
                if not (
                    can_update_own_assigned_event(current_user, event)
                    or current_user.role == "management"
                ):
                    require_permission(current_user, Permission.UPDATE_EVENT)

            # Validate data before update
            if "name" in kwargs:
                kwargs["name"] = validate_string_not_empty(kwargs["name"], "event name")
            if "location" in kwargs:
                kwargs["location"] = validate_string_not_empty(
                    kwargs["location"], "location"
                )
            if "attendees" in kwargs:
                kwargs["attendees"] = validate_positive_integer(
                    kwargs["attendees"], "number of attendees"
                )

            # If updating dates, check consistency
            new_start = kwargs.get("date_start", event.date_start)
            new_end = kwargs.get("date_end", event.date_end)
            if new_start and new_end:
                validate_date_order(new_start, new_end, "start date", "end date")

            for key, value in kwargs.items():
                setattr(event, key, value)
            session.commit()
            print(f"Event {event_id} updated.")
            return event
        else:
            print(f"Event {event_id} not found.")
            return None
    except (PermissionError, ValidationError):
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        print(f"Error updating event: {e}")
        raise
    finally:
        session.close()


def delete_event(event_id, current_user: Optional[Employee] = None):
    """
    Deletes an event

    Args:
        event_id: ID of the event to delete
        current_user: The employee performing the action (for permission checking)

    Returns:
        True if deletion successful, False otherwise

    Raises:
        PermissionError: If the user doesn't have permission
    """
    # Check permissions (only management can delete)
    if current_user:
        require_permission(current_user, Permission.DELETE_EVENT)

    session = Session()
    try:
        event = session.get(Event, event_id)
        if event:
            session.delete(event)
            session.commit()
            print(f"Event {event_id} deleted.")
            return True
        else:
            print(f"Event {event_id} not found.")
            return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting event: {e}")
        raise
    finally:
        session.close()
