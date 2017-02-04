# -*- coding: utf-8 -*-

from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.testing.z2 import Browser
from Products.CMFPlone.testing import PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING
import unittest


class ZmiTest(unittest.TestCase):
    """Test the ZMI views."""

    layer = PRODUCTS_CMFPLONE_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(self.app)
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def tearDown(self):
        logout()

    def test_manage_properties_form(self):
        self.browser.open(self.portal_url + '/manage_propertiesForm')
        get_header = self.browser.headers.getheader
        self.assertEqual(
            get_header('Status'), '200 OK')
        self.assertTrue(
            get_header('content-type').startswith('text/html'))

    def test_manage_catalog_indexes(self):
        self.browser.open(
            self.portal_url + '/portal_catalog/manage_catalogIndexes')
        get_header = self.browser.headers.getheader
        self.assertEqual(
            get_header('Status'), '200 OK')
        self.assertTrue(
            get_header('content-type').startswith('text/html'))

    def test_manage_catalog_view(self):
        self.browser.open(
            self.portal_url + '/portal_catalog/manage_catalogView')
        get_header = self.browser.headers.getheader
        self.assertEqual(
            get_header('Status'), '200 OK')
        self.assertTrue(
            get_header('content-type').startswith('text/html'))
