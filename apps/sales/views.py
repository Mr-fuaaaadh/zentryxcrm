from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db import transaction
from django.db.models import Q, Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.utils import timezone

from .models import Proposal, Product, Estimate, StaffMonthlyTarget, StaffPerformance
from apps.staff.models import Staff
from .forms import ProposalForm, ProposalItemFormSet, EstimateForm, EstimateItemFormSet, StaffMonthlyTargetForm
import logging
import json

logger = logging.getLogger(__name__)

class ProposalListView(LoginRequiredMixin, ListView):
    model = Proposal
    template_name = 'sales/proposal-list.html'
    context_object_name = 'proposals'
    paginate_by = 10

    def get_queryset(self):
        try:
            queryset = Proposal.objects.all().select_related('customer', 'created_by')

            # Search
            search = self.request.GET.get('search')
            if search:
                queryset = queryset.filter(
                    Q(document_number__icontains=search) |
                    Q(customer__name__icontains=search) |
                    Q(customer__company_name__icontains=search) |
                    Q(notes__icontains=search)
                )

            # Filters
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status)

            # Sorting
            sort = self.request.GET.get('sort', '-issue_date')
            allowed_sort = ['issue_date', '-issue_date', 'total_amount', '-total_amount', 'status', '-status']
            if sort in allowed_sort:
                queryset = queryset.order_by(sort)
            else:
                queryset = queryset.order_by('-issue_date')

            return queryset
        except Exception as e:
            logger.error(f"Error in ProposalListView queryset: {str(e)}")
            return Proposal.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Proposal.STATUS_CHOICES

        proposals = Proposal.objects.all()
        context['total_proposals'] = proposals.count()
        context['sent_proposals'] = proposals.filter(status='SENT').count()
        context['approved_proposals'] = proposals.filter(status='APPROVED').count()
        context['declined_proposals'] = proposals.filter(status='REJECTED').count()
        context['total_revenue'] = (
            proposals.filter(status='APPROVED')
            .aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        )

        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '-issue_date')

        return context

class ProposalCreateView(LoginRequiredMixin, CreateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'sales/proposal-add.html'
    success_url = reverse_lazy('sales:proposal_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = ProposalItemFormSet(self.request.POST)
        else:
            data['items'] = ProposalItemFormSet()
        
        products = Product.objects.filter(proposal__isnull=True, estimate__isnull=True, invoice__isnull=True).prefetch_related('price_tiers')
        product_list = []
        for p in products:
            prices = {pt.price_level_id: str(pt.price) for pt in p.price_tiers.all()}
            product_list.append({
                'id': p.id, 
                'name': p.name, 
                'description': p.description, 
                'unit_price': str(p.unit_price), 
                'tax_percent': str(p.tax_percent),
                'tiered_prices': prices
            })
        
        data['product_data_json'] = json.dumps(product_list)
        from .models import PriceLevel
        data['price_levels'] = PriceLevel.objects.filter(is_active=True)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            form.instance.created_by = self.request.user
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
            else:
                return self.form_invalid(form)
        messages.success(self.request, "Proposal created successfully!")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error saving the proposal. Please check the fields below.")
        return super().form_invalid(form)

class ProposalUpdateView(LoginRequiredMixin, UpdateView):
    model = Proposal
    form_class = ProposalForm
    template_name = 'sales/proposal-add.html'
    success_url = reverse_lazy('sales:proposal_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = ProposalItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = ProposalItemFormSet(instance=self.object)
        
        products = Product.objects.filter(proposal__isnull=True, estimate__isnull=True, invoice__isnull=True).prefetch_related('price_tiers')
        product_list = []
        for p in products:
            prices = {pt.price_level_id: str(pt.price) for pt in p.price_tiers.all()}
            product_list.append({
                'id': p.id, 
                'name': p.name, 
                'description': p.description, 
                'unit_price': str(p.unit_price), 
                'tax_percent': str(p.tax_percent),
                'tiered_prices': prices
            })
        
        data['product_data_json'] = json.dumps(product_list)
        from .models import PriceLevel
        data['price_levels'] = PriceLevel.objects.filter(is_active=True)
        data['is_update'] = True
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        with transaction.atomic():
            self.object = form.save()
            if items.is_valid():
                items.instance = self.object
                items.save()
            else:
                return self.form_invalid(form)
        messages.success(self.request, "Proposal updated successfully!")
        return redirect(self.success_url)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the proposal. Please check the fields below.")
        return super().form_invalid(form)


class ProposalDeleteView(LoginRequiredMixin, DeleteView):
    model = Proposal
    success_url = reverse_lazy('sales:proposal_list')
    
    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            messages.success(request, "Proposal deleted successfully!")
            return response
        except Exception as e:
            messages.error(request, f"Error deleting proposal: {str(e)}")
            return redirect(self.success_url)


class EstimateListView(LoginRequiredMixin, ListView):
    model = Estimate
    template_name = 'sales/estimate-list.html'
    context_object_name = 'estimates'
    paginate_by = 10

    def get_queryset(self):
        try:
            queryset = Estimate.objects.all().select_related('customer', 'created_by')

            # Search
            search = self.request.GET.get('search')
            if search:
                queryset = queryset.filter(
                    Q(document_number__icontains=search) |
                    Q(customer__name__icontains=search) |
                    Q(customer__company_name__icontains=search) |
                    Q(notes__icontains=search)
                )

            # Filters
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status)

            # Sorting
            sort = self.request.GET.get('sort', '-issue_date')
            allowed_sort = ['document_number', '-document_number', 'issue_date', '-issue_date', 'total_amount', '-total_amount', 'status', '-status']
            if sort in allowed_sort:
                queryset = queryset.order_by(sort)
            else:
                queryset = queryset.order_by('-issue_date')

            return queryset
        except Exception as e:
            logger.error(f"Error in EstimateListView queryset: {str(e)}")
            return Estimate.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Estimate.STATUS_CHOICES

        estimates = Estimate.objects.all()
        context['total_estimates'] = estimates.count()
        context['sent_estimates'] = estimates.filter(status='SENT').count()
        context['approved_estimates'] = estimates.filter(status='APPROVED').count()
        context['declined_estimates'] = estimates.filter(status='REJECTED').count()
        context['total_revenue'] = (
            estimates.filter(status='APPROVED')
            .aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        )

        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '-issue_date')

        return context


class EstimateCreateView(LoginRequiredMixin, CreateView):
    model = Estimate
    form_class = EstimateForm
    template_name = 'sales/estimate-add.html'
    success_url = reverse_lazy('sales:estimate_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = EstimateItemFormSet(self.request.POST)
        else:
            data['items'] = EstimateItemFormSet()
        
        products = Product.objects.filter(proposal__isnull=True, estimate__isnull=True, invoice__isnull=True).prefetch_related('price_tiers')
        product_list = []
        for p in products:
            prices = {pt.price_level_id: str(pt.price) for pt in p.price_tiers.all()}
            product_list.append({
                'id': p.id, 
                'name': p.name, 
                'description': p.description, 
                'unit_price': str(p.unit_price), 
                'tax_percent': str(p.tax_percent),
                'tiered_prices': prices
            })
        
        data['product_data_json'] = json.dumps(product_list)
        from .models import PriceLevel
        data['price_levels'] = PriceLevel.objects.filter(is_active=True)
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        try:
            with transaction.atomic():
                form.instance.created_by = self.request.user
                self.object = form.save()
                if items.is_valid():
                    items.instance = self.object
                    items.save()
                else:
                    return self.form_invalid(form)
            messages.success(self.request, "Estimate created successfully!")
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error creating estimate: {str(e)}")
            messages.error(self.request, f"An unexpected error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error saving the estimate. Please check the fields below.")
        return super().form_invalid(form)

class EstimateUpdateView(LoginRequiredMixin, UpdateView):
    model = Estimate
    form_class = EstimateForm
    template_name = 'sales/estimate-add.html'
    success_url = reverse_lazy('sales:estimate_list')

    def get_context_data(self, **kwargs):
        data = super().get_context_data(**kwargs)
        if self.request.POST:
            data['items'] = EstimateItemFormSet(self.request.POST, instance=self.object)
        else:
            data['items'] = EstimateItemFormSet(instance=self.object)
        
        products = Product.objects.filter(proposal__isnull=True, estimate__isnull=True, invoice__isnull=True).prefetch_related('price_tiers')
        product_list = []
        for p in products:
            prices = {pt.price_level_id: str(pt.price) for pt in p.price_tiers.all()}
            product_list.append({
                'id': p.id, 
                'name': p.name, 
                'description': p.description, 
                'unit_price': str(p.unit_price), 
                'tax_percent': str(p.tax_percent),
                'tiered_prices': prices
            })
        
        data['product_data_json'] = json.dumps(product_list)
        from .models import PriceLevel
        data['price_levels'] = PriceLevel.objects.filter(is_active=True)
        data['is_update'] = True
        return data

    def form_valid(self, form):
        context = self.get_context_data()
        items = context['items']
        try:
            with transaction.atomic():
                self.object = form.save()
                if items.is_valid():
                    items.instance = self.object
                    items.save()
                else:
                    return self.form_invalid(form)
            messages.success(self.request, "Estimate updated successfully!")
            return redirect(self.success_url)
        except Exception as e:
            logger.error(f"Error updating estimate: {str(e)}")
            messages.error(self.request, f"An unexpected error occurred: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error updating the estimate. Please check the fields below.")
        return super().form_invalid(form)


class EstimateDeleteView(LoginRequiredMixin, DeleteView):
    model = Estimate
    success_url = reverse_lazy('sales:estimate_list')
    
    def get(self, request, *args, **kwargs):
        return redirect(self.success_url)

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            messages.success(request, "Estimate deleted successfully!")
            return response
        except Exception as e:
            messages.error(request, f"Error deleting estimate: {str(e)}")
            return redirect(self.success_url)



# --- Staff Monthly Target Views ---

class StaffMonthlyTargetListView(LoginRequiredMixin, ListView):
    model = StaffMonthlyTarget
    template_name = 'sales/staff-target-list.html'
    context_object_name = 'targets'
    paginate_by = 10

    def get_queryset(self):
        queryset = StaffMonthlyTarget.objects.all().select_related('staff', 'staff__user')
        
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(staff__user__first_name__icontains=search) |
                Q(staff__user__last_name__icontains=search) |
                Q(staff__user__username__icontains=search)
            )
            
        month = self.request.GET.get('month')
        if month:
            queryset = queryset.filter(month=month)
            
        year = self.request.GET.get('year')
        if year:
            queryset = queryset.filter(year=year)
            
        return queryset.order_by('-year', '-month', 'staff__user__username')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['months'] = range(1, 13)
        context['current_month'] = self.request.GET.get('month', '')
        context['current_year'] = self.request.GET.get('year', '')
        context['current_search'] = self.request.GET.get('search', '')
        return context


class StaffMonthlyTargetCreateView(LoginRequiredMixin, CreateView):
    model = StaffMonthlyTarget
    form_class = StaffMonthlyTargetForm
    template_name = 'sales/staff-target-add.html'
    success_url = reverse_lazy('sales:staff_target_list')

    def form_valid(self, form):
        messages.success(self.request, "Monthly target set successfully!")
        return super().form_valid(form)


class StaffMonthlyTargetUpdateView(LoginRequiredMixin, UpdateView):
    model = StaffMonthlyTarget
    form_class = StaffMonthlyTargetForm
    template_name = 'sales/staff-target-add.html'
    success_url = reverse_lazy('sales:staff_target_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, "Monthly target updated successfully!")
        return super().form_valid(form)


class StaffMonthlyTargetDeleteView(LoginRequiredMixin, DeleteView):
    model = StaffMonthlyTarget
    success_url = reverse_lazy('sales:staff_target_list')

    def post(self, request, *args, **kwargs):
        try:
            response = super().post(request, *args, **kwargs)
            messages.success(request, "Monthly target deleted successfully!")
            return response
        except Exception as e:
            messages.error(request, f"Error deleting target: {str(e)}")
            return redirect(self.success_url)

class StaffPerformanceDashboardView(LoginRequiredMixin, ListView):
    template_name = 'sales/staff-performance.html'
    context_object_name = 'performances'

    def get_queryset(self):
        month = int(self.request.GET.get('month', timezone.now().month))
        year = int(self.request.GET.get('year', timezone.now().year))

        # Iterate over active Staff members (consistent with Lead.assigned_to)
        staff_list = Staff.objects.filter(is_active=True).select_related('user')

        performance_data = []
        for staff in staff_list:
            # Get target for this staff/month/year
            target = StaffMonthlyTarget.objects.filter(
                staff=staff, month=month, year=year
            ).first()

            # Aggregate performance for this staff/month/year
            actuals = StaffPerformance.objects.filter(
                staff=staff,
                date__month=month,
                date__year=year
            ).aggregate(
                leads=Sum('leads_generated'),
                calls=Sum('calls_made'),
                meetings=Sum('meetings_booked'),
                proposals=Sum('proposals_sent'),
                deals=Sum('deals_closed'),
                revenue=Sum('revenue_generated')
            )

            def calc_pct(actual, target_val):
                if not target_val or target_val == 0:
                    return 100 if (actual or 0) > 0 else 0
                return min(int(((actual or 0) / target_val) * 100), 100)

            # Conversion Rate Intelligence
            leads_actual = actuals['leads'] or 0
            deals_actual = actuals['deals'] or 0
            conv_rate = round((deals_actual / leads_actual * 100), 1) if leads_actual > 0 else 0

            stats = {
                'staff': staff,
                'target': target,
                'actuals': actuals,
                'conversion_rate': conv_rate,
                'leads_pct': calc_pct(actuals['leads'], target.leads_target if target else 0),
                'calls_pct': calc_pct(actuals['calls'], target.calls_target if target else 0),
                'meetings_pct': calc_pct(actuals['meetings'], target.meetings_target if target else 0),
                'proposals_pct': calc_pct(actuals['proposals'], target.proposals_target if target else 0),
                'deals_pct': calc_pct(actuals['deals'], target.deals_target if target else 0),
                'revenue_pct': calc_pct(actuals['revenue'], target.revenue_target if target else 0),
            }
            # Efficiency Index: Weighted average (Revenue 40%, Deals 30%, Leads 20%, Calls 10%)
            eff_index = (stats['revenue_pct'] * 0.4) + (stats['deals_pct'] * 0.3) + (stats['leads_pct'] * 0.2) + (stats['calls_pct'] * 0.1)
            stats['efficiency_index'] = round(eff_index)
            
            performance_data.append(stats)

        # Sort by efficiency to rank performers
        performance_data = sorted(performance_data, key=lambda x: x['efficiency_index'], reverse=True)
        return performance_data

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['months'] = range(1, 13)
        context['current_month'] = int(self.request.GET.get('month', timezone.now().month))
        context['current_year'] = int(self.request.GET.get('year', timezone.now().year))

        queryset = self.get_queryset()
        context['total_leads'] = sum(p['actuals']['leads'] or 0 for p in queryset)
        context['total_deals'] = sum(p['actuals']['deals'] or 0 for p in queryset)
        context['total_revenue'] = sum(p['actuals']['revenue'] or 0 for p in queryset)

        # Prepare chart data
        chart_labels = []
        leads_target_data = []
        leads_actual_data = []
        total_pct = 0
        count = 0
        for p in queryset:
            # Staff objects now, so use .user.get_full_name()
            chart_labels.append(p['staff'].user.get_full_name() or p['staff'].user.username)
            leads_target_data.append(p['target'].leads_target if p['target'] else 0)
            leads_actual_data.append(p['actuals']['leads'] or 0)
            total_pct += p['revenue_pct'] + p['leads_pct'] + p['calls_pct'] + p['deals_pct']
            count += 4

        context['chart_data_json'] = json.dumps({
            'labels': chart_labels,
            'leads_target': leads_target_data,
            'leads_actual': leads_actual_data,
        })
        context['team_efficiency'] = round(total_pct / (count or 1))
        
        # Elite Performers (Top 3)
        context['elite_performers'] = queryset[:3]
        
        # Aggregate Targets vs Actuals for Pulse Head
        context['agg_actual_revenue'] = context['total_revenue']
        context['agg_target_revenue'] = sum(p['target'].revenue_target if p['target'] else 0 for p in queryset)
        context['rev_achievement_pct'] = round((context['agg_actual_revenue'] / context['agg_target_revenue'] * 100), 1) if context['agg_target_revenue'] > 0 else 0

        return context
