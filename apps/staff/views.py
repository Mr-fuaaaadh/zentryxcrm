from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, TemplateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.contrib.auth import get_user_model
from .models import Staff
from .forms import StaffForm, StaffUpdateForm
from apps.core.models import Department, Designation

User = get_user_model()

class StaffListView(LoginRequiredMixin, ListView):
    """
    Optimized and secure staff list view.
    """
    model = Staff
    template_name = 'staff/list.html'
    context_object_name = 'staff_list'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'department', 'designation')
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(employee_id__icontains=search_query)
            )

        status_filter = self.request.GET.get('status', '').strip()
        if status_filter:
            queryset = queryset.filter(employment_status=status_filter)

        department_filter = self.request.GET.get('department', '').strip()
        if department_filter:
            queryset = queryset.filter(department_id=department_filter)

        sort_by = self.request.GET.get('sort', '-created_at').strip()
        allowed_sort_fields = [
            'employee_id', '-employee_id', 
            'user__first_name', '-user__first_name',
            'joining_date', '-joining_date',
            'employment_status', '-employment_status',
            'created_at', '-created_at'
        ]
        if sort_by in allowed_sort_fields:
            queryset = queryset.order_by(sort_by)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.utils import timezone
        
        # Dashboard stats
        context['total_staff'] = Staff.objects.count()
        context['active_staff'] = Staff.objects.filter(employment_status='ACTIVE').count()
        context['on_leave_staff'] = Staff.objects.filter(employment_status='ON_LEAVE').count()
        
        # New joinees (this month)
        now = timezone.now()
        context['new_joinees'] = Staff.objects.filter(
            joining_date__month=now.month,
            joining_date__year=now.year
        ).count()

        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['department_filter'] = self.request.GET.get('department', '')
        context['sort_by'] = self.request.GET.get('sort', '-created_at')
        context['status_choices'] = Staff.EMPLOYMENT_STATUS
        context['departments'] = Department.objects.filter(is_active=True)
        return context

class StaffAdd(LoginRequiredMixin, TemplateView):
    template_name = "staff/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'form' not in context:
            context['form'] = StaffForm()
        return context

    def post(self, request, *args, **kwargs):
        form = StaffForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Create User
                    user = User.objects.create_user(
                        email=form.cleaned_data['email'],
                        username=form.cleaned_data['email'].split('@')[0],
                        first_name=form.cleaned_data['first_name'],
                        last_name=form.cleaned_data['last_name'],
                        password=form.cleaned_data['password'],
                        role='STAFF'
                    )
                    
                    if form.cleaned_data.get('profile_image'):
                        user.profile_image = form.cleaned_data['profile_image']
                        user.save()

                    # Save Staff Profile
                    staff = form.save(commit=False)
                    staff.user = user
                    staff.save()
                    
                messages.success(request, f"Staff profile created successfully for {user.get_full_name()}.")
                return redirect('staff:list')
            except Exception as e:
                messages.error(request, f"Error creating staff: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.capitalize()}: {error}")
        
        return self.render_to_response(self.get_context_data(form=form))

class StaffUpdateView(LoginRequiredMixin, UpdateView):
    model = Staff
    form_class = StaffUpdateForm
    template_name = "staff/update.html"
    success_url = reverse_lazy('staff:list')

    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Update associated User fields
                user = self.object.user
                user.first_name = form.cleaned_data['first_name']
                user.last_name = form.cleaned_data['last_name']
                if form.cleaned_data.get('profile_image'):
                    user.profile_image = form.cleaned_data['profile_image']
                user.save()
                
                # Save Staff fields
                response = super().form_valid(form)
                messages.success(self.request, f"Staff profile for {user.get_full_name()} updated successfully.")
                return response
        except Exception as e:
            messages.error(self.request, f"Error updating staff: {str(e)}")
            return self.form_invalid(form)

    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f"{field.capitalize()}: {error}")
        return super().form_invalid(form)

class StaffDeleteView(LoginRequiredMixin, DeleteView):
    model = Staff
    template_name = "staff/delete_confirm.html"
    success_url = reverse_lazy('staff:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        user = self.object.user
        try:
            with transaction.atomic():
                # Important: CASCADE delete will handle Staff if we delete User, 
                # but here we follow request to delete Staff and its User account.
                name = user.get_full_name()
                user.delete() 
                messages.success(request, f"Staff record for {name} has been deleted.")
                return redirect(self.get_success_url())
        except Exception as e:
            messages.error(request, f"Error deleting staff: {str(e)}")
            return redirect('staff:list')
