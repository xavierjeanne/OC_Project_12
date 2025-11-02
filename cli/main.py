"""
Epic Events CLI Application Main Entry Point
"""

import click
from cli.commands import employee, customer, contract, event
from services.auth_manager import auth_manager
from cli.utils.auth import get_current_user, check_authentication

@click.group()
@click.version_option(version='1.0.0')
@click.option('--debug', is_flag=True, help='Enable debug mode with detailed messages')
@click.pass_context
def cli(ctx, debug):
    """
    Epic Events CRM - Event Management System
    
    Command-line application to manage employees, customers, 
    contracts and events for Epic Events company.
    """
    # Store global context
    ctx.ensure_object(dict)
    ctx.obj['debug'] = debug
    
    if debug:
        click.echo(click.style('Debug mode enabled', fg='yellow'))

# Add command groups
cli.add_command(employee.employee_group)
cli.add_command(customer.customer_group)
cli.add_command(contract.contract_group)
cli.add_command(event.event_group)

@cli.command()
def login():
    """Login to the application"""
    click.echo(click.style('=== Epic Events CRM Login ===', fg='blue', bold=True))
    
    employee_number = click.prompt('Employee Number (e.g., EMP001)')
    password = click.prompt('Password', hide_input=True)
    
    # Use AuthenticationManager
    result = auth_manager.login(employee_number, password)
    
    if result['success']:
        click.echo(click.style('✓ Login successful!', fg='green'))
        user = result['user']
        click.echo(f"Welcome {user['name']} ({user['role']})!")
        click.echo(f"Employee ID: {user['employee_number']}")
    else:
        click.echo(click.style(f'✗ Login failed: {result["message"]}', fg='red'))
        raise click.Abort()

@cli.command()
def logout():
    """Logout from the application"""
    if not check_authentication():
        click.echo(click.style('You are not currently logged in.', fg='yellow'))
        return
    
    result = auth_manager.logout()
    if result['success']:
        click.echo(click.style(result['message'], fg='green'))
    else:
        click.echo(click.style(f'Logout failed: {result["message"]}', fg='red'))

@cli.command()
def status():
    """Display application status and current user"""
    click.echo(click.style('=== Epic Events CRM Status ===', fg='blue', bold=True))
    click.echo('Version: 1.0.0')
    click.echo('Database: Connected')
    
    # Display current user info
    user = get_current_user()
    if user:
        click.echo(f'Logged in as: {user["name"]} ({user["employee_number"]})')
        click.echo(f'Role: {user["role"]}')
        click.echo(f'Email: {user["email"]}')
        
        # Get session info
        session_info = auth_manager.get_session_info()
        if session_info:
            expiry_minutes = int(session_info['time_until_expiry_minutes'])
            click.echo(f'Session expires in: {expiry_minutes} minutes')
    else:
        click.echo('Status: Not logged in')
        click.echo('Use "python -m cli.main login" to authenticate')


if __name__ == '__main__':
    cli()
