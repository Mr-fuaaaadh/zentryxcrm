from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render
from .models import Department, Designation
from .forms import DepartmentForm, DesignationForm





# --- Department Views ---

class DepartmentListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Department
    template_name = 'core/department_list.html'
    context_object_name = 'departments'
    permission_required = 'core.view_department'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                models.Q(name__icontains=q) | models.Q(code__icontains=q)
            )
        
        # Filter by status
        status = self.request.GET.get('status')
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        # Sorting
        sort = self.request.GET.get('sort', 'name')
        direction = self.request.GET.get('direction', 'asc')
        if direction == 'desc':
            sort = f'-{sort}'
        
        # Validate sort field to prevent errors
        valid_sort_fields = ['name', 'code', 'created_at', 'is_active']
        if sort.lstrip('-') in valid_sort_fields:
            queryset = queryset.order_by(sort)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_q'] = self.request.GET.get('q', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', 'name')
        context['current_direction'] = self.request.GET.get('direction', 'asc')
        return context


class DepartmentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'core/department_form.html'
    success_url = reverse_lazy('core:department-list')
    permission_required = 'core.add_department'

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Department '{form.instance.name}' created successfully.",
                'redirect_url': self.success_url
            })
        messages.success(self.request, f"Department '{form.instance.name}' created successfully.")
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, self.template_name, {'form': form}, status=400)
        return response


class DepartmentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'core/department_form.html'
    success_url = reverse_lazy('core:department-list')
    permission_required = 'core.change_department'

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Department '{form.instance.name}' updated successfully.",
                'redirect_url': self.success_url
            })
        messages.success(self.request, f"Department '{form.instance.name}' updated successfully.")
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, self.template_name, {'form': form}, status=400)
        return response


class DepartmentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Department
    template_name = 'core/department_confirm_delete.html'
    success_url = reverse_lazy('core:department-list')
    permission_required = 'core.delete_department'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        name = obj.name
        response = super().delete(request, *args, **kwargs)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Department '{name}' deleted successfully.",
                'redirect_url': self.success_url
            })
        messages.success(self.request, f"Department '{name}' deleted successfully.")
        return response


# --- Designation Views ---

class DesignationListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Designation
    template_name = 'core/designation_list.html'
    context_object_name = 'designations'
    permission_required = 'core.view_designation'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Search
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(title__icontains=q)
        
        # Filter by level
        level = self.request.GET.get('level')
        if level:
            queryset = queryset.filter(level=level)
        
        # Sorting
        sort = self.request.GET.get('sort', 'level')
        direction = self.request.GET.get('direction', 'asc')
        if direction == 'desc':
            sort = f'-{sort}'
        
        # Validate sort field
        valid_sort_fields = ['title', 'level', 'created_at']
        if sort.lstrip('-') in valid_sort_fields:
            queryset = queryset.order_by(sort)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_q'] = self.request.GET.get('q', '')
        context['current_level'] = self.request.GET.get('level', '')
        context['current_sort'] = self.request.GET.get('sort', 'level')
        context['current_direction'] = self.request.GET.get('direction', 'asc')
        # Get unique levels for filter dropdown
        context['levels'] = Designation.objects.values_list('level', flat=True).distinct().order_by('level')
        return context


class DesignationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Designation
    form_class = DesignationForm
    template_name = 'core/designation_form.html'
    success_url = reverse_lazy('core:designation-list')
    permission_required = 'core.add_designation'

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Designation '{form.instance.title}' created successfully.",
                'redirect_url': self.success_url
            })
        messages.success(self.request, f"Designation '{form.instance.title}' created successfully.")
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, self.template_name, {'form': form}, status=400)
        return response


class DesignationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Designation
    form_class = DesignationForm
    template_name = 'core/designation_form.html'
    success_url = reverse_lazy('core:designation-list')
    permission_required = 'core.change_designation'

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Designation '{form.instance.title}' updated successfully.",
                'redirect_url': self.success_url
            })
        messages.success(self.request, f"Designation '{form.instance.title}' updated successfully.")
        return response

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return render(self.request, self.template_name, {'form': form}, status=400)
        return response


class DesignationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Designation
    template_name = 'core/designation_confirm_delete.html'
    success_url = reverse_lazy('core:designation-list')
    permission_required = 'core.delete_designation'

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        title = obj.title
        response = super().delete(request, *args, **kwargs)
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': f"Designation '{title}' deleted successfully.",
                'redirect_url': self.success_url
            })
        messages.success(self.request, f"Designation '{title}' deleted successfully.")
        return response

