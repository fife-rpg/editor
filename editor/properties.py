# -*- coding: utf-8 -*-
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Contains the property classes

.. module:: property
    :synopsis: Contains the property classes

.. moduleauthor:: Karsten Bock <KarstenBock@gmx.net>
"""

from builtins import str
from past.builtins import basestring
from builtins import object
from abc import ABCMeta, abstractmethod

import PyCEGUI
from fife_rpg import helpers

from .list_editor import ListEditor
from .set_editor import SetEditor
from .dict_editor import DictEditor
from future.utils import with_metaclass


class BaseProperty(with_metaclass(ABCMeta, object)):

    """Base class for properties"""

    def __init__(self, editor, section, name, value_data, rows=1):
        self.editor = editor
        self.section = section
        self.name = name
        self.value_data = value_data
        self.base_widget = None
        self.base_text = None
        self.rows = rows

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        raise NotImplementedError("Method \"check_type\" was not overridden.")

    def _create_base_widget(self, root, w_type="HorizontalLayoutContainer"):
        """Create the base widget for the editor

        Args:

            root: The root widget to which to add the widget to

            y_pos: The vertical position of the widget

            w_type: The widget type to create for the container.
        """
        base_text = "/".join((self.section, self.name))
        widget_margin = self.editor.WIDGET_MARGIN
        property_container = root.createChild(w_type,
                                              "%s_container" % (base_text))
        property_container.setMargin(widget_margin)
        property_label = property_container.createChild(
            "TaharezLook/Label", "%s_label" % (base_text))
        property_label.setProperty(
            "HorzFormatting", "LeftAligned")
        property_label.setWidth(PyCEGUI.UDim(0.5, 0))
        property_label.setHeight(self.editor.WIDGET_HEIGHT)
        property_label.setText(self.name)
        property_label.setTooltipText(self.name)
        self.base_widget = property_container
        self.base_text = base_text

    @abstractmethod
    def setup_widget(self, root):
        """Sets up the widget for this property"""

    @abstractmethod
    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""

    def update_data(self, value_data):
        """Update the properties data

        Args:

            value_data: The new value data
        """
        self.value_data = value_data
        self.update_input_widgets()


class ComboProperty(BaseProperty):

    """Class for a combo property"""

    def __init__(self, editor, section, name, value_data):
        BaseProperty.__init__(self, editor, section, name, value_data)
        self.__list_items = []
        self.property_input = None

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 2:
            return False
        try:
            iter(value_data[1])
        except TypeError:
            return False
        value_type = type(value_data[0])
        for value in value_data[1]:
            if type(value) != value_type:
                return False
        return True

    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""
        possible_values = self.value_data[0]
        start_value = str(self.value_data[1])
        self.property_input.setMutedState(True)
        self.property_input.resetList()

        self.property_input.setText(start_value)
        self.property_input.setTooltipText(start_value)
        for value in possible_values:
            item = PyCEGUI.ListboxTextItem(str(value))
            item.setSelectionBrushImage("TaharezLook/"
                                        "MultiListSelectionBrush")
            self.property_input.addItem(item)
            self.__list_items.append(item)

        self.property_input.selectListItemWithEditboxText()
        self.property_input.setMutedState(False)

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self.__list_items = []
        self._create_base_widget(root)
        property_input = self.base_widget.createChild(
            "TaharezLook/Combobox", "%s_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(0.49, 0))
        property_input.subscribeEvent(
            PyCEGUI.Combobox.EventListSelectionAccepted,
            self.cb_value_changed)
        self.property_input = property_input
        self.update_input_widgets()

    def cb_value_changed(self, args):
        """Called when the value of the widget was changed

        Args:

            args: PyCEGUI event args
        """
        window = args.window
        new_value = str(window.getText())
        window.setTooltipText(new_value)
        self.editor.send_value_changed(self.section,
                                       self.name,
                                       new_value)


class ToggleProperty(BaseProperty):

    """Class for toggleable properties"""

    def __init__(self, editor, section, name, value_data):
        BaseProperty.__init__(self, editor, section, name, value_data)
        self.property_input = None

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], bool)

    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""
        cur_value = self.value_data[0]
        self.property_input.setMutedState(True)
        self.property_input.setSelected(cur_value)
        self.property_input.setMutedState(False)

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self._create_base_widget(root)
        property_input = self.base_widget.createChild(
            "TaharezLook/Checkbox", "%s_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(0.49, 0))
        property_input.subscribeEvent(
            PyCEGUI.ToggleButton.EventSelectStateChanged,
            self.cb_value_changed)
        self.property_input = property_input
        self.update_input_widgets()

    def update_data(self, value_data):
        """Update the properties data

        Args:

            value_data: The new value data
        """
        BaseProperty.update_data(self, value_data)

    def cb_value_changed(self, args):
        """Called when the value of toggle button/checkbox was changed

        Args:

            args: PyCEGUI event args
        """
        self.editor.send_value_changed(self.section,
                                       self.name,
                                       args.window.isSelected())


class PointProperty(BaseProperty):

    """Class for point properties"""

    def __init__(self, editor, section, name, value_data):
        BaseProperty.__init__(self, editor, section, name, value_data, rows=3)
        self.property_input_x = None
        self.property_input_y = None

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], helpers.DoublePointYaml)

    def update_input_widgets(self):
        """Updates the input widgets to the current data"""
        x_pos = str(self.value_data[0].x)
        y_pos = str(self.value_data[0].y)
        self.property_input_x.setMutedState(True)
        self.property_input_y.setMutedState(True)

        self.property_input_x.setText(x_pos)
        self.property_input_x.setTooltipText(x_pos)
        self.property_input_y.setText(y_pos)
        self.property_input_y.setTooltipText(y_pos)
        self.property_input_x.setMutedState(False)
        self.property_input_y.setMutedState(False)

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self._create_base_widget(root, "VerticalLayoutContainer")
        base_widget = self.base_widget
        font = base_widget.getFont()
        input_mode = PyCEGUI.Spinner.TextInputMode.FloatingPoint
        property_layout = base_widget.createChild("HorizontalLayoutContainer",
                                                  "%s_x_layout" %
                                                  (self.base_text))
        widget_height = self.editor.WIDGET_HEIGHT
        widget_margin = self.editor.WIDGET_MARGIN
        property_layout.setHeight(widget_height)
        property_layout.setMargin(widget_margin)
        property_label = property_layout.createChild("TaharezLook/Label",
                                                     "%s_x_label" %
                                                     (self.base_text))
        property_label.setText("X")
        text_width = font.getTextExtent(property_label.getText()) + 10
        property_label.setWidth(PyCEGUI.UDim(0, text_width))
        property_label.setHeight(widget_height)
        property_input = property_layout.createChild(
            "TaharezLook/Spinner", "%s_x_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(1, -text_width))
        property_input.setHeight(widget_height)
        property_input.setTextInputMode(input_mode)
        property_input.subscribeEvent(PyCEGUI.Spinner.EventValueChanged,
                                      self.cb_value_changed)
        self.property_input_x = property_input

        property_layout = base_widget.createChild("HorizontalLayoutContainer",
                                                  "%s_y_layout" %
                                                  (self.base_text))
        property_layout.setHeight(widget_height)
        property_layout.setMargin(widget_margin)

        property_label = property_layout.createChild("TaharezLook/Label",
                                                     "%s_y_label" %
                                                     (self.base_text))
        property_label.setText("Y")
        text_width = font.getTextExtent(property_label.getText()) + 10
        property_label.setWidth(PyCEGUI.UDim(0, text_width))
        property_label.setHeight(widget_height)
        property_input = property_layout.createChild(
            "TaharezLook/Spinner", "%s_y_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(1, -text_width))
        property_input.setHeight(widget_height)
        property_input.setTextInputMode(input_mode)
        property_input.subscribeEvent(PyCEGUI.Spinner.EventValueChanged,
                                      self.cb_value_changed)
        self.property_input_y = property_input
        self.update_input_widgets()

    def cb_value_changed(self, args):
        """Called when the value of a point was changed

        Args:

            args: PyCEGUI event args
        """
        x_pos_edit = self.property_input_x
        y_pos_edit = self.property_input_y
        try:
            x_pos = x_pos_edit.getCurrentValue()
            y_pos = y_pos_edit.getCurrentValue()
            pos = helpers.DoublePointYaml(x_pos, y_pos)
            self.editor.send_value_changed(self.section,
                                           self.name,
                                           pos)
        except ValueError:
            self.editor.update_widgets()


class Point3DProperty(BaseProperty):

    """Class for point3d properties"""

    def __init__(self, editor, section, name, value_data):
        BaseProperty.__init__(self, editor, section, name, value_data, rows=4)
        self.property_input_x = None
        self.property_input_y = None
        self.property_input_z = None

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], helpers.DoublePoint3DYaml)

    def update_input_widgets(self):
        """Updates the input widgets to the current data"""
        x_pos = str(self.value_data[0].x)
        y_pos = str(self.value_data[0].y)
        z_pos = str(self.value_data[0].z)
        self.property_input_x.setMutedState(True)
        self.property_input_y.setMutedState(True)
        self.property_input_z.setMutedState(True)

        self.property_input_x.setText(x_pos)
        self.property_input_x.setTooltipText(x_pos)
        self.property_input_y.setText(y_pos)
        self.property_input_y.setTooltipText(y_pos)
        self.property_input_z.setText(z_pos)
        self.property_input_z.setTooltipText(z_pos)
        self.property_input_x.setMutedState(False)
        self.property_input_y.setMutedState(False)
        self.property_input_z.setMutedState(False)

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self._create_base_widget(root, "VerticalLayoutContainer")
        base_widget = self.base_widget
        font = base_widget.getFont()
        input_mode = PyCEGUI.Spinner.TextInputMode.FloatingPoint
        property_layout = base_widget.createChild("HorizontalLayoutContainer",
                                                  "%s_x_layout" %
                                                  (self.base_text))
        widget_height = self.editor.WIDGET_HEIGHT
        widget_margin = self.editor.WIDGET_MARGIN
        property_layout.setHeight(widget_height)
        property_layout.setMargin(widget_margin)
        property_label = property_layout.createChild("TaharezLook/Label",
                                                     "%s_x_label" %
                                                     (self.base_text))
        property_label.setText("X")
        text_width = font.getTextExtent(property_label.getText()) + 10
        property_label.setWidth(PyCEGUI.UDim(0, text_width))
        property_label.setHeight(widget_height)
        property_input = property_layout.createChild(
            "TaharezLook/Spinner", "%s_x_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(1, -text_width))
        property_input.setHeight(widget_height)
        property_input.setTextInputMode(input_mode)
        property_input.subscribeEvent(PyCEGUI.Spinner.EventValueChanged,
                                      self.cb_value_changed)
        self.property_input_x = property_input

        property_layout = base_widget.createChild("HorizontalLayoutContainer",
                                                  "%s_y_layout" %
                                                  (self.base_text))
        property_layout.setHeight(widget_height)
        property_layout.setMargin(widget_margin)

        property_label = property_layout.createChild("TaharezLook/Label",
                                                     "%s_y_label" %
                                                     (self.base_text))
        property_label.setText("Y")
        text_width = font.getTextExtent(property_label.getText()) + 10
        property_label.setWidth(PyCEGUI.UDim(0, text_width))
        property_label.setHeight(widget_height)
        property_input = property_layout.createChild(
            "TaharezLook/Spinner", "%s_y_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(1, -text_width))
        property_input.setHeight(widget_height)
        property_input.setTextInputMode(input_mode)
        property_input.subscribeEvent(PyCEGUI.Spinner.EventValueChanged,
                                      self.cb_value_changed)
        self.property_input_y = property_input

        property_layout = base_widget.createChild("HorizontalLayoutContainer",
                                                  "%s_z_layout" %
                                                  (self.base_text))
        property_layout.setHeight(widget_height)
        property_layout.setMargin(widget_margin)
        property_label = property_layout.createChild("TaharezLook/Label",
                                                     "%s_z_label" %
                                                     (self.base_text))
        property_label.setText("Z")
        text_width = font.getTextExtent(property_label.getText()) + 10
        property_label.setWidth(PyCEGUI.UDim(0, text_width))
        property_label.setHeight(widget_height)
        property_input = property_layout.createChild(
            "TaharezLook/Spinner", "%s_z_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(1, -text_width))
        property_input.setHeight(widget_height)
        property_input.setTextInputMode(input_mode)
        property_input.subscribeEvent(PyCEGUI.Spinner.EventValueChanged,
                                      self.cb_value_changed)
        self.property_input_z = property_input
        self.update_input_widgets()

    def cb_value_changed(self, args):
        """Called when the value of a point was changed

        Args:

            args: PyCEGUI event args
        """
        x_pos_edit = self.property_input_x
        y_pos_edit = self.property_input_y
        z_pos_edit = self.property_input_z
        try:
            x_pos = x_pos_edit.getCurrentValue()
            y_pos = y_pos_edit.getCurrentValue()
            z_pos = z_pos_edit.getCurrentValue()
            pos = helpers.DoublePoint3DYaml(x_pos, y_pos, z_pos)
            self.editor.send_value_changed(self.section,
                                           self.name,
                                           pos)
        except ValueError:
            self.editor.update_widgets()


class TextProperty(BaseProperty):

    """Class for a text property"""

    def __init__(self, editor, section, name, value_data):
        BaseProperty.__init__(self, editor, section, name, value_data)
        self.property_input = None

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], basestring)

    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""
        cur_value = str(self.value_data[0])
        self.property_input.setMutedState(True)
        self.property_input.setText(cur_value)
        self.property_input.setTooltipText(cur_value)
        self.property_input.setMutedState(False)

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self._create_base_widget(root)
        property_input = self.base_widget.createChild(
            "TaharezLook/Editbox", "%s_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(0.49, 0))
        property_input.setHeight(self.editor.WIDGET_HEIGHT)

        property_input.subscribeEvent(PyCEGUI.Editbox.EventTextAccepted,
                                      self.cb_value_changed)
        property_input.subscribeEvent(PyCEGUI.Editbox.EventDeactivated,
                                      self.cb_value_changed)
        self.property_input = property_input
        self.update_input_widgets()

    def cb_value_changed(self, args):
        """Called when the text value of a widget was changed

        Args:

            args: PyCEGUI event args
        """
        window = args.window
        new_value = str(window.getText())
        window.setTooltipText(new_value)
        self.editor.send_value_changed(self.section, self.name, new_value)


class ListProperty(BaseProperty):

    """Class for a list property"""

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], list)

    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""
        pass

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self._create_base_widget(root)
        property_edit = self.base_widget.createChild(
            "TaharezLook/Editbox", "%s_edit" % (self.base_text))
        property_edit.setWidth(PyCEGUI.UDim(0.49, 0))
        property_edit.setHeight(self.editor.WIDGET_HEIGHT)
        property_edit.setText("(list)")
        property_edit.setTooltipText("(list)")
        property_edit.setReadOnly(True)

        property_edit.subscribeEvent(
            PyCEGUI.Editbox.EventMouseClick,
            self.cb_mouse_clicked)

    def cb_mouse_clicked(self, args):
        """Called when the text value of a widget was changed

        Args:

            args: PyCEGUI event args
        """
        dialog = ListEditor(self.editor.app, self.value_data[0])
        dialog.show_modal(self.editor.app.editor_gui.editor_window,
                          self.editor.app.engine.pump)
        if not dialog.return_value:
            return
        values = dialog.get_values()
        self.editor.send_value_changed(self.section, self.name,
                                       values["items"])


class SetProperty(BaseProperty):

    """Class for a list property"""

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], set)

    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""
        pass

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self._create_base_widget(root)
        property_edit = self.base_widget.createChild(
            "TaharezLook/Editbox", "%s_edit" % (self.base_text))
        property_edit.setWidth(PyCEGUI.UDim(0.49, 0))
        property_edit.setHeight(self.editor.WIDGET_HEIGHT)
        property_edit.setText("(set)")
        property_edit.setTooltipText("(set)")
        property_edit.setReadOnly(True)

        property_edit.subscribeEvent(
            PyCEGUI.Editbox.EventMouseClick,
            self.cb_mouse_clicked)

    def cb_mouse_clicked(self, args):
        """Called when the text value of a widget was changed

        Args:

            args: PyCEGUI event args
        """
        dialog = SetEditor(self.editor.app, self.value_data[0])
        dialog.show_modal(self.editor.app.editor_gui.editor_window,
                          self.editor.app.engine.pump)
        if not dialog.return_value:
            return
        values = dialog.get_values()
        self.editor.send_value_changed(self.section, self.name,
                                       values["items"])


class DictProperty(BaseProperty):

    """Class for a dict property"""

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], dict)

    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""
        pass

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to
        """
        self._create_base_widget(root)
        property_edit = self.base_widget.createChild(
            "TaharezLook/Editbox", "%s_edit" % (self.base_text))
        property_edit.setWidth(PyCEGUI.UDim(0.49, 0))
        property_edit.setHeight(self.editor.WIDGET_HEIGHT)
        property_edit.setText("(dict)")
        property_edit.setTooltipText("(dict)")
        property_edit.setReadOnly(True)

        property_edit.subscribeEvent(
            PyCEGUI.Editbox.EventMouseClick,
            self.cb_mouse_clicked)

    def cb_mouse_clicked(self, args):
        """Called when the text value of a widget was changed

        Args:

            args: PyCEGUI event args
        """
        dialog = DictEditor(self.editor.app, self.value_data[0])
        dialog.show_modal(self.editor.app.editor_gui.editor_window,
                          self.editor.app.engine.pump)
        if not dialog.return_value:
            return
        values = dialog.get_values()
        self.editor.send_value_changed(self.section, self.name,
                                       values)


class NumberProperty(BaseProperty):

    """Class for a text property"""

    def __init__(self, editor, section, name, value_data):
        BaseProperty.__init__(self, editor, section, name, value_data)
        self.property_input = None

    @classmethod
    def check_type(cls, value_data):
        """Checks if the value_data is of the type this class is for

        Args:

            value_data: The value_data to check

        Returns:
            True if the property can handle the type, False if not
        """
        if len(value_data) != 1:
            return False
        return isinstance(value_data[0], (float, int))

    def update_input_widgets(self):
        """Updates the values of the input widgets to the current data"""
        start_value = self.value_data[0]
        input_modes = PyCEGUI.Spinner.TextInputMode
        input_mode = (input_modes.Integer if isinstance(start_value, int) else
                      input_modes.FloatingPoint)
        self.property_input.setTextInputMode(input_mode)
        self.property_input.setMutedState(True)
        self.property_input.setCurrentValue(start_value)
        self.property_input.setMutedState(False)
        self.property_input.setTooltipText(str(start_value))

    def setup_widget(self, root):
        """Sets up the widget for this property

        Args:

            root: The root widget to which to add the widget to

        """
        self._create_base_widget(root)
        property_input = self.base_widget.createChild(
            "TaharezLook/Spinner", "%s_input" % (self.base_text))
        property_input.setWidth(PyCEGUI.UDim(0.49, 0))
        property_input.setHeight(self.editor.WIDGET_HEIGHT)

        property_input.subscribeEvent(
            PyCEGUI.Spinner.EventValueChanged,
            self.cb_value_changed)
        self.property_input = property_input
        self.update_input_widgets()

    def cb_value_changed(self, args):
        """Called when the text value of a widget was changed

        Args:

            args: PyCEGUI event args
        """
        window = args.window
        input_modes = PyCEGUI.Spinner.TextInputMode
        input_mode = window.getTextInputMode()
        val_type = int if input_mode == input_modes.Integer else float
        new_value = val_type(window.getCurrentValue())
        window.setTooltipText(str(new_value))
        self.editor.send_value_changed(self.section, self.name, new_value)
