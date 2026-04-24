from .views.helpers import process_auto_deductions

class RecurringTransactionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            process_auto_deductions(request.user)
        
        response = self.get_response(request)
        return response
