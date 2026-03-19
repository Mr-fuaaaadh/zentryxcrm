from django.test import TestCase
from django.urls import reverse
from .models import Customer
from .forms import CustomerForm

class CustomerTests(TestCase):
    def setUp(self):
        self.customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            phone="1234567890",
            customer_type="INDIVIDUAL"
        )

    def test_customer_list_view(self):
        response = self.client.get(reverse('customers:list'))
        self.assertEqual(response.status_code, 302) # Redirects to login

    def test_customer_uniqueness(self):
        form = CustomerForm(data={
            'name': "Duplicate Customer",
            'email': "test@example.com",
            'phone': "1234567890",
            'customer_type': "INDIVIDUAL"
        })
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('phone', form.errors)
