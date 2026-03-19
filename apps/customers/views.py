from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.db.models import Q
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
import logging
from .models import Customer
from .forms import CustomerForm

logger = logging.getLogger(__name__)

class CustomerListView(LoginRequiredMixin, ListView):
    model = Customer
    template_name = 'customers/list.html'
    context_object_name = 'customers'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Searching
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(customer_code__icontains=search_query) |
                Q(company_name__icontains=search_query)
            )

        # Filtering
        customer_type = self.request.GET.get('type', '').strip()
        if customer_type:
            queryset = queryset.filter(customer_type=customer_type)

        status_filter = self.request.GET.get('status', '').strip()
        if status_filter:
            is_active = status_filter == 'active'
            queryset = queryset.filter(is_active=is_active)

        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at').strip()
        allowed_sort_fields = [
            'name', '-name',
            'customer_code', '-customer_code',
            'created_at', '-created_at',
            'customer_type', '-customer_type'
        ]
        if sort_by in allowed_sort_fields:
            queryset = queryset.order_by(sort_by)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'search_query': self.request.GET.get('search', ''),
            'type_filter': self.request.GET.get('type', ''),
            'status_filter': self.request.GET.get('status', ''),
            'sort_by': self.request.GET.get('sort', '-created_at'),
            'customer_types': Customer.CUSTOMER_TYPE,
            'is_paginated': context.get('is_paginated', False),
        })
        return context

class CustomerCreateView(LoginRequiredMixin,SuccessMessageMixin, CreateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/create.html'
    success_url = reverse_lazy('customers:list')
    success_message = "Customer created successfully!"

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                logger.info(f"Customer {self.object.customer_code} created successfully.")
                return response
        except Exception as e:
            logger.error(f"Error creating customer: {str(e)}")
            messages.error(self.request, "An unexpected error occurred while creating the customer. Please try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid data submitted. Please check the form errors below.")
        return super().form_invalid(form)

class CustomerUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Customer
    form_class = CustomerForm
    template_name = 'customers/update.html'
    success_url = reverse_lazy('customers:list')
    success_message = "Customer updated successfully!"

    def form_valid(self, form):
        try:
            with transaction.atomic():
                response = super().form_valid(form)
                logger.info(f"Customer {self.object.customer_code} updated successfully.")
                return response
        except Exception as e:
            logger.error(f"Error updating customer {self.kwargs.get('pk')}: {str(e)}")
            messages.error(self.request, "An unexpected error occurred while updating the customer. Please try again.")
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Invalid data submitted. Please check the form errors below.")
        return super().form_invalid(form)

class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    model = Customer
    success_url = reverse_lazy('customers:list')

    def delete(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                self.object = self.get_object()
                customer_name = self.object.name
                self.object.delete() # Soft delete
                logger.warning(f"Customer {customer_name} deleted successfully.")
                messages.warning(request, f"Customer '{customer_name}' has been successfully deleted (soft-deleted).")
                return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            logger.error(f"Error deleting customer {self.kwargs.get('pk')}: {str(e)}")
            messages.error(request, "An error occurred while trying to delete the customer.")
            return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
