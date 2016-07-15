# This file is part documentation module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .documentation import *


def register():
    Pool.register(
        BuildDocumentationStart,
        module='documentation', type_='model')
    Pool.register(
        BuildDocumentation,
        OpenDocumentation,
        module='documentation', type_='wizard')
