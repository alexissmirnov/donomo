"""
Handy helpers and typs for dealing the HTTP requests and responses

Inspired by the django-http-status project on Google code.  See:

    http://code.google.com/p/django-http-status/

Response code descriptions taken from:

    http://www.w3.org/Protocols/rfc2616/rfc2616-sec10.html

"""

#
# pylint: disable-msg = W0142, W0611
#
#   W0142 - use of * and ** magic
#   W0611 - unused imports
#

import httplib
from django.utils.encoding import iri_to_uri
from django.http import (
    HttpResponse,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponseGone,
    HttpResponseNotAllowed,
    HttpResponseNotFound,
    HttpResponseNotModified,
    HttpResponsePermanentRedirect,
    HttpResponseRedirect,
    HttpResponseServerError,
    )


# -----------------------------------------------------------------------------

def http_method_dispatcher(method_table_function):
    """
    Decorator function for a view function dispatcher based on the HTTP
    method of the incoming Django request.

    """

    method_table = method_table_function()

    def view_func(request, *args, **kwargs):
        """
        The resulting view function

        """
        method = request.GET.get('_method', request.method).upper()
        
        handler = method_table.get(method, None)
        if not handler:
            return HttpResponseNotAllowed(method_table.keys())

        return handler( request, *args, **kwargs)

    return view_func

# -----------------------------------------------------------------------------

class HttpResponseCreated(HttpResponse):
    """
    The request has been fulfilled and resulted in a new resource being created.

    """

    status_code = httplib.CREATED

    def __init__(self, location = None):

        """
        Constructor

        """

        HttpResponse.__init__(self)
        if location:
            self['Location'] = iri_to_uri(location)

# -----------------------------------------------------------------------------

class HttpResponseAccepted(HttpResponse):
    """
    The request has been accepted for processing, but the processing has not
    been completed.

    """
    status_code = httplib.ACCEPTED

# -----------------------------------------------------------------------------

class HttpResponseNonAuthoritativeInformation(HttpResponse):
    """
    The returned metainformation in the entity-header is not the definitive
    set as available from the origin server, but is gathered from a local or
    a third-party copy.

    """
    status_code = httplib.NON_AUTHORITATIVE_INFORMATION

# -----------------------------------------------------------------------------

class HttpResponseNoContent(HttpResponse):
    """
    The server has fulfilled the request but does not need to return an
    entity-body, and might want to return updated metainformation.

    """

    status_code = httplib.NO_CONTENT

# -----------------------------------------------------------------------------

class HttpResponseResetContent(HttpResponse):
    """
    The server has fulfilled the request and the user agent SHOULD
    reset the document view which caused the request to be sent. This
    response is primarily intended to allow input for actions to take
    place via user input, followed by a clearing of the form in which
    the input is given so that the user can easily initiate another
    input action. The response MUST NOT include an entity.

    """

    status_code = httplib.RESET_CONTENT

# -----------------------------------------------------------------------------

class HttpResponsePartialContent(HttpResponse):
    """
    The server has fulfilled the partial GET request for the resource. The
    request MUST have included a Range header field indicating the desired
    range, and MAY have included an If-Range header field to make the request
    conditional.

    """

    #
    # TODO: Update HttpResponsePartialContent to fill in headers and body
    #
    # The response MUST include the following header fields:
    #
    #   - Either a Content-Range header field (section 14.16) indicating
    #     the range included with this response, or a multipart/byteranges
    #     Content-Type including Content-Range fields for each part. If a
    #     Content-Length header field is present in the response, its
    #     value MUST match the actual number of OCTETs transmitted in the
    #     message-body.
    #
    #   - Date
    #
    #   - ETag and/or Content-Location, if the header would have been sent
    #     in a 200 response to the same request
    #
    #   - Expires, Cache-Control, and/or Vary, if the field-value might
    #     differ from that sent in any previous response for the same
    #     variant
    #

    status_code = httplib.PARTIAL_CONTENT

# -----------------------------------------------------------------------------

class HttpResponseMultiStatus(HttpResponse):
    """
    WebDAV response code.

    The message body that follows is an XML message and can contain a
    number of separate response codes, depending on how many
    sub-requests were made.

    """

    status_code = httplib.MULTI_STATUS

# -----------------------------------------------------------------------------

class HttpResponseMultipleChoices(HttpResponse):
    """
    The requested resource corresponds to any one of a set of representations,
    each with its own specific location.

    """

    status_code = httplib.MULTIPLE_CHOICES


# -----------------------------------------------------------------------------

class HttpResponseSeeOther(HttpResponse):
    """
    The response to the request can be found under a different URI and
    SHOULD be retrieved using a GET method on that resource. This
    method exists primarily to allow the output of a POST-activated
    script to redirect the user agent to a selected resource.

    """

    status_code = httplib.SEE_OTHER


# -----------------------------------------------------------------------------

class HttpResponseUseProxy(HttpResponse):
    """
    The requested resource MUST be accessed through the proxy given by
    the Location field. The Location field gives the URI of the
    proxy. The recipient is expected to repeat this single request via
    the proxy.

    HttpResponseUseProxy responses MUST only be generated by origin servers.

    """

    status_code = httplib.USE_PROXY

# -----------------------------------------------------------------------------

class HttpResponseTemporaryRedirect(HttpResponse):
    """
    The requested resource resides temporarily under a different
    URI. Since the redirection MAY be altered on occasion, the client
    SHOULD continue to use the Request-URI for future requests. This
    response is only cacheable if indicated by a Cache-Control or
    Expires header field.
    """

    status_code = httplib.TEMPORARY_REDIRECT

# -----------------------------------------------------------------------------

class HttpResponseUnauthorized(HttpResponse):
    """
    The request requires user authentication. The response MUST
    include a WWW-Authenticate header field containing a challenge
    applicable to the requested resource. The client MAY repeat the
    request with a suitable Authorization header field. If the request
    already included Authorization credentials, then the 401 response
    indicates that authorization has been refused for those
    credentials. If the 401 response contains the same challenge as
    the prior response, and the user agent has already attempted
    authentication at least once, then the user SHOULD be presented
    the entity that was given in the response, since that entity might
    include relevant diagnostic information.

    """

    status_code = httplib.UNAUTHORIZED

# -----------------------------------------------------------------------------

class HttpResponsePaymentRequired(HttpResponse):
    """
    Reserved for future use.

    """

    status_code = httplib.PAYMENT_REQUIRED

# -----------------------------------------------------------------------------

class HttpResponseNotAcceptable(HttpResponse):
    """
    The resource identified by the request is only capable of
    generating response entities which have content characteristics
    not acceptable according to the accept headers sent in the
    request.

    """

    status_code = httplib.NOT_ACCEPTABLE

# -----------------------------------------------------------------------------

class HttpResponseProxyAuthenticationRequired(HttpResponse):
    """
    This code is similar to 401 (Unauthorized), but indicates that the
    client must first authenticate itself with the proxy. The proxy
    MUST return a Proxy-Authenticate header field containing a
    challenge applicable to the proxy for the requested resource. The
    client MAY repeat the request with a suitable Proxy-Authorization
    header field.

    """

    status_code = httplib.PROXY_AUTHENTICATION_REQUIRED

# -----------------------------------------------------------------------------

class HttpResponseRequestTimeout(HttpResponse):
    """
    The client did not produce a request within the time that the
    server was prepared to wait. The client MAY repeat the request
    without modifications at any later time.

    """

    status_code = httplib.REQUEST_TIMEOUT

# -----------------------------------------------------------------------------

class HttpResponseConflict(HttpResponse):
    """
    The request could not be completed due to a conflict with the
    current state of the resource. This code is only allowed in
    situations where it is expected that the user might be able to
    resolve the conflict and resubmit the request. The response body
    SHOULD include enough information for the user to recognize the
    source of the conflict.

    """

    status_code = httplib.CONFLICT

# -----------------------------------------------------------------------------

class HttpResponseLengthRequired(HttpResponse):
    """
    The server refuses to accept the request without a defined
    Content- Length. The client MAY repeat the request if it adds a
    valid Content-Length header field containing the length of the
    message-body in the request message.

    """

    status_code = httplib.LENGTH_REQUIRED

# -----------------------------------------------------------------------------

class HttpResponsePreconditionFailed(HttpResponse):
    """
    The precondition given in one or more of the request-header fields
    evaluated to false when it was tested on the server. This response
    code allows the client to place preconditions on the current
    resource metainformation (header field data) and thus prevent the
    requested method from being applied to a resource other than the
    one intended.

    """

    status_code = httplib.PRECONDITION_FAILED

# -----------------------------------------------------------------------------

class HttpResponseRequestEntityTooLarge(HttpResponse):
    """
    The server is refusing to process a request because the request
    entity is larger than the server is willing or able to process.
    The server MAY close the connection to prevent the client from
    continuing the request.

    """

    status_code = httplib.REQUEST_ENTITY_TOO_LARGE

# -----------------------------------------------------------------------------

class HttpResponseRequestURITooLong(HttpResponse):
    """
    The server is refusing to service the request because the
    Request-URI is longer than the server is willing to
    interpret. This rare condition is only likely to occur when a
    client has improperly converted a POST request to a GET request
    with long query information, when the client has descended into a
    URI "black hole" of redirection (e.g., a redirected URI prefix
    that points to a suffix of itself), or when the server is under
    attack by a client attempting to exploit security holes present in
    some servers using fixed-length buffers for reading or
    manipulating the Request-URI.

    """

    status_code = httplib.REQUEST_URI_TOO_LONG

# -----------------------------------------------------------------------------

class HttpResponseUnsupportedMediaType(HttpResponse):
    """
    The server is refusing to service the request because the entity
    of the request is in a format not supported by the requested
    resource for the requested method.

    """

    status_code = httplib.UNSUPPORTED_MEDIA_TYPE

# -----------------------------------------------------------------------------

class HttpResponseRequestedRangeNotSatisfiable(HttpResponse):
    """
    A server SHOULD return a response with this status code if a
    request included a Range request-header field, and none of the
    range-specifier values in this field overlap the current extent of
    the selected resource, and the request did not include an If-Range
    request-header field. (For byte-ranges, this means that the first-
    byte-pos of all of the byte-range-spec values were greater than
    the current length of the selected resource.)

    When this status code is returned for a byte-range request, the
    response SHOULD include a Content-Range entity-header field
    specifying the current length of the selected resource. This
    response MUST NOT use the multipart/byteranges content- type.

    """

    status_code = httplib.REQUESTED_RANGE_NOT_SATISFIABLE

# -----------------------------------------------------------------------------

class HttpResponseExpectationFailed(HttpResponse):
    """
    The expectation given in an Expect request-header field could not
    be met by this server, or, if the server is a proxy, the server
    has unambiguous evidence that the request could not be met by the
    next-hop server.
    """

    status_code = httplib.EXPECTATION_FAILED

# -----------------------------------------------------------------------------

class HttpResponseUnprocessableEntity(HttpResponse):
    """
    WebDAV response code.

    The request was well-formed but was unable to be followed due to
    semantic errors.

    """

    status_code = httplib.UNPROCESSABLE_ENTITY

# -----------------------------------------------------------------------------

class HttpResponseLocket(HttpResponse):
    """
    WebDAV response code.

    The resource that is being accessed is locked.

    """

    status_code = httplib.LOCKED

# -----------------------------------------------------------------------------

class HttpResponseFailedDependency(HttpResponse):
    """
    WebDAV response code.

    The request failed due to failure of a previous request (e.g. a PROPPATCH).
    """

    status_code = httplib.FAILED_DEPENDENCY

# -----------------------------------------------------------------------------

class HttpResponseUpgradeRequired(HttpResponse):
    """
    The client should switch to TLS/1.0

    """

    status_code = httplib.UPGRADE_REQUIRED

# -----------------------------------------------------------------------------

class HttpResponseNotImplemented(HttpResponse):
    """
    The server does not support the functionality required to fulfill
    the request. This is the appropriate response when the server does
    not recognize the request method and is not capable of supporting
    it for any resource.

    """

    status_code = httplib.NOT_IMPLEMENTED

# -----------------------------------------------------------------------------

class HttpResponseBadGateway(HttpResponse):
    """
    The server, while acting as a gateway or proxy, received an
    invalid response from the upstream server it accessed in
    attempting to fulfill the request.

    """

    status_code = httplib.BAD_GATEWAY

# -----------------------------------------------------------------------------

class HttpResponseServiceUnavailable(HttpResponse):
    """
    The server is currently unable to handle the request due to a
    temporary overloading or maintenance of the server. The
    implication is that this is a temporary condition which will be
    alleviated after some delay. If known, the length of the delay MAY
    be indicated in a Retry-After header. If no Retry-After is given,
    the client SHOULD handle the response as it would for a 500
    response.

    """

    status_code = httplib.SERVICE_UNAVAILABLE

    def __init__(self, retry_after = None):
        """
        Constructor

        """
        HttpResponse.__init__(self)
        if retry_after:
            self['Retry-After'] = retry_after

# -----------------------------------------------------------------------------

class HttpResponseGatewayTimeout(HttpResponse):
    """
    The server, while acting as a gateway or proxy, did not receive a
    timely response from the upstream server specified by the URI
    (e.g. HTTP, FTP, LDAP) or some other auxiliary server (e.g. DNS)
    it needed to access in attempting to complete the request.

    """

    status_code = httplib.GATEWAY_TIMEOUT

# -----------------------------------------------------------------------------

class HttpResponseHttpVersionNotSupported(HttpResponse):
    """
    The server does not support, or refuses to support, the HTTP
    protocol version that was used in the request message.

    """

    status_code = httplib.HTTP_VERSION_NOT_SUPPORTED

# -----------------------------------------------------------------------------

class HttpResponseInsufficientStorage(HttpResponse):
    """
    WebDAV response code.

    """

    status_code = httplib.INSUFFICIENT_STORAGE

# -----------------------------------------------------------------------------
