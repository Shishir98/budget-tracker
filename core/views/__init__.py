from .dashboard import dashboard
from .transactions import transaction_list, transaction_add, transaction_edit, transaction_delete, bulk_categorize
from .investments import (investment_list, investment_add, investment_edit, investment_delete,
                          investment_type_list, investment_type_delete)
from .analytics import analytics
from .categories import category_list, category_edit, category_delete
from .limits import limit_list, limit_delete
from .subscriptions import subscription_list, subscription_add, subscription_edit, subscription_delete
from .savings import savings_dashboard, plan_edit, plan_delete, plan_toggle
from .summary import summary
from .pdf_upload import upload_pdf, pdf_preview
from .settings_view import user_settings
