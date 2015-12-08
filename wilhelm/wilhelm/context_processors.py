from django.conf import settings

def domain_name(request):
    return {'BASE_DOMAIN_NAME': settings.DOMAIN_NAME}

def data_subdomain(request):
    return {'DATA_SUBDOMAIN_NAME': settings.DATA_SUBDOMAIN_NAME}

def main_subdomain(request):
    return {'MAIN_SUBDOMAIN_NAME': settings.MAIN_SUBDOMAIN_NAME}
