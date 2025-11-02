"""
Customer management commands
"""

import click
from datetime import datetime
from models import Session, Customer
from repositories.customer import CustomerRepository
from services.customer import CustomerService
from utils.validators import ValidationError
from utils.permissions import PermissionError, Permission
from cli.utils.auth import cli_auth_required, get_current_user, require_permission
from cli.utils.error_handling import (
    handle_cli_errors, validate_id, display_success_message, 
    display_info_message, ResourceNotFoundError, confirm_destructive_action
)


def get_customer_service():
    """Create customer service instance"""
    session = Session()
    repository = CustomerRepository(session)
    return CustomerService(repository), session


@click.group(name='customer')
def customer_group():
    """Customer management (create, update, view, delete)"""
    pass


@customer_group.command(name='list')
@click.option('--sales-contact', type=int, help='Filter by sales contact ID')
@click.option('--limit', default=20, help='Maximum number of results')
@cli_auth_required
@handle_cli_errors
def list_customers(sales_contact, limit):
    """Display customer list"""
    click.echo(click.style('=== Customer List ===', fg='blue', bold=True))
    
    # Parameter validation
    if sales_contact is not None:
        sales_contact = validate_id(sales_contact, "Sales contact ID")
    if limit <= 0:
        limit = 20
    
    service, session = get_customer_service()
    
    try:
        current_user = get_current_user()
        customers = service.list_customers(current_user)
        
        # Apply sales contact filter if specified
        if sales_contact:
            customers = [cust for cust in customers if cust.sales_contact_id == sales_contact]
        
        # Apply limit
        customers = customers[:limit] if limit else customers
        
        if not customers:
            display_info_message('No customers found.')
            return
        
        # Display customers in table format
        click.echo(f"{'ID':<5} {'Company':<25} {'Contact':<20} {'Email':<30} {'Sales':<6}")
        click.echo('-' * 86)
        
        for customer in customers:
            click.echo(f"{customer.id:<5} {customer.company_name or 'N/A':<25} {customer.full_name:<20} "
                      f"{customer.email:<30} {customer.sales_contact_id or 'N/A':<6}")
        
        click.echo(f"\nTotal: {len(customers)} customer(s)")
        
    finally:
        session.close()


@customer_group.command(name='create')
@click.option('--company-name', prompt='Company name', help='Customer company name')
@click.option('--contact-name', prompt='Contact name', help='Customer contact person name')
@click.option('--email', prompt='Email', help='Customer email address')
@click.option('--phone', help='Customer phone number')
@click.option('--sales-contact-id', type=int, help='Sales contact employee ID')
@cli_auth_required
@require_permission(Permission.CREATE_CUSTOMER)
@handle_cli_errors
def create_customer(company_name, contact_name, email, phone, sales_contact_id):
    """Create a new customer"""
    click.echo(click.style('=== Create New Customer ===', fg='blue', bold=True))
    
    # Input data validation
    if not company_name.strip():
        raise ValidationError("Company name cannot be empty")
    if not contact_name.strip():
        raise ValidationError("Contact name cannot be empty")
    if not email.strip():
        raise ValidationError("Email cannot be empty")
    
    if sales_contact_id is not None:
        sales_contact_id = validate_id(sales_contact_id, "Sales contact ID")
    
    service, session = get_customer_service()
    
    try:
        current_user = get_current_user()
        
        customer_data = {
            'full_name': contact_name.strip(),
            'company_name': company_name.strip(),
            'email': email.strip()
        }
        
        # Add optional fields if provided
        if phone and phone.strip():
            customer_data['phone'] = phone.strip()
        if sales_contact_id:
            customer_data['sales_contact_id'] = sales_contact_id
        
        customer = service.create_customer(customer_data, current_user)
        
        display_success_message(
            "Customer created successfully!",
            {
                "ID": customer.id,
                "Company": customer.company_name,
                "Contact": customer.full_name,
                "Email": customer.email,
                "Phone": customer.phone or "Not provided",
                "Sales Contact": customer.sales_contact_id or "Not assigned"
            }
        )
        
    finally:
        session.close()


@customer_group.command(name='update')
@click.argument('customer_id', type=int)
@click.option('--company-name', help='Nouveau nom de société')
@click.option('--contact-name', help='Nouveau nom de contact')
@click.option('--email', help='Nouvelle adresse email')
@click.option('--phone', help='Nouveau numéro de téléphone')
@click.option('--sales-contact-id', type=int, help='Nouvel ID du contact commercial')
@cli_auth_required
@require_permission(Permission.UPDATE_CUSTOMER)
@handle_cli_errors
def update_customer(customer_id, company_name, contact_name, email, phone, sales_contact_id):
    """Update an existing customer"""
    # ID validation
    customer_id = validate_id(customer_id, "Customer ID")
    
    click.echo(click.style(f'=== Update Customer {customer_id} ===', fg='blue', bold=True))
    
    # Validate other parameters
    if sales_contact_id is not None:
        sales_contact_id = validate_id(sales_contact_id, "Sales contact ID")
    
    service, session = get_customer_service()
    
    try:
        current_user = get_current_user()
        
        # Get existing customer
        existing_customer = service.get_customer(customer_id)
        if not existing_customer:
            raise ResourceNotFoundError(f"Customer with ID {customer_id} does not exist.")
        
        # Prepare update data with only provided fields
        update_data = {}
        
        if company_name:
            if not company_name.strip():
                raise ValidationError("Le nom de la société ne peut pas être vide")
            update_data['company_name'] = company_name.strip()
        else:
            update_data['company_name'] = existing_customer.company_name
            
        if contact_name:
            if not contact_name.strip():
                raise ValidationError("Le nom du contact ne peut pas être vide")
            update_data['full_name'] = contact_name.strip()
        else:
            update_data['full_name'] = existing_customer.full_name
            
        if email:
            if not email.strip():
                raise ValidationError("L'email ne peut pas être vide")
            update_data['email'] = email.strip()
        else:
            update_data['email'] = existing_customer.email
            
        if phone is not None:  # Allow empty string to clear phone
            update_data['phone'] = phone.strip() if phone else None
        else:
            update_data['phone'] = existing_customer.phone
            
        if sales_contact_id:
            update_data['sales_contact_id'] = sales_contact_id
        else:
            update_data['sales_contact_id'] = existing_customer.sales_contact_id
        
        # If no changes specified, prompt user
        if not any([company_name, contact_name, email, phone is not None, sales_contact_id]):
            display_info_message('No changes specified. Interactive mode:')
            new_company = click.prompt('Company name', default=existing_customer.company_name, show_default=True)
            new_contact = click.prompt('Contact name', default=existing_customer.full_name, show_default=True)
            new_email = click.prompt('Email', default=existing_customer.email, show_default=True)
            new_phone = click.prompt('Phone', default=existing_customer.phone or '', show_default=True)
            new_sales_id = click.prompt('Sales contact ID', default=existing_customer.sales_contact_id or '', 
                                       show_default=True)
            
            # Validate interactively entered data
            if not new_company.strip():
                raise ValidationError("Company name cannot be empty")
            if not new_contact.strip():
                raise ValidationError("Contact name cannot be empty") 
            if not new_email.strip():
                raise ValidationError("Email cannot be empty")
            
            update_data.update({
                'company_name': new_company.strip(),
                'full_name': new_contact.strip(),
                'email': new_email.strip(),
                'phone': new_phone.strip() if new_phone else None,
                'sales_contact_id': validate_id(new_sales_id, "Sales contact ID") if new_sales_id else None
            })
        
        updated_customer = service.update_customer(customer_id, update_data, current_user)
        
        display_success_message(
            "Customer updated successfully!",
            {
                "ID": updated_customer.id,
                "Company": updated_customer.company_name,
                "Contact": updated_customer.full_name,
                "Email": updated_customer.email,
                "Phone": updated_customer.phone or "Not provided",
                "Sales Contact": updated_customer.sales_contact_id or "Not assigned"
            }
        )
        
    finally:
        session.close()


@customer_group.command(name='delete')
@click.argument('customer_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@cli_auth_required
@require_permission(Permission.DELETE_CUSTOMER)
@handle_cli_errors
def delete_customer(customer_id, force):
    """Delete a customer"""
    # ID validation
    customer_id = validate_id(customer_id, "Customer ID")
    
    service, session = get_customer_service()
    
    try:
        current_user = get_current_user()
        
        # Get existing customer to show details before deletion
        existing_customer = service.get_customer(customer_id)
        if not existing_customer:
            raise ResourceNotFoundError(f"Customer with ID {customer_id} does not exist.")
        
        # Show customer details
        click.echo(click.style(f'=== Delete Customer {customer_id} ===', fg='red', bold=True))
        click.echo(f"Company: {existing_customer.company_name}")
        click.echo(f"Contact: {existing_customer.full_name}")
        click.echo(f"Email: {existing_customer.email}")
        
        # Confirmation
        if not force:
            if not confirm_destructive_action(f"delete customer '{existing_customer.company_name}'"):
                display_info_message("Operation cancelled.")
                return
        
        # Perform deletion
        service.delete_customer(customer_id, current_user)
        
        display_success_message(f"Customer '{existing_customer.company_name}' deleted successfully!")
        
    finally:
        session.close()
