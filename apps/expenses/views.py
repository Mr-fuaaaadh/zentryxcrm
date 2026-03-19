from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from decimal import Decimal
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.views import View
from django.http import HttpResponse
from .models import Expense, ExpensePayment, ExpenseActivityLog, ExpenseAttachment
import csv
from .forms import ExpenseForm, ExpensePaymentForm, ExpenseAttachmentForm
import logging

logger = logging.getLogger(__name__)

class ExpenseListView(LoginRequiredMixin, ListView):
    model = Expense
    template_name = 'expense/list.html'
    context_object_name = 'expenses'
    paginate_by = 10

    def get_queryset(self):
        try:
            queryset = Expense.objects.all().select_related('created_by')
            
            # Search
            search = self.request.GET.get('search')
            if search:
                queryset = queryset.filter(
                    Q(expense_number__icontains=search) |
                    Q(title__icontains=search) |
                    Q(description__icontains=search)
                )

            # Filter by Status
            status = self.request.GET.get('status')
            if status:
                queryset = queryset.filter(status=status)

            # Filter by Date Range
            start_date = self.request.GET.get('start_date')
            end_date = self.request.GET.get('end_date')
            if start_date:
                queryset = queryset.filter(expense_date__gte=start_date)
            if end_date:
                queryset = queryset.filter(expense_date__lte=end_date)

            # Sorting
            sort = self.request.GET.get('sort', '-created_at')
            allowed_sorts = ['expense_date', '-expense_date', 'total_amount', '-total_amount', 'created_at', '-created_at']
            if sort in allowed_sorts:
                queryset = queryset.order_by(sort)
            else:
                queryset = queryset.order_by('-created_at')

            return queryset
        except Exception as e:
            logger.error(f"Error in ExpenseListView: {str(e)}")
            return Expense.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        all_exp = Expense.objects.all()
        
        # Comprehensive stats for the dashboard cards
        stats = all_exp.aggregate(
            total=Sum('total_amount'),
            paid=Sum('payments__amount'),
            pending=Sum('total_amount', filter=Q(status='submitted')),
            draft=Sum('total_amount', filter=Q(status='draft'))
        )
        # Calculate balance manually since it's total - paid
        stats['balance'] = (stats['total'] or Decimal('0.00')) - (stats['paid'] or Decimal('0.00'))
        context['stats'] = stats
        context['counts'] = {
            'total': all_exp.count(),
            'pending': all_exp.filter(status='submitted').count(),
            'approved': all_exp.filter(status='approved').count(),
        }
        
        # Filter persistence to keep inputs filled after submit
        context['current_search'] = self.request.GET.get('search', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_start_date'] = self.request.GET.get('start_date', '')
        context['current_end_date'] = self.request.GET.get('end_date', '')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        
        return context

class ExpenseCreateView(LoginRequiredMixin, CreateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense/add.html'
    success_url = reverse_lazy('expenses:expense_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, f"Expense '{form.instance.title}' created successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error creating expense. Please check the fields.")
        return super().form_invalid(form)

class ExpenseUpdateView(LoginRequiredMixin, UpdateView):
    model = Expense
    form_class = ExpenseForm
    template_name = 'expense/add.html'
    success_url = reverse_lazy('expenses:expense_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Expense '{form.instance.title}' updated successfully!")
        return super().form_valid(form)

class ExpenseDeleteView(LoginRequiredMixin, DeleteView):
    model = Expense
    success_url = reverse_lazy('expenses:expense_list')

    def post(self, request, *args, **kwargs):
        try:
            expense = self.get_object()
            if expense.status == 'paid':
                messages.error(request, "Cannot delete an already paid expense.")
                return redirect(self.success_url)
            
            response = super().post(request, *args, **kwargs)
            messages.success(request, "Expense deleted successfully!")
            return response
        except Exception as e:
            messages.error(request, f"Error deleting expense: {str(e)}")
            return redirect(self.success_url)

class ExpenseDetailView(LoginRequiredMixin, DetailView):
    model = Expense
    template_name = 'expense/detail.html'
    context_object_name = 'expense'

    def get_queryset(self):
        return super().get_queryset().select_related('created_by', 'approved_by').prefetch_related('payments', 'attachments', 'activity_logs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        expense = self.get_object()
        
        # Calculate payment progress percentage
        if expense.total_amount > 0:
            context['payment_percentage'] = int((expense.paid_amount / expense.total_amount) * 100)
        else:
            context['payment_percentage'] = 0

        # Stepper progress mapping
        status_map = {'draft': 0, 'submitted': 33, 'approved': 66, 'partial': 66, 'paid': 100}
        context['stepper_width'] = status_map.get(expense.status, 0)
            
        context['payment_form'] = ExpensePaymentForm()
        context['attachment_form'] = ExpenseAttachmentForm()
        context['today'] = timezone.now()
        return context

class ExpenseWorkflowView(LoginRequiredMixin, View):
    def post(self, request, pk, action):
        expense = get_object_or_404(Expense, pk=pk)
        
        if action == 'submit' and expense.status == 'draft':
            expense.status = 'submitted'
            ExpenseActivityLog.objects.create(expense=expense, action='submitted', message="Expense submitted for approval", user=request.user)
            messages.success(request, "Expense submitted for approval.")
        
        elif action == 'approve' and expense.status == 'submitted':
            expense.status = 'approved'
            expense.approved_by = request.user
            ExpenseActivityLog.objects.create(expense=expense, action='approved', message="Expense approved", user=request.user)
            messages.success(request, "Expense approved.")
        
        elif action == 'reject' and expense.status == 'submitted':
            expense.status = 'rejected'
            reason = request.POST.get('reason', '')
            expense.rejection_reason = reason
            ExpenseActivityLog.objects.create(expense=expense, action='rejected', message=f"Expense rejected: {reason}", user=request.user)
            messages.warning(request, "Expense rejected.")
            
        expense.save()
        return redirect('expenses:expense_detail', pk=pk)

class ExpensePaymentCreateView(LoginRequiredMixin, CreateView):
    model = ExpensePayment
    form_class = ExpensePaymentForm
    
    def form_valid(self, form):
        expense = get_object_or_404(Expense, pk=self.kwargs.get('pk'))
        payment = form.save(commit=False)
        payment.expense = expense
        payment.created_by = self.request.user
        payment.save()
        
        ExpenseActivityLog.objects.create(
            expense=expense, 
            action='payment_added', 
            message=f"Payment of ₹{payment.amount} added via {payment.get_payment_method_display()}", 
            user=self.request.user
        )
        
        messages.success(self.request, "Payment recorded successfully.")
        return redirect('expenses:expense_detail', pk=expense.pk)

class ExpenseAttachmentCreateView(LoginRequiredMixin, CreateView):
    model = ExpenseAttachment
    form_class = ExpenseAttachmentForm

    def form_valid(self, form):
        expense = get_object_or_404(Expense, pk=self.kwargs.get('pk'))
        attachment = form.save(commit=False)
        attachment.expense = expense
        attachment.uploaded_by = self.request.user
        attachment.save()
        
        ExpenseActivityLog.objects.create(
            expense=expense, 
            action='attachment_added', 
            message=f"File attached: {attachment.file.name}", 
            user=self.request.user
        )
        
        messages.success(self.request, "File attached successfully.")
        return redirect('expenses:expense_detail', pk=expense.pk)

class ExpenseBulkActionView(LoginRequiredMixin, View):
    def post(self, request):
        expense_ids = request.POST.getlist('expense_ids')
        action = request.POST.get('bulk_action')
        
        if not expense_ids:
            messages.warning(request, "No expenses selected.")
            return redirect('expenses:expense_list')
            
        expenses = Expense.objects.filter(id__in=expense_ids)
        
        if action == 'delete':
            # Filter non-paid ones for safety
            deletable = expenses.exclude(status='paid')
            count = deletable.count()
            deletable.delete()
            messages.success(request, f"Successfully deleted {count} expenses.")
            
        elif action == 'approve':
            # Filter submitted ones
            approvable = expenses.filter(status='submitted')
            count = approvable.count()
            for exp in approvable:
                exp.status = 'approved'
                exp.approved_by = request.user
                exp.save()
                ExpenseActivityLog.objects.create(expense=exp, action='approved', message="Bulk approved", user=request.user)
            messages.success(request, f"Successfully approved {count} expenses.")
            
        return redirect('expenses:expense_list')

class ExpenseExportCSVView(LoginRequiredMixin, View):
    def get(self, request):
        from django.utils import timezone
        import csv
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="expenses_export_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Expense No', 'Title', 'Date', 'Amount', 'Tax', 'Total', 'Status', 'Created By'])
        
        expenses = Expense.objects.all().select_related('created_by')
        for exp in expenses:
            writer.writerow([
                exp.expense_number,
                exp.title,
                exp.expense_date,
                exp.amount,
                exp.tax_amount,
                exp.total_amount,
                exp.get_status_display(),
                exp.created_by.username if exp.created_by else 'N/A'
            ])
            
        return response
