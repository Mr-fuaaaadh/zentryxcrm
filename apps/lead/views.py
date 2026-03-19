from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from django.contrib import messages
from django.http import JsonResponse, HttpResponseRedirect
from apps.staff.models import Staff

from .models import Lead, LeadActivity
from .forms import LeadForm, LeadActivityForm


class LeadListView(LoginRequiredMixin, ListView):
    model = Lead
    template_name = 'lead/list.html'
    context_object_name = 'leads'
    paginate_by = 10

    def get_queryset(self):
        # Base queryset optimized with select_related
        queryset = Lead.objects.all().select_related('assigned_to', 'assigned_to__user', 'created_by')

        # Staff see only assigned or created leads; Admin/superuser see all
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            try:
                staff = Staff.objects.get(user=self.request.user)
                queryset = queryset.filter(
                    Q(assigned_to=staff) | Q(created_by=self.request.user)
                )
            except Staff.DoesNotExist:
                queryset = queryset.filter(created_by=self.request.user)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(phone__icontains=search) |
                Q(company_name__icontains=search)
            )

        # Filters
        status_filter = self.request.GET.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        source_filter = self.request.GET.get('source')
        if source_filter:
            queryset = queryset.filter(source=source_filter)

        priority_filter = self.request.GET.get('priority')
        if priority_filter:
            queryset = queryset.filter(priority=priority_filter)

        # Filter by Staff ID (assigned_to is FK to Staff)
        assignee_filter = self.request.GET.get('assigned_to')
        if assignee_filter:
            queryset = queryset.filter(assigned_to_id=assignee_filter)

        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        return queryset.order_by(sort)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Current filter state for template
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_priority'] = self.request.GET.get('priority', '')
        context['current_assigned_to'] = self.request.GET.get('assigned_to', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')

        context['status_choices'] = Lead.STATUS_CHOICES
        context['source_choices'] = Lead.SOURCE_CHOICES
        context['priority_choices'] = Lead.PRIORITY_CHOICES
        # Use Staff objects for the assignee dropdown (consistent with Lead.assigned_to)
        context['staff_members'] = Staff.objects.filter(
            is_active=True
        ).select_related('user').order_by('user__first_name')

        # Optimized base queryset for stats
        stats_qs = Lead.objects.all()
        if not self.request.user.is_superuser and not self.request.user.is_staff:
            try:
                staff = Staff.objects.get(user=self.request.user)
                stats_qs = stats_qs.filter(
                    Q(assigned_to=staff) | Q(created_by=self.request.user)
                )
            except Staff.DoesNotExist:
                stats_qs = stats_qs.filter(created_by=self.request.user)

        # Summary Stats for Dashboard component in List View
        context['total_leads'] = stats_qs.count()
        context['new_leads'] = stats_qs.filter(status='new').count()
        context['contacted_leads'] = stats_qs.filter(status='contacted').count()
        context['won_leads'] = stats_qs.filter(status='won').count()
        context['lost_leads'] = stats_qs.filter(status='lost').count()
        
        # Calculate Conversion Rate
        total = context['total_leads']
        won = context['won_leads']
        context['conversion_rate'] = round((won / total * 100), 1) if total > 0 else 0
        
        context['total_revenue'] = stats_qs.aggregate(
            Sum('expected_revenue')
        )['expected_revenue__sum'] or 0

        # Recent activities related to leads this user can see
        if self.request.user.is_superuser or self.request.user.is_staff:
            context['recent_activities'] = LeadActivity.objects.all().select_related(
                'lead', 'created_by', 'created_by__user'
            )[:10]
        else:
            try:
                staff = Staff.objects.get(user=self.request.user)
                context['recent_activities'] = LeadActivity.objects.filter(
                    Q(lead__assigned_to=staff) | Q(lead__created_by=self.request.user)
                ).select_related('lead', 'created_by', 'created_by__user')[:10]
            except Staff.DoesNotExist:
                context['recent_activities'] = LeadActivity.objects.filter(
                    lead__created_by=self.request.user
                ).select_related('lead', 'created_by', 'created_by__user')[:10]

        return context


class LeadDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Lead
    template_name = 'lead/detail.html'
    context_object_name = 'lead'

    def test_func(self):
        lead = self.get_object()
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        try:
            staff = Staff.objects.get(user=user)
            return lead.assigned_to == staff or lead.created_by == user
        except Staff.DoesNotExist:
            return lead.created_by == user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['activities'] = self.object.activities.all().select_related(
            'created_by', 'created_by__user'
        )
        context['activity_form'] = LeadActivityForm()
        return context


class LeadCreateView(LoginRequiredMixin, CreateView):
    model = Lead
    form_class = LeadForm
    template_name = 'lead/create.html'
    success_url = reverse_lazy('leads:list')

    def form_valid(self, form):
        try:
            form.instance.created_by = self.request.user
            response = super().form_valid(form)
            messages.success(self.request, "Lead created successfully!")
            return response
        except Exception as e:
            messages.error(self.request, f"Error creating lead: {str(e)}")
            return self.form_invalid(form)


class LeadUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Lead
    form_class = LeadForm
    template_name = 'lead/create.html'

    def test_func(self):
        lead = self.get_object()
        user = self.request.user
        if user.is_superuser or user.is_staff:
            return True
        try:
            staff = Staff.objects.get(user=user)
            return lead.assigned_to == staff
        except Staff.DoesNotExist:
            return False

    def get_success_url(self):
        return reverse_lazy('leads:detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "Lead updated successfully!")
            return response
        except Exception as e:
            messages.error(self.request, f"Error updating lead: {str(e)}")
            return self.form_invalid(form)


class LeadDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Lead
    success_url = reverse_lazy('leads:list')

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.is_deleted = True
            self.object.save()
            messages.warning(request, "Lead soft-deleted successfully.")
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(request, f"Error deleting lead: {str(e)}")
            return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)


class AddActivityView(LoginRequiredMixin, View):
    def post(self, request, pk):
        lead = get_object_or_404(Lead, pk=pk)

        # The logged-in user must have a Staff profile to log activities
        try:
            staff = Staff.objects.get(user=request.user)
        except Staff.DoesNotExist:
            messages.error(request, "Only staff members can log activities.")
            return redirect('leads:detail', pk=pk)

        form = LeadActivityForm(request.POST)
        if form.is_valid():
            activity = form.save(commit=False)
            activity.lead = lead
            activity.created_by = staff  # Staff object — signals will use this
            activity.save()
            messages.success(request, "Activity logged successfully.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

        return redirect('leads:detail', pk=pk)
