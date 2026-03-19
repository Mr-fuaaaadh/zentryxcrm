from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone

from .models import Project, ProjectActivity
from .forms import ProjectForm


class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = "projects/list.html"
    context_object_name = "projects"
    paginate_by = 10

    def get_queryset(self):
        queryset = Project.objects.filter(is_deleted=False).select_related('customer', 'lead', 'manager').prefetch_related('team_members')
        
        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(project_code__icontains=search)
            )

        # Filters
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)

        # Sorting
        sort = self.request.GET.get('sort', '-created_at')
        valid_sort_fields = ['created_at', '-created_at', 'name', '-name', 'budget', '-budget', 'start_date', '-start_date']
        if sort in valid_sort_fields:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add activities for the timeline (recent 20)
        context['activities'] = ProjectActivity.objects.all().select_related('project', 'created_by')[:20]
        
        # Add filter options
        context['status_choices'] = Project.STATUS_CHOICES
        context['priority_choices'] = Project.PRIORITY_CHOICES
        
        # Stats for cards
        all_projects = Project.objects.filter(is_deleted=False)
        today = timezone.now().date()
        
        total_budget = sum(p.budget for p in all_projects if p.budget) or 0
        total_actual = sum(p.actual_cost for p in all_projects if p.actual_cost) or 0
        
        context['stats'] = {
            'total': all_projects.count(),
            'in_progress': all_projects.filter(status='in_progress').count(),
            'completed': all_projects.filter(status='completed').count(),
            'overdue': all_projects.filter(status__in=['planning', 'in_progress', 'on_hold'], end_date__lt=today).count(),
            'total_budget': total_budget,
            'budget_utilization': round((total_actual / total_budget * 100), 1) if total_budget > 0 else 0
        }
        return context


class ProjectCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/create.html"
    success_url = reverse_lazy('projects:list')
    success_message = "Project '%(name)s' was created successfully!"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Failed to create project. Please check the errors below.")
        return super().form_invalid(form)


class ProjectUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "projects/update.html"
    success_url = reverse_lazy('projects:list')
    success_message = "Project '%(name)s' was updated successfully!"

    def form_invalid(self, form):
        messages.error(self.request, "Failed to update project. Please check the errors below.")
        return super().form_invalid(form)


class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        self.object.is_deleted = True
        self.object.save()
        messages.success(request, f"Project '{self.object.name}' was deleted successfully.")
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"status": "success", "message": "Project deleted successfully."})
        return redirect(success_url)

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
