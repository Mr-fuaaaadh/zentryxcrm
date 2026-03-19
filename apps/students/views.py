from django.views.generic import ListView, TemplateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.db import transaction
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from .models import Student
from .forms import StudentUpdateForm

User = get_user_model()

class StudentListView(LoginRequiredMixin, ListView):
    model = Student
    template_name = 'student/list.html'
    context_object_name = 'students'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset().select_related('user', 'course')
        
        # Searching
        search_query = self.request.GET.get('search', '').strip()
        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(student_id__icontains=search_query)
            )

        # Filtering
        status_filter = self.request.GET.get('status', '').strip()
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        course_filter = self.request.GET.get('course', '').strip()
        if course_filter:
            queryset = queryset.filter(course_id=course_filter)

        # Sorting
        sort_by = self.request.GET.get('sort', '-created_at').strip()
        allowed_sort_fields = [
            'student_id', '-student_id',
            'user__first_name', '-user__first_name',
            'joining_date', '-joining_date',
            'status', '-status',
            'created_at', '-created_at'
        ]
        if sort_by in allowed_sort_fields:
            queryset = queryset.order_by(sort_by)
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('search', '')
        context['status_filter'] = self.request.GET.get('status', '')
        context['course_filter'] = self.request.GET.get('course', '')
        context['sort_by'] = self.request.GET.get('sort', '-created_at')
        context['status_choices'] = Student.STATUS_CHOICES
        
        # Student Statistics
        context['total_students'] = Student.objects.count()
        context['active_students'] = Student.objects.filter(status='ACTIVE').count()
        context['graduated_students'] = Student.objects.filter(status='GRADUATED').count()
        
        from django.utils import timezone
        now = timezone.now()
        context['new_enrollments'] = Student.objects.filter(
            joining_date__month=now.month,
            joining_date__year=now.year
        ).count()
        
        try:
            from apps.course.models import Course
            context['courses'] = Course.objects.all()
        except ImportError:
            context['courses'] = []
            
        return context


class StudentAdd(LoginRequiredMixin, TemplateView):
    template_name = "student/create.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Student.STATUS_CHOICES
        try:
            from apps.course.models import Course
            context['courses'] = Course.objects.all()
        except ImportError:
            context['courses'] = []
        return context

    def post(self, request, *args, **kwargs):
        data = request.POST
        files = request.FILES
        
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return self.get(request, *args, **kwargs)
            
        try:
            with transaction.atomic():
                # Create User
                email = data.get('email')
                user = User.objects.create_user(
                    email=email,
                    username=email.split('@')[0],
                    first_name=data.get('first_name'),
                    last_name=data.get('last_name'),
                    password=password,
                    role='STUDENT'
                )
                
                if 'profile_image' in files:
                    user.profile_image = files['profile_image']
                    user.save()

                # Create Student Profile
                Student.objects.create(
                    user=user,
                    course_id=data.get('course') or None,
                    status=data.get('status', 'ACTIVE'),
                    joining_date=data.get('joining_date') or timezone.now().date(),
                    emergency_contact=data.get('emergency_contact', ''),
                    address=data.get('address', '')
                )
                
            messages.success(request, f"Student profile created successfully for {user.get_full_name()}.")
            return redirect('students:list')
            
        except Exception as e:
            messages.error(request, f"Error creating student: {str(e)}")
            return self.get(request, *args, **kwargs)

class StudentUpdateView(LoginRequiredMixin, UpdateView):
    model = Student
    form_class = StudentUpdateForm
    template_name = 'student/update.html'
    success_url = reverse_lazy('students:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Student.STATUS_CHOICES
        try:
            from apps.course.models import Course
            context['courses'] = Course.objects.all()
        except ImportError:
            context['courses'] = []
        return context

    def form_valid(self, form):
        messages.success(self.request, "Student profile updated successfully.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error updating student. Please check the form.")
        return super().form_invalid(form)

class StudentDeleteView(LoginRequiredMixin, DeleteView):
    model = Student
    success_url = reverse_lazy('students:list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete() # Soft delete
        messages.warning(request, "Student profile deleted successfully.")
        return HttpResponseRedirect(self.get_success_url())

    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)
