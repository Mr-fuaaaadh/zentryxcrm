from django.apps import AppConfig


class CourseConfig(AppConfig):
    name = 'apps.course'
    default_auto_field = 'django.db.models.BigAutoField'
    label = 'course'

    def ready(self):
        import apps.course.signals
