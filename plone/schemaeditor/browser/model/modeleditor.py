import json
from lxml import etree

from zope.component import queryMultiAdapter
from Products.Five import BrowserView
from AccessControl import Unauthorized


class ModelEditorView(BrowserView):
    """ editor view """

    def modelSource(self):
        return self.context.fti.model_source


def authorized(context, request):
    authenticator = queryMultiAdapter((context, request),
                                      name=u"authenticator")
    return authenticator and authenticator.verify()


class AjaxSaveHandler(BrowserView):
    """ handle AJAX save posts """

    def __call__(self):
        """ handle AJAX save post """

        if not authorized(self.context, self.request):
            raise Unauthorized

        source = self.request.form.get('source')
        if source:
            # Is it valid XML?
            try:
                root = etree.fromstring(source)
            except etree.XMLSyntaxError, e:
                return json.dumps({
                    'success': False,
                    'message': "XMLSyntaxError: %s" % e.message.encode('utf8')
                })

            # a little more sanity checking, look at first two element levels
            if root.tag != '{http://namespaces.plone.org/supermodel/schema}model':
                return json.dumps({
                    'success': False,
                    'message': "Error: root tag must be 'model'"
                })
            for element in root.getchildren():
                if element.tag != '{http://namespaces.plone.org/supermodel/schema}schema':
                    return json.dumps({
                        'success': False,
                        'message': "Error: all model elements must be 'schema'"
                    })

            # clean up formatting sins
            source = etree.tostring(
                root,
                pretty_print=True,
                xml_declaration=True,
                encoding='utf8'
            )
            # and save to FTI
            fti = self.context.fti
            fti.manage_changeProperties(model_source=source)

            self.request.response.setHeader('Content-Type', 'application/json')
            return json.dumps({'success': True, 'message': "Saved"})