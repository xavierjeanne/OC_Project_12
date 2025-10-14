

from models import Customer
from repositories.customer import CustomerRepository
from security.permissions import Permission, require_permission
from utils.validators import (validate_email, validate_phone,
                                    validate_string_not_empty)


class CustomerService:
    def __init__(self, customer_repository : CustomerRepository):
        self.repository = customer_repository

    def get_customer(self, customer_id):
        return self.repository.find_by_id(customer_id)

    def create_customer(self, customer_data, current_user):
        require_permission(current_user, Permission.CREATE_CUSTOMER)

        full_name = validate_string_not_empty(customer_data["full_name"], "full_name")
        email = validate_email(customer_data["email"])
        phone = validate_phone(customer_data.get("phone"))
        company_name = customer_data.get("company_name", "")

        customer = Customer(
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            sales_contact_id=current_user.id
        )

        return self.repository.create(customer)

    def update_customer(self, customer_id, customer_data, current_user):
        require_permission(current_user, Permission.UPDATE_CUSTOMER)

        full_name = validate_string_not_empty(customer_data["full_name"],
                                              "full_name")
        email = validate_email(customer_data["email"])
        phone = validate_phone(customer_data.get("phone"))
        company_name = customer_data.get("company_name", "")

        customer = Customer(
            id=customer_id,
            full_name=full_name,
            email=email,
            phone=phone,
            company_name=company_name,
            sales_contact_id=current_user.id
        )

        return self.repository.update(customer)

    def delete_customer(self, customer_id, current_user):
        require_permission(current_user, Permission.DELETE_CUSTOMER)
        return self.repository.delete(customer_id)

    def list_customers(self):
        return self.repository.list_all()
