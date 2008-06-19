
from django.http import HttpResponseNotAllowed

def http_method_dispatcher(method_table_function):
    method_table = method_table_function()

    def view_func(request, *args, **kwargs):
        handler = method_table.get(request.method, None)
        if not handler:
            HttpResponseNotAllowed(method_table.keys())

        return handler( request, *args, **kwargs)

    return view_func

from django.http import HttpResponse
from django.utils.encoding import iri_to_uri

class HttpResponseCreated(HttpResponse):
    status_code = 201

    def __init__(self, redirect_to):
        HttpResponse.__init__(self)
        self['Location'] = iri_to_uri(redirect_to)
        