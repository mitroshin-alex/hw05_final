from django.shortcuts import render


def page_not_found(request, exception):
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def csrf_failure(request, reason=''):
    return render(request, 'core/403_csrf.html')


def internal_server_error(request, *args, **kwargs):
    return render(request, 'core/500.html')


def permission_denied(request, *args, **kwargs):
    return render(request, 'core/403.html')
