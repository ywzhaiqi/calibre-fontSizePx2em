#!/usr/bin/env python2
# vim:fileencoding=utf-8
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2015'

from calibre.customize import EditBookToolPlugin


class DemoPlugin(EditBookToolPlugin):

    name = 'Change Book FontSize From px to em'
    version = (1, 0, 0)
    author = 'ywzhaiqi'
    supported_platforms = ['windows', 'osx', 'linux']
    description = 'Change font size from px to em for the ebook editor'
    minimum_calibre_version = (1, 46, 0)
