# This file is part documentation module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
import unittest

from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import suite as test_suite


class DocumentationTestCase(ModuleTestCase):
    'Test Documentation module'
    module = 'documentation'


def suite():
    suite = test_suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
            DocumentationTestCase))
    return suite
