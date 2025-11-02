"""
Event management commands
"""

import click
from datetime import datetime
from models import Session, Event
from repositories.event import EventRepository
from services.event import EventService
from utils.validators import ValidationError
from utils.permissions import PermissionError, Permission
from cli.utils.auth import cli_auth_required, get_current_user, require_permission
from cli.utils.error_handling import handle_cli_errors, display_success_message


def get_event_service():
    """Create event service instance"""
    session = Session()
    repository = EventRepository(session)
    return EventService(repository), session


@click.group(name='event')
def event_group():
    """Event management (create, update, view, delete)"""
    pass


@event_group.command(name='list')
@click.option('--support-contact', type=int, help='Filter by support contact ID')
@click.option('--customer-id', type=int, help='Filter by customer ID')
@click.option('--upcoming', is_flag=True, help='Show only upcoming events')
@click.option('--limit', default=20, help='Maximum number of results')
@cli_auth_required
@handle_cli_errors
def list_events(support_contact, customer_id, upcoming, limit):
    """Display event list"""
    click.echo(click.style('=== Event List ===', fg='blue', bold=True))
    
    service, session = get_event_service()
    
    try:
        current_user = get_current_user()
        events = service.list_events(current_user)
        
        # Apply support contact filter if specified
        if support_contact:
            events = [event for event in events if event.support_contact_id == support_contact]
        
        # Apply customer filter if specified
        if customer_id:
            events = [event for event in events if event.customer_id == customer_id]
        
        # Apply upcoming filter if specified
        if upcoming:
            now = datetime.now()
            events = [event for event in events 
                     if event.date_start and event.date_start > now]
        
        # Apply limit
        events = events[:limit] if limit else events
        
        if not events:
            click.echo(click.style('No events found.', fg='yellow'))
            return
        
        # Display events in table format
        click.echo(f"{'ID':<5} {'Name':<30} {'Customer ID':<12} {'Location':<20} {'Attendees':<10} {'Start Date':<12}")
        click.echo('-' * 95)
        
        for event in events:
            location = (event.location[:17] + '...' if event.location and len(event.location) > 20 
                       else (event.location or 'N/A'))
            start_date = event.date_start.strftime('%Y-%m-%d') if event.date_start else 'N/A'
            click.echo(f"{event.id:<5} {event.name:<30} {event.customer_id:<12} {location:<20} {event.attendees or 0:<10} {start_date:<12}")
        
        click.echo(f"\nTotal: {len(events)} event(s)")
        
    except PermissionError as e:
        click.echo(click.style(f'Permission denied: {e}', fg='red'))
    except Exception as e:
        click.echo(click.style(f'Error: {e}', fg='red'))
    finally:
        session.close()


@event_group.command(name='create')
@click.option('--name', prompt='Event name', help='Event name')
@click.option('--customer-id', prompt='Customer ID', type=int, help='Customer ID')
@click.option('--contract-id', type=int, help='Contract ID (optional)')
@click.option('--location', help='Event location')
@click.option('--attendees', type=int, help='Number of attendees')
@click.option('--start-date', help='Start date (YYYY-MM-DD)')
@click.option('--end-date', help='End date (YYYY-MM-DD)')
@click.option('--notes', help='Event notes')
@click.option('--support-contact-id', type=int, help='Support contact employee ID')
@cli_auth_required
@require_permission(Permission.CREATE_EVENT)
@handle_cli_errors
def create_event(name, customer_id, contract_id, location, attendees, start_date, end_date, notes, support_contact_id):
    """Create a new event"""
    click.echo(click.style('=== Create Event ===', fg='blue', bold=True))
    
    service, session = get_event_service()
    
    try:
        current_user = get_current_user()
        
        event_data = {
            'name': name,
            'customer_id': str(customer_id)  # Service expects string
        }
        
        # Add optional fields if provided
        if contract_id:
            event_data['contract_id'] = str(contract_id)
        if location:
            event_data['location'] = location
        if attendees:
            event_data['attendees'] = attendees
        if start_date:
            event_data['date_start'] = start_date
        if end_date:
            event_data['date_end'] = end_date
        if notes:
            event_data['notes'] = notes
        if support_contact_id:
            event_data['support_contact_id'] = support_contact_id
        
        event = service.create_event(event_data, current_user)
        
        event_details = {
            "ID": event.id,
            "Name": event.name,
            "Customer ID": event.customer_id,
            "Support Contact ID": event.support_contact_id
        }
        
        if event.contract_id:
            event_details["Contract ID"] = event.contract_id
        if event.location:
            event_details["Location"] = event.location
        if event.attendees:
            event_details["Attendees"] = event.attendees
        if event.date_start:
            event_details["Start Date"] = event.date_start
        if event.date_end:
            event_details["End Date"] = event.date_end
        if event.notes:
            event_details["Notes"] = event.notes
        
        display_success_message("Event created successfully!", event_details)
        
    finally:
        session.close()


@event_group.command(name='update')
@click.argument('event_id', type=int)
@click.option('--name', help='New event name')
@click.option('--customer-id', type=int, help='New customer ID')
@click.option('--contract-id', type=int, help='New contract ID')
@click.option('--location', help='New event location')
@click.option('--attendees', type=int, help='New number of attendees')
@click.option('--start-date', help='New start date (YYYY-MM-DD)')
@click.option('--end-date', help='New end date (YYYY-MM-DD)')
@click.option('--notes', help='New event notes')
@click.option('--support-contact-id', type=int, help='New support contact employee ID')
@cli_auth_required
@require_permission(Permission.UPDATE_EVENT)
@handle_cli_errors
def update_event(event_id, name, customer_id, contract_id, location, attendees, start_date, end_date, notes, support_contact_id):
    """Update an existing event"""
    click.echo(click.style(f'=== Update Event {event_id} ===', fg='blue', bold=True))
    
    service, session = get_event_service()
    
    try:
        current_user = get_current_user()
        
        # Get existing event
        existing_event = service.get_event(event_id)
        if not existing_event:
            click.echo(click.style(f'Event {event_id} not found.', fg='red'))
            return
        
        # Prepare update data with only provided fields
        update_data = {}
        
        if name:
            update_data['name'] = name
        else:
            update_data['name'] = existing_event.name
            
        if customer_id:
            update_data['customer_id'] = str(customer_id)
        else:
            update_data['customer_id'] = str(existing_event.customer_id)
            
        if contract_id:
            update_data['contract_id'] = str(contract_id)
        elif existing_event.contract_id:
            update_data['contract_id'] = str(existing_event.contract_id)
            
        if location is not None:  # Allow empty string to clear location
            update_data['location'] = location
        else:
            update_data['location'] = existing_event.location or ''
            
        if attendees is not None:
            update_data['attendees'] = attendees
        else:
            update_data['attendees'] = existing_event.attendees or 0
            
        if start_date:
            update_data['date_start'] = start_date
        elif existing_event.date_start:
            update_data['date_start'] = existing_event.date_start.strftime('%Y-%m-%d')
            
        if end_date:
            update_data['date_end'] = end_date
        elif existing_event.date_end:
            update_data['date_end'] = existing_event.date_end.strftime('%Y-%m-%d')
            
        if notes is not None:  # Allow empty string to clear notes
            update_data['notes'] = notes
        else:
            update_data['notes'] = existing_event.notes or ''
            
        if support_contact_id:
            update_data['support_contact_id'] = support_contact_id
        else:
            update_data['support_contact_id'] = existing_event.support_contact_id
        
        # If no changes specified, prompt user
        if not any([name, customer_id, contract_id, location is not None, attendees is not None, 
                   start_date, end_date, notes is not None, support_contact_id]):
            click.echo('No changes specified. What would you like to update?')
            new_name = click.prompt('Name', default=existing_event.name, show_default=True)
            new_customer_id = click.prompt('Customer ID', default=existing_event.customer_id, 
                                         type=int, show_default=True)
            new_location = click.prompt('Location', default=existing_event.location or '', show_default=True)
            new_attendees = click.prompt('Attendees', default=existing_event.attendees or 0, 
                                       type=int, show_default=True)
            new_support_id = click.prompt('Support Contact ID', default=existing_event.support_contact_id, 
                                        type=int, show_default=True)
            
            update_data.update({
                'name': new_name,
                'customer_id': str(new_customer_id),
                'location': new_location,
                'attendees': new_attendees,
                'support_contact_id': new_support_id
            })
        
        updated_event = service.update_event(event_id, update_data, current_user)
        
        click.echo(click.style('✓ Event updated successfully!', fg='green'))
        click.echo(f'ID: {updated_event.id}')
        click.echo(f'Name: {updated_event.name}')
        click.echo(f'Customer ID: {updated_event.customer_id}')
        if updated_event.contract_id:
            click.echo(f'Contract ID: {updated_event.contract_id}')
        if updated_event.location:
            click.echo(f'Location: {updated_event.location}')
        event_details = {
            "ID": updated_event.id,
            "Name": updated_event.name,
            "Customer ID": updated_event.customer_id,
            "Support Contact ID": updated_event.support_contact_id
        }
        
        if updated_event.contract_id:
            event_details["Contract ID"] = updated_event.contract_id
        if updated_event.location:
            event_details["Location"] = updated_event.location
        if updated_event.attendees:
            event_details["Attendees"] = updated_event.attendees
        if updated_event.date_start:
            event_details["Start Date"] = updated_event.date_start
        if updated_event.date_end:
            event_details["End Date"] = updated_event.date_end
        if updated_event.notes:
            event_details["Notes"] = updated_event.notes
        
        display_success_message("Event updated successfully!", event_details)
        
    finally:
        session.close()


@event_group.command(name='delete')
@click.argument('event_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@cli_auth_required
@require_permission(Permission.DELETE_EVENT)
@handle_cli_errors
def delete_event(event_id, force):
    """Delete an event"""
    from cli.utils.error_handling import validate_id, display_success_message, display_info_message, ResourceNotFoundError, confirm_destructive_action
    
    # ID validation
    event_id = validate_id(event_id, "Event ID")
    
    service, session = get_event_service()
    
    try:
        current_user = get_current_user()
        
        # Get existing event to show details before deletion
        existing_event = service.get_event(event_id)
        if not existing_event:
            raise ResourceNotFoundError(f"Event with ID {event_id} does not exist.")
        
        # Show event details
        click.echo(click.style(f'=== Delete Event {event_id} ===', fg='red', bold=True))
        click.echo(f"Name: {existing_event.name}")
        click.echo(f"Customer ID: {existing_event.customer_id}")
        click.echo(f"Location: {existing_event.location or 'Not specified'}")
        if existing_event.date_start:
            click.echo(f"Start Date: {existing_event.date_start}")
        
        # Confirmation
        if not force:
            if not confirm_destructive_action(f"delete event '{existing_event.name}'"):
                display_info_message("Operation cancelled.")
                return
        
        # Perform deletion
        service.delete_event(event_id, current_user)
        
        display_success_message(f"Event '{existing_event.name}' deleted successfully!")
        
    finally:
        session.close()
