"""
Contract management commands
"""

import click
from datetime import datetime
from models import Session
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


@click.group(name="contract")
def contract_group():
    """Contract management (create, update, view, delete)"""


@contract_group.command(name="list")
@click.option("--signed/--unsigned", default=None, help="Filter by signature status")
@click.option(
    "--unpaid", is_flag=True, help="Show only contracts with outstanding balance"
)
@click.option("--customer-id", type=int, help="Filter by customer ID")
@click.option("--limit", default=20, help="Maximum number of results")
@cli_auth_required
@handle_cli_errors
def list_contracts(signed, unpaid, customer_id, limit):
    """Display contract list"""
    click.echo(click.style("=== Contract List ===", fg="blue", bold=True))

    service, session = get_contract_service()

    try:
        current_user = get_current_user()

        # Use specialized repository methods for efficient filtering
        repository = service.repository

        if unpaid:
            contracts = repository.find_with_balance()
            click.echo(
                click.style(
                    "Contracts with outstanding balance:", fg="yellow", bold=True
                )
            )
        elif signed is False:
            contracts = repository.find_unsigned()
            click.echo(click.style("Unsigned contracts:", fg="cyan", bold=True))
        elif signed is True:
            contracts = repository.find_signed()
            click.echo(click.style("Signed contracts:", fg="green", bold=True))
        else:
            contracts = service.list_contracts(current_user)

        # Apply customer filter if specified
        if customer_id:
            contracts = [
                contract
                for contract in contracts
                if contract.customer_id == customer_id
            ]

        # Apply limit
        contracts = contracts[:limit] if limit else contracts

        if not contracts:
            click.echo(click.style("No contracts found.", fg="yellow"))
            return

        # Display contracts in table format
        click.echo(
            f"{'ID':<5} {'Customer':<10} {'Total':<15} {'Remaining':<15} {'Status':<10} {'Sales':<8}"
        )
        click.echo("-" * 63)

        for contract in contracts:
            # Status formatting
            if contract.signed:
                status_display = click.style("Signed", fg="green")
            else:
                status_display = click.style("Unsigned", fg="cyan")

            # Payment status formatting
            remaining = contract.remaining_amount or 0
            total_display = f"€{contract.total_amount:,.2f}"
            
            if remaining > 0:
                remaining_display = click.style(f"€{remaining:,.2f}", fg="yellow", bold=True)
            else:
                remaining_display = click.style("€0.00 (Paid)", fg="green")

            click.echo(
                f"{contract.id:<5} {contract.customer_id:<10} "
                f"{total_display:<15} {remaining_display:<25} "
                f"{status_display:<20} {contract.sales_contact_id or 'N/A':<8}"
            )

        click.echo(f"\nTotal: {len(contracts)} contract(s)")

    except PermissionError as e:
        click.echo(click.style(f"Permission denied: {e}", fg="red"))
    except Exception as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
    finally:
        session.close()


@contract_group.command(name="create")
@click.option("--customer-id", prompt="Customer ID", type=int, help="Customer ID")
@click.option(
    "--total-amount", prompt="Total amount", type=float, help="Total contract amount"
)
@click.option(
    "--remaining-amount", type=float, help="Remaining amount (defaults to total)"
)
@click.option("--signed", is_flag=True, help="Mark contract as signed")
@click.option("--sales-contact-id", type=int, help="Sales contact employee ID")
@cli_auth_required
@require_permission(Permission.CREATE_CONTRACT)
@handle_cli_errors
def create_contract(
    customer_id, total_amount, remaining_amount, signed, sales_contact_id
):
    """Create a new contract"""
    click.echo(click.style("=== Create Contract ===", fg="blue", bold=True))

    service, session = get_contract_service()

    try:
        current_user = get_current_user()

        contract_data = {
            "customer_id": str(customer_id),  # Service expects string
            "total_amount": total_amount,
            "remaining_amount": (
                remaining_amount if remaining_amount is not None else total_amount
            ),
            "signed": signed,
            "date_created": datetime.now(),
        }

        # Add sales contact if provided
        if sales_contact_id:
            contract_data["sales_contact_id"] = sales_contact_id

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
                "Date Created": contract.date_created,
            },
        )

    finally:
        session.close()


@contract_group.command(name="update")
@click.argument("contract_id", type=int)
@click.option("--customer-id", type=int, help="New customer ID")
@click.option("--total-amount", type=float, help="New total amount")
@click.option("--remaining-amount", type=float, help="New remaining amount")
@click.option("--signed/--unsigned", default=None, help="Update signature status")
@click.option("--sales-contact-id", type=int, help="New sales contact employee ID")
@cli_auth_required
@require_permission(Permission.UPDATE_CONTRACT)
@handle_cli_errors
def update_contract(
    contract_id, customer_id, total_amount, remaining_amount, signed, sales_contact_id
):
    """Update an existing contract"""
    click.echo(
        click.style(f"=== Update Contract {contract_id} ===", fg="blue", bold=True)
    )

    service, session = get_contract_service()

    try:
        current_user = get_current_user()

        # Get existing contract
        existing_contract = service.get_contract(contract_id)
        if not existing_contract:
            click.echo(click.style(f"Contract {contract_id} not found.", fg="red"))
            return

        # Prepare update data with only provided fields
        update_data = {}

        if customer_id:
            update_data["customer_id"] = str(customer_id)
        else:
            update_data["customer_id"] = str(existing_contract.customer_id)

        if total_amount is not None:
            update_data["total_amount"] = total_amount
        else:
            update_data["total_amount"] = existing_contract.total_amount

        if remaining_amount is not None:
            update_data["remaining_amount"] = remaining_amount
        else:
            update_data["remaining_amount"] = existing_contract.remaining_amount

        if signed is not None:
            update_data["signed"] = signed
        else:
            update_data["signed"] = existing_contract.signed

        if sales_contact_id:
            update_data["sales_contact_id"] = sales_contact_id
        else:
            update_data["sales_contact_id"] = existing_contract.sales_contact_id

        update_data["date_created"] = existing_contract.date_created

        # If no changes specified, prompt user
        if not any(
            [
                customer_id is not None,
                total_amount is not None,
                remaining_amount is not None,
                signed is not None,
                sales_contact_id is not None,
            ]
        ):
            click.echo("No changes specified. What would you like to update?")
            new_customer_id = click.prompt(
                "Customer ID",
                default=existing_contract.customer_id,
                type=int,
                show_default=True,
            )
            new_total = click.prompt(
                "Total amount",
                default=existing_contract.total_amount,
                type=float,
                show_default=True,
            )
            new_remaining = click.prompt(
                "Remaining amount",
                default=existing_contract.remaining_amount,
                type=float,
                show_default=True,
            )
            new_signed = click.confirm("Signed?", default=existing_contract.signed)
            new_sales_id = click.prompt(
                "Sales Contact ID",
                default=existing_contract.sales_contact_id,
                type=int,
                show_default=True,
            )

            update_data.update(
                {
                    "customer_id": str(new_customer_id),
                    "total_amount": new_total,
                    "remaining_amount": new_remaining,
                    "signed": new_signed,
                    "sales_contact_id": new_sales_id,
                }
            )

        updated_contract = service.update_contract(
            contract_id, update_data, current_user
        )

        display_success_message(
            "Contract updated successfully!",
            {
                "ID": updated_contract.id,
                "Customer ID": updated_contract.customer_id,
                "Total Amount": f"€{updated_contract.total_amount:,.2f}",
                "Remaining Amount": f"€{updated_contract.remaining_amount:,.2f}",
                "Status": "Signed" if updated_contract.signed else "Unsigned",
                "Sales Contact ID": updated_contract.sales_contact_id,
            },
        )

    finally:
        session.close()


@contract_group.command(name="delete")
@click.argument("contract_id", type=int)
@click.option("--force", is_flag=True, help="Skip confirmation prompt")
@cli_auth_required
@require_permission(Permission.DELETE_CONTRACT)
@handle_cli_errors
def delete_contract(contract_id, force):
    """Delete a contract"""
    from cli.utils.error_handling import (
        validate_id,
        display_success_message,
        display_info_message,
        ResourceNotFoundError,
        confirm_destructive_action,
    )

    # ID validation
    contract_id = validate_id(contract_id, "Contract ID")

    service, session = get_contract_service()

    try:
        current_user = get_current_user()

        # Get existing contract to show details before deletion
        existing_contract = service.get_contract(contract_id)
        if not existing_contract:
            raise ResourceNotFoundError(
                f"Contract with ID {contract_id} does not exist."
            )

        # Show contract details
        click.echo(
            click.style(f"=== Delete Contract {contract_id} ===", fg="red", bold=True)
        )
        click.echo(f"Customer ID: {existing_contract.customer_id}")
        click.echo(f"Total Amount: €{existing_contract.total_amount:,.2f}")
        click.echo(f"Status: {'Signed' if existing_contract.signed else 'Unsigned'}")

        # Confirmation
        if not force:
            if not confirm_destructive_action(
                f"delete contract {contract_id}"
                f"(€{existing_contract.total_amount:,.2f})"
            ):
                display_info_message("Operation cancelled.")
                return

        # Perform deletion
        service.delete_contract(contract_id, current_user)

        display_success_message(f"Contract {contract_id} deleted successfully!")

    finally:
        session.close()


@contract_group.command(name="sign")
@click.option("--contract-id", type=int, required=True, help="Contract ID to sign")
@cli_auth_required
@handle_cli_errors
def sign_contract(contract_id):
    """Sign a contract (specific action for business traceability)"""
    service, session = get_contract_service()
    current_user = get_current_user()

    try:
        # Get existing contract to show details before signing
        existing_contract = service.get_contract(contract_id)
        if not existing_contract:
            raise ValidationError(f"Contract with ID {contract_id} does not exist.")

        if existing_contract.signed:
            click.echo(
                click.style(
                    f"Warning: Contract {contract_id} is already signed!", fg="yellow"
                )
            )
            return

        # Show contract details
        click.echo(
            click.style(f"=== Sign Contract {contract_id} ===", fg="blue", bold=True)
        )
        click.echo(f"Customer ID: {existing_contract.customer_id}")
        click.echo(f"Total Amount: €{existing_contract.total_amount:,.2f}")
        click.echo(f"Remaining Amount: €{existing_contract.remaining_amount:,.2f}")
        click.echo("Current Status: Unsigned")

        # Confirmation for important action
        if not click.confirm(
            click.style(
                f"Do you want to sign this contract for €"
                f"{existing_contract.total_amount:,.2f}?",
                fg="yellow",
                bold=True,
            )
        ):
            click.echo("Signature cancelled.")
            return

        # Perform signature
        signed_contract = service.sign_contract(contract_id, current_user)

        # Success message
        click.echo(click.style("Contract signed successfully!", fg="green", bold=True))
        click.echo(f"   Contract ID: {signed_contract.id}")
        click.echo(f"   Amount: €{signed_contract.total_amount:,.2f}")
        click.echo("   Status: Signed")
        click.echo(f"   Signed by: {current_user.email}")

    finally:
        session.close()
