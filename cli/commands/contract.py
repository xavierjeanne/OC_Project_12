"""
Contract management commands
"""

import click
from datetime import datetime
from decimal import Decimal
from models import Session, Contract
from repositories.contract import ContractRepository
from services.contract import ContractService
from utils.validators import ValidationError
from utils.permissions import PermissionError, Permission
from cli.utils.auth import cli_auth_required, get_current_user, require_permission
from cli.utils.error_handling import handle_cli_errors, display_success_message


def get_contract_service():
    """Create contract service instance"""
    session = Session()
    repository = ContractRepository(session)
    return ContractService(repository), session


@click.group(name='contract')
def contract_group():
    """Contract management (create, update, view, delete)"""
    pass


@contract_group.command(name='list')
@click.option('--signed/--unsigned', default=None, help='Filter by signature status')
@click.option('--customer-id', type=int, help='Filter by customer ID')
@click.option('--limit', default=20, help='Maximum number of results')
@cli_auth_required
@handle_cli_errors
def list_contracts(signed, customer_id, limit):
    """Display contract list"""
    click.echo(click.style('=== Contract List ===', fg='blue', bold=True))
    
    service, session = get_contract_service()
    
    try:
        current_user = get_current_user()
        contracts = service.list_contracts(current_user)
        
        # Apply signature filter if specified
        if signed is not None:
            contracts = [contract for contract in contracts if contract.signed == signed]
        
        # Apply customer filter if specified
        if customer_id:
            contracts = [contract for contract in contracts if contract.customer_id == customer_id]
        
        # Apply limit
        contracts = contracts[:limit] if limit else contracts
        
        if not contracts:
            click.echo(click.style('No contracts found.', fg='yellow'))
            return
        
        # Display contracts in table format
        click.echo(f"{'ID':<5} {'Customer ID':<12} {'Total':<12} {'Remaining':<12} {'Status':<10} {'Sales Contact':<12}")
        click.echo('-' * 75)
        
        for contract in contracts:
            status = 'Signed' if contract.signed else 'Unsigned'
            click.echo(f"{contract.id:<5} {contract.customer_id:<12} €{contract.total_amount:<10,.2f} €{contract.remaining_amount:<10,.2f} {status:<10} {contract.sales_contact_id:<12}")
        
        click.echo(f"\nTotal: {len(contracts)} contract(s)")
        
    except PermissionError as e:
        click.echo(click.style(f'Permission denied: {e}', fg='red'))
    except Exception as e:
        click.echo(click.style(f'Error: {e}', fg='red'))
    finally:
        session.close()


@contract_group.command(name='create')
@click.option('--customer-id', prompt='Customer ID', type=int, help='Customer ID')
@click.option('--total-amount', prompt='Total amount', type=float, help='Total contract amount')
@click.option('--remaining-amount', type=float, help='Remaining amount (defaults to total)')
@click.option('--signed', is_flag=True, help='Mark contract as signed')
@click.option('--sales-contact-id', type=int, help='Sales contact employee ID')
@cli_auth_required
@require_permission(Permission.CREATE_CONTRACT)
@handle_cli_errors
def create_contract(customer_id, total_amount, remaining_amount, signed, sales_contact_id):
    """Create a new contract"""
    click.echo(click.style('=== Create Contract ===', fg='blue', bold=True))
    
    service, session = get_contract_service()
    
    try:
        current_user = get_current_user()
        
        contract_data = {
            'customer_id': str(customer_id),  # Service expects string
            'total_amount': total_amount,
            'remaining_amount': remaining_amount if remaining_amount is not None else total_amount,
            'signed': signed,
            'date_created': datetime.now()
        }
        
        # Add sales contact if provided
        if sales_contact_id:
            contract_data['sales_contact_id'] = sales_contact_id
        
        contract = service.create_contract(contract_data, current_user)
        
        display_success_message(
            "Contract created successfully!",
            {
                "ID": contract.id,
                "Customer ID": contract.customer_id,
                "Total Amount": f"€{contract.total_amount:,.2f}",
                "Remaining Amount": f"€{contract.remaining_amount:,.2f}",
                "Status": "Signed" if contract.signed else "Unsigned",
                "Sales Contact ID": contract.sales_contact_id,
                "Date Created": contract.date_created
            }
        )
        
    finally:
        session.close()


@contract_group.command(name='update')
@click.argument('contract_id', type=int)
@click.option('--customer-id', type=int, help='New customer ID')
@click.option('--total-amount', type=float, help='New total amount')
@click.option('--remaining-amount', type=float, help='New remaining amount')
@click.option('--signed/--unsigned', help='Update signature status')
@click.option('--sales-contact-id', type=int, help='New sales contact employee ID')
@cli_auth_required
@require_permission(Permission.UPDATE_CONTRACT)
@handle_cli_errors
def update_contract(contract_id, customer_id, total_amount, remaining_amount, signed, sales_contact_id):
    """Update an existing contract"""
    click.echo(click.style(f'=== Update Contract {contract_id} ===', fg='blue', bold=True))
    
    service, session = get_contract_service()
    
    try:
        current_user = get_current_user()
        
        # Get existing contract
        existing_contract = service.get_contract(contract_id)
        if not existing_contract:
            click.echo(click.style(f'Contract {contract_id} not found.', fg='red'))
            return
        
        # Prepare update data with only provided fields
        update_data = {}
        
        if customer_id:
            update_data['customer_id'] = str(customer_id)
        else:
            update_data['customer_id'] = str(existing_contract.customer_id)
            
        if total_amount is not None:
            update_data['total_amount'] = total_amount
        else:
            update_data['total_amount'] = existing_contract.total_amount
            
        if remaining_amount is not None:
            update_data['remaining_amount'] = remaining_amount
        else:
            update_data['remaining_amount'] = existing_contract.remaining_amount
            
        if signed is not None:
            update_data['signed'] = signed
        else:
            update_data['signed'] = existing_contract.signed
            
        if sales_contact_id:
            update_data['sales_contact_id'] = sales_contact_id
        else:
            update_data['sales_contact_id'] = existing_contract.sales_contact_id
            
        update_data['date_created'] = existing_contract.date_created
        
        # If no changes specified, prompt user
        if not any([customer_id, total_amount is not None, remaining_amount is not None, 
                   signed is not None, sales_contact_id]):
            click.echo('No changes specified. What would you like to update?')
            new_customer_id = click.prompt('Customer ID', default=existing_contract.customer_id, 
                                         type=int, show_default=True)
            new_total = click.prompt('Total amount', default=existing_contract.total_amount, 
                                   type=float, show_default=True)
            new_remaining = click.prompt('Remaining amount', default=existing_contract.remaining_amount, 
                                       type=float, show_default=True)
            new_signed = click.confirm('Signed?', default=existing_contract.signed)
            new_sales_id = click.prompt('Sales Contact ID', default=existing_contract.sales_contact_id, 
                                      type=int, show_default=True)
            
            update_data.update({
                'customer_id': str(new_customer_id),
                'total_amount': new_total,
                'remaining_amount': new_remaining,
                'signed': new_signed,
                'sales_contact_id': new_sales_id
            })
        
        updated_contract = service.update_contract(contract_id, update_data, current_user)
        
        display_success_message(
            "Contract updated successfully!",
            {
                "ID": updated_contract.id,
                "Customer ID": updated_contract.customer_id,
                "Total Amount": f"€{updated_contract.total_amount:,.2f}",
                "Remaining Amount": f"€{updated_contract.remaining_amount:,.2f}",
                "Status": "Signed" if updated_contract.signed else "Unsigned",
                "Sales Contact ID": updated_contract.sales_contact_id
            }
        )
        
    finally:
        session.close()


@contract_group.command(name='delete')
@click.argument('contract_id', type=int)
@click.option('--force', is_flag=True, help='Skip confirmation prompt')
@cli_auth_required
@require_permission(Permission.DELETE_CONTRACT)
@handle_cli_errors
def delete_contract(contract_id, force):
    """Delete a contract"""
    from cli.utils.error_handling import validate_id, display_success_message, display_info_message, ResourceNotFoundError, confirm_destructive_action
    
    # ID validation
    contract_id = validate_id(contract_id, "Contract ID")
    
    service, session = get_contract_service()
    
    try:
        current_user = get_current_user()
        
        # Get existing contract to show details before deletion
        existing_contract = service.get_contract(contract_id)
        if not existing_contract:
            raise ResourceNotFoundError(f"Contract with ID {contract_id} does not exist.")
        
        # Show contract details
        click.echo(click.style(f'=== Delete Contract {contract_id} ===', fg='red', bold=True))
        click.echo(f"Customer ID: {existing_contract.customer_id}")
        click.echo(f"Total Amount: €{existing_contract.total_amount:,.2f}")
        click.echo(f"Status: {'Signed' if existing_contract.signed else 'Unsigned'}")
        
        # Confirmation
        if not force:
            if not confirm_destructive_action(f"delete contract {contract_id} (€{existing_contract.total_amount:,.2f})"):
                display_info_message("Operation cancelled.")
                return
        
        # Perform deletion
        service.delete_contract(contract_id, current_user)
        
        display_success_message(f"Contract {contract_id} deleted successfully!")
        
    finally:
        session.close()
