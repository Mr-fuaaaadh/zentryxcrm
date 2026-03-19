from django.apps import AppConfig


class ExpensesConfig(AppConfig):
    name = 'apps.expenses'
    label = 'expenses'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import apps.expenses.signals
