import logging
from django.shortcuts import render, redirect
from django.views import View
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from .forms import EmailAuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.db.models import Sum, Count, Q
from django.utils import timezone
from apps.customers.models import Customer
from apps.lead.models import Lead, LeadActivity
from apps.staff.models import Staff
from apps.sales.models import Invoice, StaffMonthlyTarget, StaffPerformance, Proposal, Estimate
from django.contrib.admin.models import LogEntry

logger = logging.getLogger(__name__)


class SignInView(View):
    """
    Handles user authentication for the CRM system.
    Includes error handling and feedback via Django messages.
    """
    
    @method_decorator(never_cache)
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('accounts:dashboard') 
        form = EmailAuthenticationForm()
        return render(request, 'auth-signin.html', {'form': form})

    def post(self, request):
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name()}!")            
            next_url = request.GET.get('next', 'accounts:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid email or password. Please try again.")
            return render(request, 'auth-signin.html', {'form': form})

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Main dashboard for the CRM, providing key metrics and insights.
    Optimized for performance with aggregated queries and efficient indexing.
    """
    template_name = 'dashboard_placeholder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # 1. Headline Statistics (Aggregated for efficiency)
            stats = Lead.objects.aggregate(
                total_customers=Count('id', filter=Q(is_converted=True)),
                active_leads=Count('id', filter=~Q(status__in=['won', 'lost'])),
                monthly_won_deals=Count('id', filter=Q(status='won', converted_at__gte=start_of_month)),
                estimated_pipeline=Sum('expected_revenue', filter=~Q(status__in=['won', 'lost']))
            )
            
            # Real customer count from Customer app
            stats['total_customers_actual'] = Customer.objects.count()
            context['stats'] = stats

            # 2. Top deals of this month (High potential revenue)
            context['top_deals'] = Lead.objects.filter(
                created_at__gte=start_of_month,
                expected_revenue__isnull=False
            ).exclude(status='lost').order_by('-expected_revenue')[:5]

            # 3. Delayed deals (Follow-up date has passed)
            context['delayed_leads'] = Lead.objects.filter(
                next_follow_up__lt=now,
                status__in=['new', 'contacted', 'qualified', 'proposal_sent', 'negotiation']
            ).select_related('assigned_to').order_by('next_follow_up')[:5]

            # 4. Recent Activity (CRM Specific)
            context['recent_activities'] = LeadActivity.objects.select_related(
                'lead', 'created_by'
            ).order_by('-activity_date')[:10]

            # 5. System Log Entries (Admin Specific)
            context['system_logs'] = LogEntry.objects.select_related(
                'user', 'content_type'
            ).order_by('-action_time')[:10]

            # 6. Top Customers (By Revenue)
            context['top_customers'] = Customer.objects.annotate(
                total_revenue=Sum('invoices__total_amount', filter=~Q(invoices__status__in=['REJECTED', 'CANCELLED']))
            ).filter(total_revenue__gt=0).order_by('-total_revenue')[:5]

            # 7. Revenue Analytics Metrics (for revenueAnalytics.html)
            revenue_stats = Invoice.objects.exclude(status__in=['REJECTED', 'CANCELLED']).aggregate(
                total_revenue=Sum('total_amount') or 0,
                revenue_this_month=Sum('total_amount', filter=Q(issue_date__gte=start_of_month)) or 0
            )

            # Revenue Last Month
            start_of_last_month = (start_of_month - timezone.timedelta(days=1)).replace(day=1)
            end_of_last_month = start_of_month - timezone.timedelta(seconds=1)
            revenue_stats['revenue_last_month'] = Invoice.objects.filter(
                issue_date__range=(start_of_last_month, end_of_last_month)
            ).exclude(status__in=['REJECTED', 'CANCELLED']).aggregate(total=Sum('total_amount'))['total'] or 0

            # Revenue Growth
            growth = 0
            if revenue_stats['revenue_last_month'] > 0:
                growth = ((revenue_stats['revenue_this_month'] - revenue_stats['revenue_last_month']) / 
                          revenue_stats['revenue_last_month']) * 100
            revenue_stats['growth'] = round(growth, 1)
            
            # Monthly Revenue for Chart (Last 6 Months)
            monthly_data = []
            month_labels = []
            for i in range(5, -1, -1):
                month_date = start_of_month - timezone.timedelta(days=i*30) # Rough estimate for labels
                month_start = (start_of_month - timezone.timedelta(days=i*31)).replace(day=1) # Safer start
                # Fix: better way to get month starts
                current_m = start_of_month
                for _ in range(i):
                    current_m = (current_m - timezone.timedelta(days=1)).replace(day=1)
                
                m_start = current_m
                if current_m.month == 12:
                    m_end = current_m.replace(year=current_m.year + 1, month=1, day=1) - timezone.timedelta(seconds=1)
                else:
                    m_end = current_m.replace(month=current_m.month + 1, day=1) - timezone.timedelta(seconds=1)
                
                m_revenue = Invoice.objects.filter(
                    issue_date__range=(m_start, m_end)
                ).exclude(status__in=['REJECTED', 'CANCELLED']).aggregate(total=Sum('total_amount'))['total'] or 0
                
                monthly_data.append(float(m_revenue))
                month_labels.append(m_start.strftime('%b'))

            # Avg Deal Size
            invoice_count = Invoice.objects.exclude(status__in=['REJECTED', 'CANCELLED']).count()
            revenue_stats['avg_deal_size'] = 0
            if invoice_count > 0:
                revenue_stats['avg_deal_size'] = round(revenue_stats['total_revenue'] / invoice_count, 2)

            revenue_stats['chart_data'] = monthly_data
            revenue_stats['chart_labels'] = month_labels
            context['revenue_stats'] = revenue_stats

            # 8. Lead Performance Metrics (for leadsGraph.html)
            total_leads = stats['total_customers'] + stats['active_leads'] + Lead.objects.filter(status='lost').count()
            conversion_rate = 0
            if total_leads > 0:
                conversion_rate = (stats['total_customers'] / total_leads) * 100
            
            # Percentages for progress bars
            def get_perc(count):
                return (count / total_leads * 100) if total_leads > 0 else 0

            context['lead_performance'] = {
                'total': total_leads,
                'new': Lead.objects.filter(status='new').count(),
                'converted': stats['total_customers'],
                'pending': stats['active_leads'],
                'conversion_rate': round(conversion_rate, 1),
                'new_perc': get_perc(Lead.objects.filter(status='new').count()),
                'won_perc': get_perc(stats['total_customers']),
                'active_perc': get_perc(stats['active_leads']),
                'lost_perc': get_perc(Lead.objects.filter(status='lost').count()),
            }

            # 8. Lead Distribution (for charts)
            lead_dist = Lead.objects.values('status').annotate(count=Count('id'))
            context['lead_distribution'] = {item['status']: item['count'] for item in lead_dist}

        except Exception as e:
            logger.error(f"Dashboard data retrieval error: {str(e)}")
            context['error'] = "Some dashboard data could not be loaded. Please try again later."
            # Provide empty defaults to avoid template errors
            context['stats'] = {}
            context['top_deals'] = []
            context['delayed_leads'] = []
            context['recent_activities'] = []
            context['system_logs'] = []
            context['top_customers'] = []
            context['lead_distribution'] = {}

        return context



class LogoutView(View):
    @method_decorator(never_cache)
    def get(self, request):
        if request.user.is_authenticated:
            logout(request)
            messages.success(request, "You have been logged out successfully.")
        return redirect('accounts:signin')