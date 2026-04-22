def more_menu(request):
    items = [
        ('/summary/',       'clipboard2-data', 'Summary',    '#4F46E5'),
        ('/subscriptions/', 'repeat',          'Subs',       '#0891B2'),
        ('/savings/',       'piggy-bank',      'Savings',    '#10B981'),
        ('/limits/',        'speedometer2',    'Limits',     '#F59E0B'),
        ('/categories/',    'tags',            'Categories', '#7C3AED'),
        ('/upload/',        'upload',          'Import PDF', '#4F46E5'),
        ('/settings/',      'gear',            'Settings',   '#6B7280'),
    ]
    return {'more_items': items}

def theme_settings(request):
    if request.user.is_authenticated:
        return {'theme_mode': getattr(request.user.profile, 'theme', 'light')}
    return {'theme_mode': 'light'}
