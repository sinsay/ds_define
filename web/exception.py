import json
import datetime
from werkzeug.exceptions import HTTPException


class APIException(HTTPException):
    """
    Serialization to json response
    """
    # http code
    code = None
    # message description
    description = None
    # custom code
    status_code = None

    data = None

    def __init__(self, status_code=None, description=None, data=None, response=None):
        super().__init__(description, response)
        if status_code is not None:
            self.status_code = status_code

        if data is not None:
            self.data = data

    def get_description(self, environ=None):
        return self.description

    def get_body(self, environ=None):
        return json.dumps({
            "code": self.status_code or self.name.replace(" ", "_").upper(),
            "message": self.get_description(environ),
            "data": self.data
        })

    def get_headers(self, environ=None):
        """Get a list of headers."""
        return [("Content-Type", "application/json; charset=utf-8")]


class BadRequest(APIException):
    """*400* `Bad Request`

    Raise if the browser sends something to the application the application
    or server cannot handle.
    """

    code = 400
    description = (
        "The browser (or proxy) sent a request that this server could "
        "not understand."
    )


class SecurityError(BadRequest):
    """
    Raised if something triggers a security error.  This is otherwise
    exactly like a bad request error.
    """


class BadHost(BadRequest):
    """
    Raised if the submitted host is badly formatted.
    """


class Unauthorized(APIException):
    """
    *401* ``Unauthorized``
    """

    code = 401
    description = (
        "The server could not verify that you are authorized to access"
        " the URL requested. You either supplied the wrong credentials"
        " (e.g. a bad password), or your browser doesn't understand"
        " how to supply the credentials required."
    )

    def __init__(self, description=None, response=None, www_authenticate=None):
        APIException.__init__(self, description, response)

        if www_authenticate is not None:
            if not isinstance(www_authenticate, (tuple, list)):
                www_authenticate = (www_authenticate,)

        self.www_authenticate = www_authenticate

    def get_headers(self, environ=None):
        headers = APIException.get_headers(self, environ)
        if self.www_authenticate:
            headers.append(
                ("WWW-Authenticate", ", ".join([str(x) for x in self.www_authenticate]))
            )
        return headers


class Forbidden(APIException):
    """*403* `Forbidden`

    Raise if the user doesn't have the permission for the requested resource
    but was authenticated.
    """

    code = 403
    description = (
        "You don't have the permission to access the requested"
        " resource. It is either read-protected or not readable by the"
        " server."
    )


class NotFound(APIException):
    """*404* `Not Found`

    Raise if a resource does not exist and never existed.
    """

    code = 404
    description = (
        "The requested URL was not found on the server. If you entered"
        " the URL manually please check your spelling and try again."
    )


class MethodNotAllowed(APIException):
    """*405* `Method Not Allowed`

    Raise if the server used a method the resource does not handle.  For
    example `POST` if the resource is view only.  Especially useful for REST.

    The first argument for this exception should be a list of allowed methods.
    Strictly speaking the response would be invalid if you don't provide valid
    methods in the header which you can do with that list.
    """

    code = 405
    description = "The method is not allowed for the requested URL."

    def __init__(self, valid_methods=None, description=None):
        """Takes an optional list of valid http methods
        starting with werkzeug 0.3 the list will be mandatory."""
        APIException.__init__(self, description)
        self.valid_methods = valid_methods

    def get_headers(self, environ=None):
        headers = APIException.get_headers(self, environ)
        if self.valid_methods:
            headers.append(("Allow", ", ".join(self.valid_methods)))
        return headers


class NotAcceptable(APIException):
    """*406* `Not Acceptable`

    Raise if the server can't return any content conforming to the
    `Accept` headers of the client.
    """

    code = 406

    description = (
        "The resource identified by the request is only capable of"
        " generating response entities which have content"
        " characteristics not acceptable according to the accept"
        " headers sent in the request."
    )


class RequestTimeout(APIException):
    """*408* `Request Timeout`

    Raise to signalize a timeout.
    """

    code = 408
    description = (
        "The server closed the network connection because the browser"
        " didn't finish the request within the specified time."
    )


class Conflict(APIException):
    """*409* `Conflict`

    Raise to signal that a request cannot be completed because it conflicts
    with the current state on the server.
    """

    code = 409
    description = (
        "A conflict happened while processing the request. The"
        " resource might have been modified while the request was being"
        " processed."
    )


class Gone(APIException):
    """*410* `Gone`

    Raise if a resource existed previously and went away without new location.
    """

    code = 410
    description = (
        "The requested URL is no longer available on this server and"
        " there is no forwarding address. If you followed a link from a"
        " foreign page, please contact the author of this page."
    )


class LengthRequired(APIException):
    """*411* `Length Required`

    Raise if the browser submitted data but no ``Content-Length`` header which
    is required for the kind of processing the server does.
    """

    code = 411
    description = (
        "A request with this method requires a valid <code>Content-"
        "Length</code> header."
    )


class PreconditionFailed(APIException):
    """*412* `Precondition Failed`

    Status code used in combination with ``If-Match``, ``If-None-Match``, or
    ``If-Unmodified-Since``.
    """

    code = 412
    description = (
        "The precondition on the request for the URL failed positive evaluation."
    )


class RequestEntityTooLarge(APIException):
    """*413* `Request Entity Too Large`

    The status code one should return if the data submitted exceeded a given
    limit.
    """

    code = 413
    description = "The data value transmitted exceeds the capacity limit."


class RequestURITooLarge(APIException):
    """*414* `Request URI Too Large`

    Like *413* but for too long URLs.
    """

    code = 414
    description = (
        "The length of the requested URL exceeds the capacity limit for"
        " this server. The request cannot be processed."
    )


class UnsupportedMediaType(APIException):
    """*415* `Unsupported Media Type`

    The status code returned if the server is unable to handle the media type
    the client transmitted.
    """

    code = 415
    description = (
        "The server does not support the media type transmitted in the request."
    )


class RequestedRangeNotSatisfiable(APIException):
    """*416* `Requested Range Not Satisfiable`

    The client asked for an invalid part of the file.
    """

    code = 416
    description = "The server cannot provide the requested range."

    def __init__(self, length=None, units="bytes", description=None):
        """Takes an optional `Content-Range` header value based on ``length``
        parameter.
        """
        APIException.__init__(self, description)
        self.length = length
        self.units = units

    def get_headers(self, environ=None):
        headers = APIException.get_headers(self, environ)
        if self.length is not None:
            headers.append(("Content-Range", "%s */%d" % (self.units, self.length)))
        return headers


class ExpectationFailed(APIException):
    """*417* `Expectation Failed`

    The server cannot meet the requirements of the Expect request-header.

    """

    code = 417
    description = "The server could not meet the requirements of the Expect header"


class ImATeapot(APIException):
    """*418* `I'm a teapot`

    The server should return this if it is a teapot and someone attempted
    to brew coffee with it.

    """

    code = 418
    description = "This server is a teapot, not a coffee machine"


class UnprocessableEntity(APIException):
    """*422* `Unprocessable Entity`

    Used if the request is well formed, but the instructions are otherwise
    incorrect.
    """

    code = 422
    description = (
        "The request was well-formed but was unable to be followed due"
        " to semantic errors."
    )


class Locked(APIException):
    """*423* `Locked`

    Used if the resource that is being accessed is locked.
    """

    code = 423
    description = "The resource that is being accessed is locked."


class FailedDependency(APIException):
    """*424* `Failed Dependency`

    Used if the method could not be performed on the resource
    because the requested action depended on another action and that action failed.
    """

    code = 424
    description = (
        "The method could not be performed on the resource because the"
        " requested action depended on another action and that action"
        " failed."
    )


class PreconditionRequired(APIException):
    """*428* `Precondition Required`

    The server requires this request to be conditional, typically to prevent
    the lost update problem, which is a race condition between two or more
    clients attempting to update a resource through PUT or DELETE. By requiring
    each client to include a conditional header ("If-Match" or "If-Unmodified-
    Since") with the proper value retained from a recent GET request, the
    server ensures that each client has at least seen the previous revision of
    the resource.
    """

    code = 428
    description = (
        "This request is required to be conditional; try using"
        ' "If-Match" or "If-Unmodified-Since".'
    )


class _RetryAfter(APIException):
    """Adds an optional ``retry_after`` parameter which will set the
    ``Retry-After`` header. May be an :class:`int` number of seconds or
    a :class:`~datetime.datetime`.
    """

    def __init__(self, description=None, response=None, retry_after=None):
        super(_RetryAfter, self).__init__(description, response)
        self.retry_after = retry_after

    def get_headers(self, environ=None):
        headers = super(_RetryAfter, self).get_headers(environ)

        if self.retry_after:
            if isinstance(self.retry_after, datetime.datetime):
                from werkzeug.http import http_date
                value = http_date(self.retry_after)
            else:
                value = str(self.retry_after)

            headers.append(("Retry-After", value))

        return headers


class TooManyRequests(_RetryAfter):
    """*429* `Too Many Requests`

    The server is limiting the rate at which this user receives
    responses, and this request exceeds that rate. (The server may use
    any convenient method to identify users and their request rates).
    The server may include a "Retry-After" header to indicate how long
    the user should wait before retrying.

    :param retry_after: If given, set the ``Retry-After`` header to this
        value. May be an :class:`int` number of seconds or a
        :class:`~datetime.datetime`.
    """

    code = 429
    description = "This user has exceeded an allotted request count. Try again later."


class RequestHeaderFieldsTooLarge(APIException):
    """*431* `Request Header Fields Too Large`

    The server refuses to process the request because the header fields are too
    large. One or more individual fields may be too large, or the set of all
    headers is too large.
    """

    code = 431
    description = "One or more header fields exceeds the maximum size."


class UnavailableForLegalReasons(APIException):
    """*451* `Unavailable For Legal Reasons`

    This status code indicates that the server is denying access to the
    resource as a consequence of a legal demand.
    """

    code = 451
    description = "Unavailable for legal reasons."


class InternalServerError(APIException):
    """*500* `Internal Server Error`

    Raise if an internal server error occurred.  This is a good fallback if an
    unknown error occurred in the dispatcher.
    """

    code = 500
    description = (
        "The server encountered an internal error and was unable to"
        " complete your request. Either the server is overloaded or"
        " there is an error in the application."
    )

    def __init__(self, description=None, response=None, original_exception=None):
        #: The original exception that caused this 500 error. Can be
        #: used by frameworks to provide context when handling
        #: unexpected errors.
        self.original_exception = original_exception
        super(InternalServerError, self).__init__(
            description=description, response=response
        )


class NotImplementedException(APIException):
    """*501* `Not Implemented`

    Raise if the application does not support the action requested by the
    browser.
    """

    code = 501
    description = "The server does not support the action requested by the browser."


class BadGateway(APIException):
    """*502* `Bad Gateway`

    If you do proxying in your application you should return this status code
    if you received an invalid response from the upstream server it accessed
    in attempting to fulfill the request.
    """

    code = 502
    description = (
        "The proxy server received an invalid response from an upstream server."
    )


class ServiceUnavailable(_RetryAfter):
    """*503* `Service Unavailable`

    Status code you should return if a service is temporarily
    unavailable.

    :param retry_after: If given, set the ``Retry-After`` header to this
        value. May be an :class:`int` number of seconds or a
        :class:`~datetime.datetime`.
    """

    code = 503
    description = (
        "The server is temporarily unable to service your request due"
        " to maintenance downtime or capacity problems. Please try"
        " again later."
    )


class GatewayTimeout(APIException):
    """*504* `Gateway Timeout`

    Status code you should return if a connection to an upstream server
    times out.
    """

    code = 504
    description = "The connection to an upstream server timed out."


class HTTPVersionNotSupported(APIException):
    """*505* `HTTP Version Not Supported`

    The server does not support the HTTP protocol version used in the request.
    """

    code = 505
    description = (
        "The server does not support the HTTP protocol version used in the request."
    )
