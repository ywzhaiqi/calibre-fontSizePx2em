#!/usr/bin/env python2
# vim:fileencoding=utf-8
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2015'

import re
from PyQt5.Qt import QAction, QInputDialog
from cssutils.css import CSSRule

# The base class that all tools must inherit from
from calibre.gui2.tweak_book.plugin import Tool

from calibre import force_unicode
from calibre.gui2 import error_dialog
from calibre.ebooks.oeb.polish.container import OEB_DOCS, OEB_STYLES, serialize

class DemoTool(Tool):

    #: Set this to a unique name it will be used as a key
    name = 'fontsize-px2em'

    #: If True the user can choose to place this tool in the plugins toolbar
    allowed_in_toolbar = True

    #: If True the user can choose to place this tool in the plugins menu
    allowed_in_menu = True

    isChanged = False

    def create_action(self, for_toolbar=True):
        # Create an action, this will be added to the plugins toolbar and
        # the plugins menu
        ac = QAction(get_icons('images/icon.png'), 'font px to em', self.gui)  # noqa
        if not for_toolbar:
            # Register a keyboard shortcut for this toolbar action. We only
            # register it for the action created for the menu, not the toolbar,
            # to avoid a double trigger
            self.register_shortcut(ac, 'fontsize-px2em-tool', default_keys=('Ctrl+Shift+Alt+E',))
        ac.triggered.connect(self.ask_user)
        return ac

    def ask_user(self):
        # Ensure any in progress editing the user is doing is present in the container
        self.boss.commit_all_editors_to_container()
        try:
            self.magnify_fonts()
        except Exception:
            # Something bad happened report the error to the user
            import traceback
            error_dialog(self.gui, _('Failed to magnify fonts'), _(
                'Failed to magnify fonts, click "Show details" for more info'),
                det_msg=traceback.format_exc(), show=True)
            # Revert to the saved restore point
            self.boss.revert_requested(self.boss.global_undo.previous_container)
        else:
            if self.isChanged:
                # Show the user what changes we have made, allowing her to
                # revert them if necessary
                self.boss.show_current_diff()
                # Update the editor UI to take into account all the changes we
                # have made
                self.boss.apply_container_update_to_gui()

    def magnify_fonts(self):
        # Magnify all font sizes defined in the book by the specified factor
        # First we create a restore point so that the user can undo all changes
        # we make.
        self.boss.add_savepoint('Before: Change fonts px to em')

        container = self.current_container  # The book being edited as a container object

        # Iterate over all style declarations in the book, this means css
        # stylesheets, <style> tags and style="" attributes
        for name, media_type in container.mime_map.iteritems():
            if media_type in OEB_STYLES:
                # A stylesheet. Parsed stylesheets are cssutils CSSStylesheet
                # objects.
                self.magnify_stylesheet(container.parsed(name))
                container.dirty(name)  # Tell the container that we have changed the stylesheet
            elif media_type in OEB_DOCS:
                # A HTML file. Parsed HTML files are lxml elements

                for style_tag in container.parsed(name).xpath('//*[local-name="style"]'):
                    if style_tag.text and style_tag.get('type', None) in {None, 'text/css'}:
                        # We have an inline CSS <style> tag, parse it into a
                        # stylesheet object
                        sheet = container.parse_css(style_tag.text)
                        self.magnify_stylesheet(sheet)
                        style_tag.text = serialize(sheet, 'text/css', pretty_print=True)
                        container.dirty(name)  # Tell the container that we have changed the stylesheet
                for elem in container.parsed(name).xpath('//*[@style]'):
                    # Process inline style attributes
                    block = container.parse_css(elem.get('style'), is_declaration=True)
                    self.magnify_declaration(block)
                    elem.set('style', force_unicode(block.getCssText(separator=' '), 'utf-8'))

    def magnify_stylesheet(self, sheet):
        for rule in sheet.cssRules.rulesOfType(CSSRule.STYLE_RULE):
            self.magnify_declaration(rule.style)

    def magnify_declaration(self, style):
        # Magnify all fonts in the specified style declaration by the specified
        # factor
        val = style.getPropertyValue('font-size')
        if not val:
            return

        if 'px' not in val:
            return

        # see if the font-size contains a number
        num = re.search(r'[0-9.]+', val)
        if num is not None:
            num = num.group()
            val = val.replace(num, '%f' % (float(num) / 16))
            val = val.replace('px', 'em')
            style.setProperty('font-size', val)
            self.isChanged = True
