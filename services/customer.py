

from sqlalchemy.exc import IntegrityError
from models import Customer
from repositories.customer import CustomerRepository
from utils.permissions import Permission, require_permission
from utils.validators import (validate_email, validate_phone,
                              validate_string_not_empty, ValidationError)


class CustomerService:
    def __init__(self, customer_repository: CustomerRepository):
        self.repository = customer_repository

    def get_customer(self, customer_id):
        return self.repository.get_by_id(customer_id)

    def create_customer(self, customer_data, current_user):
        require_permission(current_user, Permission.CREATE_CUSTOMER)

        # Validation required fields
        full_name = validate_string_not_empty(customer_data["full_name"], "full_name")
        email = validate_email(customer_data["email"])

        # Validation optional fields
        phone = validate_phone(customer_data.get("phone"))
        company_name = customer_data.get("company_name", "")

        # Relation with the sales_contact (can be modified by management)
        if current_user.get('role') in ['management', 'admin']:
            sales_contact_id = customer_data.get(
                "sales_contact_id", current_user.get('id')
                )
        else:
            sales_contact_id = current_user.get('id')

        try:
            sales_contact_id = int(sales_contact_id)
        except (ValueError, TypeError):
            raise ValidationError("Sales Contact ID must be a valid integer")

        customer_data_dict = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'company_name': company_name,
            'sales_contact_id': sales_contact_id
        }

        try:
            return self.repository.create(customer_data_dict)
        except IntegrityError as e:
            # Check if it's a duplicate email error
            if "customers_email_key" in str(e) or "email" in str(e).lower():
                raise ValidationError(f"This email address '{email}' is already used by another customer.")
            # Other integrity errors
            raise ValidationError("Data conflict: some information is already in use.")

    def update_customer(self, customer_id, customer_data, current_user):
        require_permission(current_user, Permission.UPDATE_CUSTOMER)

        # Validation required fields
        full_name = validate_string_not_empty(customer_data["full_name"], "full_name")
        email = validate_email(customer_data["email"])

        # Validation optional fields
        phone = validate_phone(customer_data.get("phone"))
        company_name = customer_data.get("company_name", "")

        # Relation with the sales_contact (can be modified by management)
        if current_user.get('role') in ['management', 'admin']:
            sales_contact_id = customer_data.get(
                "sales_contact_id", current_user.get('id')
                )
        else:
            sales_contact_id = current_user.get('id')

        try:
            sales_contact_id = int(sales_contact_id)
        except (ValueError, TypeError):
            raise ValidationError("Sales Contact ID must be a valid integer")

        customer_data_dict = {
            'full_name': full_name,
            'email': email,
            'phone': phone,
            'company_name': company_name,
            'sales_contact_id': sales_contact_id
        }

        try:
            return self.repository.update(customer_id, customer_data_dict)
        except IntegrityError as e:
            # Vérifier si c'est une erreur d'email dupliqué
            if "customers_email_key" in str(e) or "email" in str(e).lower():
                raise ValidationError(f"Cette adresse email '{email}' est déjà utilisée par un autre client.")
            # Autres erreurs d'intégrité
            raise ValidationError("Conflit de données : certaines informations sont déjà utilisées.")

    def delete_customer(self, customer_id, current_user):
        require_permission(current_user, Permission.DELETE_CUSTOMER)
        return self.repository.delete(customer_id)

    def list_customers(self, current_user):
        """List customers - all users can see all customers (read-only access)"""
        require_permission(current_user, Permission.READ_CUSTOMER)
        # CONFORMITÉ: Tous les collaborateurs doivent pouvoir accéder à tous les clients en lecture seule
        return self.repository.get_all()
