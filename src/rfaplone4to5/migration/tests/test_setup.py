# -*- coding: utf-8 -*-
"""Setup tests for this package."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from rfaplone4to5.migration.testing import RFAPLONE4TO5_MIGRATION_INTEGRATION_TESTING  # noqa

import unittest


class TestSetup(unittest.TestCase):
    """Test that rfaplone4to5.migration is properly installed."""

    layer = RFAPLONE4TO5_MIGRATION_INTEGRATION_TESTING

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')

    def test_product_installed(self):
        """Test if rfaplone4to5.migration is installed."""
        self.assertTrue(self.installer.isProductInstalled(
            'rfaplone4to5.migration'))

    def test_browserlayer(self):
        """Test that IRfaplone4to5MigrationLayer is registered."""
        from rfaplone4to5.migration.interfaces import (
            IRfaplone4to5MigrationLayer)
        from plone.browserlayer import utils
        self.assertIn(
            IRfaplone4to5MigrationLayer,
            utils.registered_layers())


class TestUninstall(unittest.TestCase):

    layer = RFAPLONE4TO5_MIGRATION_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.installer = api.portal.get_tool('portal_quickinstaller')
        roles_before = api.user.get_roles(TEST_USER_ID)
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.installer.uninstallProducts(['rfaplone4to5.migration'])
        setRoles(self.portal, TEST_USER_ID, roles_before)

    def test_product_uninstalled(self):
        """Test if rfaplone4to5.migration is cleanly uninstalled."""
        self.assertFalse(self.installer.isProductInstalled(
            'rfaplone4to5.migration'))

    def test_browserlayer_removed(self):
        """Test that IRfaplone4to5MigrationLayer is removed."""
        from rfaplone4to5.migration.interfaces import \
            IRfaplone4to5MigrationLayer
        from plone.browserlayer import utils
        self.assertNotIn(
            IRfaplone4to5MigrationLayer,
            utils.registered_layers())
