from AccessControl import getSecurityManager
from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from six import reraise
from zExceptions import Unauthorized
from zExceptions.ExceptionFormatter import format_exception
from zope.interface import classImplements
from zope.security.interfaces import IUnauthorized
import json
import sys


class ExceptionView(BrowserView):
    basic_template = ViewPageTemplateFile('templates/basic_error_message.pt')

    def is_manager(self):
        return getSecurityManager().checkPermission(
            'Manage portal', self.context)

    def __call__(self):
        exception = self.context
        self.context = self.__parent__

        # If running in the testbrowser with handleErrors=False,
        # avoid rendering exception view
        if not self.request.environ.get('wsgi.handleErrors', True):
            reraise(*sys.exc_info())

        error_type = exception.__class__.__name__
        error_tb = ''.join(format_exception(*sys.exc_info(), as_html=True))

        request = self.request
        response = self.request.response

        # Call PAS _unauthorized hook for Unauthorized exceptions
        is_unauthorized = IUnauthorized.providedBy(exception)
        if is_unauthorized and hasattr(response, '_unauthorized'):
            response._unauthorized()

        # Indicate exception as JSON
        accept = request.getHeader('Accept', '')
        if accept and "text/html" not in accept:
            request.response.setHeader("Content-Type", "application/json")
            return json.dumps({
                'error_type': error_type,
            })

        # Use a simplified template if main_template is not available
        try:
            self.context.unrestrictedTraverse('main_template')
        except:
            template = self.basic_template
        else:
            template = self.index

        # Render page with user-facing error notice
        request.set('disable_border', True)
        request.set('disable_plone.leftcolumn', True)
        request.set('disable_plone.rightcolumn', True)

        try:
            return template(
                error_type=error_type,
                error_tb=error_tb,
            )
        except:
            # There was an error rendering the exception,
            # so try the more basic template.
            return self.basic_template(
                error_type=error_type,
                error_tb=error_tb,
            )


class IPloneUnauthorized(IUnauthorized):
    pass
classImplements(Unauthorized, IPloneUnauthorized)


class UnrenderedExceptionView(BrowserView):
    # Re-raise exceptions that should never be rendered.
    # (ConflictError, KeyboardInterrupt)

    def __call__(self):
        reraise(*sys.exc_info())


class RedirectView(BrowserView):
    # Make sure 30x HTTP exceptions are always rendered
    # even in the test browser with handleErrors = False.
    # And make sure we don't waste time rendering a body
    # for them.

    def __call__(self):
        return ''
