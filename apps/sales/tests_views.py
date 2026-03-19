from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from apps.sales.models import Proposal
from apps.customers.models import Customer
from django.utils import timezone
import decimal

User = get_user_model()

class ProposalListViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123', role='SALES')
        self.client.login(email='test@example.com', password='password123')
        
        self.customer = Customer.objects.create(
            name="Test Customer",
            email="test@example.com",
            phone="1234567890"
        )
        
        # Create some proposals
        self.p1 = Proposal.objects.create(
            document_number="PROP-001",
            customer=self.customer,
            total_amount=decimal.Decimal("100.00"),
            status="DRAFT",
            issue_date=timezone.now().date(),
            created_by=self.user
        )
        self.p2 = Proposal.objects.create(
            document_number="PROP-002",
            customer=self.customer,
            total_amount=decimal.Decimal("200.00"),
            status="SENT",
            issue_date=timezone.now().date() - timezone.timedelta(days=1),
            created_by=self.user
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/sales/proposals/')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('sales:proposal_list'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('sales:proposal_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sales/proposal-list.html')

    def test_search_functionality(self):
        response = self.client.get(reverse('sales:proposal_list'), {'search': '001'})
        self.assertIn(self.p1, response.context['proposals'])
        self.assertNotIn(self.p2, response.context['proposals'])

    def test_status_filter(self):
        response = self.client.get(reverse('sales:proposal_list'), {'status': 'SENT'})
        self.assertIn(self.p2, response.context['proposals'])
        self.assertNotIn(self.p1, response.context['proposals'])

    def test_sorting(self):
        # Default sort is -issue_date, so p1 should be first
        response = self.client.get(reverse('sales:proposal_list'))
        self.assertEqual(list(response.context['proposals']), [self.p1, self.p2])

        # Sort by total_amount ascending
        response = self.client.get(reverse('sales:proposal_list'), {'sort': 'total_amount'})
        self.assertEqual(list(response.context['proposals']), [self.p1, self.p2])

        # Sort by total_amount descending
        response = self.client.get(reverse('sales:proposal_list'), {'sort': '-total_amount'})
        self.assertEqual(list(response.context['proposals']), [self.p2, self.p1])

class ProposalCreateViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser2', email='test2@example.com', password='password123', role='SALES')
        self.client.login(email='test2@example.com', password='password123')
        
        self.customer = Customer.objects.create(
            name="Test Customer 2",
            email="test2@example.com",
            phone="0987654321"
        )

    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('/sales/proposals/add/')
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('sales:proposal_add'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sales/proposal-add.html')

    def test_proposal_creation_with_items(self):
        data = {
            'document_number': 'PROP-TEST-001',
            'customer': self.customer.id,
            'issue_date': '2023-10-01',
            'expiry_date': '2023-11-01',
            'status': 'DRAFT',
            'subtotal': '100.00',
            'tax_amount': '10.00',
            'discount_amount': '0.00',
            'total_amount': '110.00',
            'notes': 'Test notes',
            # Formset management form
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            # Item 1
            'items-0-product': '',
            'items-0-description': 'Test Item',
            'items-0-quantity': '1',
            'items-0-unit_price': '100.00',
            'items-0-tax_percent': '10.00',
            'items-0-total': '110.00',
        }
        response = self.client.post(reverse('sales:proposal_add'), data)
        self.assertEqual(response.status_code, 302) # Redirect on success
        
        proposal = Proposal.objects.get(document_number='PROP-TEST-001')
        self.assertEqual(proposal.total_amount, decimal.Decimal('110.00'))
        self.assertEqual(proposal.items.count(), 1)
        self.assertEqual(proposal.items.first().total, decimal.Decimal('110.00'))

    def test_proposal_update(self):
        # Create a proposal first
        proposal = Proposal.objects.create(
            document_number="PROP-UPDATE-01",
            customer=self.customer,
            total_amount=decimal.Decimal("100.00"),
            status="DRAFT",
            issue_date=timezone.now().date(),
            created_by=self.user
        )
        data = {
            'document_number': 'PROP-UPDATE-01-CHANGED',
            'customer': self.customer.id,
            'issue_date': '2023-10-02',
            'status': 'SENT',
            'subtotal': '50.00',
            'tax_amount': '0.00',
            'discount_amount': '0.00',
            'total_amount': '50.00',
            'items-TOTAL_FORMS': '1',
            'items-INITIAL_FORMS': '0',
            'items-MIN_NUM_FORMS': '0',
            'items-MAX_NUM_FORMS': '1000',
            'items-0-product': '',
            'items-0-description': 'Updated Item',
            'items-0-quantity': '1',
            'items-0-unit_price': '50.00',
            'items-0-tax_percent': '0.00',
            'items-0-total': '50.00',
        }
        response = self.client.post(reverse('sales:proposal_edit', kwargs={'pk': proposal.pk}), data)
        self.assertEqual(response.status_code, 302)
        proposal.refresh_from_db()
        self.assertEqual(proposal.document_number, 'PROP-UPDATE-01-CHANGED')
        self.assertEqual(proposal.status, 'SENT')

    def test_proposal_delete(self):
        proposal = Proposal.objects.create(
            document_number="PROP-DELETE-01",
            customer=self.customer,
            total_amount=decimal.Decimal("100.00"),
            status="DRAFT",
            issue_date=timezone.now().date(),
            created_by=self.user
        )
        response = self.client.post(reverse('sales:proposal_delete', kwargs={'pk': proposal.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Proposal.objects.filter(pk=proposal.pk).exists())
