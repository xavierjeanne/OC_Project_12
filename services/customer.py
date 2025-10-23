

from models import Customer
from repositories.customer import CustomerRepository
from utils.permissions import Permission, require_permission
from utils.validators import (validate_email, validate_phone,
                              validate_string_not_empty, ValidationError)


class CustomerService:
    def __init__(self, customer_repository: CustomerRepository):
        self.repository = customer_repository

    def get_customer(self, customer_id):
        return self.repository.find_by_id(customer_id)

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

        customer = Customer(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            sales_contact_id=sales_contact_id
        )

        return self.repository.create(customer)

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

        customer = Customer(
            id=customer_id,
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            sales_contact_id=sales_contact_id
        )

        return self.repository.update(customer)

    def delete_customer(self, customer_id, current_user):
        require_permission(current_user, Permission.DELETE_CUSTOMER)
        return self.repository.delete(customer_id)

    def list_customers(self, current_user):
        """List customers based on user role and permissions"""
        require_permission(current_user, Permission.READ_CUSTOMER)
        if current_user['role'] in ['management', 'admin', 'support']:
            # Management/Admin/Support see all customers
            return self.repository.get_all()
        elif current_user['role'] == 'sales':
            # Sales only see assigned customers
            return self.repository.find_by_sales_contact(current_user['id'])
        else:
            # Other roles have no access
            return []
