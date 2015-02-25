# -*- coding: utf-8 -*-
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.

#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.

#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

""" Module for creating and handling the editor GUI

.. module:: editor_gui
    :synopsis: Creating and handling the editor menu

.. moduleauthor:: Karsten Bock <KarstenBock@gmx.net>
"""

import os
import PyCEGUI
import yaml

from fife.fife import Rect
from fife.fife import InstanceRenderer
from fife.extensions.serializers.simplexml import (SimpleXMLSerializer,
                                                   InvalidFormat)
from fife.extensions.serializers import ET
from fife_rpg.map import Map as GameMap
from fife_rpg.components import ComponentManager
from fife_rpg import helpers

from .edit_map import MapOptions
from .edit_layer import LayerOptions
from .edit_camera import CameraOptions
from .new_project import NewProject
from .object_toolbar import ObjectToolbar
from .basic_toolbar import BasicToolbar
from .property_editor import PropertyEditor


class EditorGui(object):

    """Creates and handles the editor GUI"""

    def __init__(self, editor):
        if False:
            self.editor_window = PyCEGUI.DefaultWindow()
            self.main_container = PyCEGUI.VerticalLayoutContainer()
            self.menubar = PyCEGUI.Menubar()
            self.toolbar = PyCEGUI.TabControl()
            self.menubar = PyCEGUI.Menubar()
            self.file_menu = PyCEGUI.MenuItem()
            self.view_menu = PyCEGUI.MenuItem()
            self.edit_menu = PyCEGUI.MenuItem()
            self.project_menu = PyCEGUI.MenuItem()
        self.menubar = None
        self.file_menu = None
        self.file_close = None
        self.file_save = None
        self.project_settings = None
        self.edit_menu = None
        self.view_menu = None
        self.view_maps_menu = None
        self.save_maps_popup = None
        self.save_popup = None
        self.save_entities_popup = None
        self.project_menu = None
        self.file_import = None
        self.import_popup = None
        self.edit_add = None
        self.add_popup = None

        self.editor = editor

        cegui_system = PyCEGUI.System.getSingleton()
        cegui_system.getDefaultGUIContext().setDefaultTooltipType(
            "TaharezLook/Tooltip")
        self.load_data()
        window_manager = PyCEGUI.WindowManager.getSingleton()
        self.editor_window = window_manager.loadLayoutFromFile(
            "editor_window.layout")
        self.main_container = self.editor_window.getChild("MainContainer")
        middle_container = self.main_container.getChild("MiddleContainer")
        self.toolbar = middle_container.getChild("Toolbar")
        self.toolbar.subscribeEvent(PyCEGUI.TabControl.EventSelectionChanged,
                                    self.cb_tb_page_changed)
        self.cur_toolbar_index = 0
        right_area = middle_container.getChild("RightArea")
        right_area_container = right_area.createChild(
            "VerticalLayoutContainer",
            "right_area_container")
        layer_box = right_area_container.createChild("TaharezLook/GroupBox",
                                                     "layer_box")
        layer_box.setText("Layers")
        layer_box.setHeight(PyCEGUI.UDim(0.175, 0.0))
        layer_box.setWidth(PyCEGUI.UDim(1.0, 0.0))

        self.listbox = layer_box.createChild("TaharezLook/ItemListbox",
                                             "Listbox")

        self.listbox.setHeight(PyCEGUI.UDim(0.99, 0.0))
        self.listbox.setWidth(PyCEGUI.UDim(0.99, 0.0))
        self.show_agents_check = right_area_container.createChild("TaharezLook"
                                                                  "/Checkbox",
                                                                  "show_agents"
                                                                  )
        self.show_agents_check.setText(_("Show Entities"))
        self.show_agents_check.setSelected(True)
        self.show_agents_check.subscribeEvent(
            PyCEGUI.ToggleButton.EventSelectStateChanged,
            self.cb_show_agent_selection_changed
        )
        property_editor_size = PyCEGUI.USize(PyCEGUI.UDim(1.0, 0),
                                             PyCEGUI.UDim(0.780, 0))
        self.property_editor = PropertyEditor(right_area_container)
        self.property_editor.set_size(property_editor_size)
        self.property_editor.add_value_changed_callback(self.cb_value_changed)

        cegui_system.getDefaultGUIContext().setRootWindow(
            self.editor_window)
        self.toolbars = {}
        self.main_container.layout()
        self.editor.add_project_clear_callback(self.cb_project_cleared)

    @property
    def selected_layer(self):
        """Returns the currently selected layer"""
        selected = self.listbox.getFirstSelectedItem()
        if selected is not None:
            return selected.getText().encode()
        return None

    @property
    def current_toolbar(self):
        """Returns the currently active toolbar"""
        cur_tab = self.toolbar.getTabContentsAtIndex(self.cur_toolbar_index)
        return self.toolbars[cur_tab.getText()]

    def load_data(self):  # pylint: disable=no-self-use
        """Load gui datafiles"""
        PyCEGUI.ImageManager.getSingleton().loadImageset(
            "TaharezLook.imageset")
        PyCEGUI.SchemeManager.getSingleton().createFromFile(
            "TaharezLook.scheme")
        PyCEGUI.FontManager.getSingleton().createFromFile("DejaVuSans-10.font")
        PyCEGUI.FontManager.getSingleton().createFromFile("DejaVuSans-12.font")
        PyCEGUI.FontManager.getSingleton().createFromFile("DejaVuSans-14.font")

    def create_menu(self):
        """Create the menu items"""
        self.menubar = self.main_container.getChild("Menu")
        # File Menu
        self.file_menu = self.menubar.createChild("TaharezLook/MenuItem",
                                                  "File")
        self.file_menu.setText(_("File"))
        self.file_menu.setVerticalAlignment(
            PyCEGUI.VerticalAlignment.VA_CENTRE)
        file_popup = self.file_menu.createChild("TaharezLook/PopupMenu",
                                                "FilePopup")
        file_new = file_popup.createChild("TaharezLook/MenuItem", "FileNew")
        file_new.setText(_("New Project"))
        file_new.subscribeEvent(PyCEGUI.MenuItem.EventClicked, self.cb_new)
        file_open = file_popup.createChild("TaharezLook/MenuItem", "FileOpen")
        file_open.subscribeEvent(PyCEGUI.MenuItem.EventClicked, self.cb_open)
        file_open.setText(_("Open Project"))
        file_import = file_popup.createChild(
            "TaharezLook/MenuItem", "FileImport")
        file_import.setText(_("Import") + "  ")
        file_import.setEnabled(False)
        file_import.setAutoPopupTimeout(0.5)
        self.file_import = file_import
        import_popup = file_import.createChild("TaharezLook/PopupMenu",
                                               "ImportPopup")
        self.import_popup = import_popup
        import_objects = import_popup.createChild("TaharezLook/MenuItem",
                                                  "FileImportObjects")
        import_objects.setText(_("Objects"))
        import_objects.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                                      self.cb_import_objects)
        file_save = file_popup.createChild("TaharezLook/MenuItem", "FileSave")
        file_save.setText(_("Save") + "  ")
        file_save.setEnabled(False)
        file_save.setAutoPopupTimeout(0.5)
        save_popup = file_save.createChild("TaharezLook/PopupMenu",
                                           "SavePopup")
        self.save_popup = save_popup
        save_all = save_popup.createChild("TaharezLook/MenuItem",
                                          "FileSaveAll")
        save_all.setText(_("All"))
        save_all.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                                self.cb_save_all)
        self.file_save = file_save
        save_project = save_popup.createChild("TaharezLook/MenuItem",
                                              "FileSaveProject")
        save_project.setText(_("Project"))
        save_project.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                                    self.cb_save_project)
        save_maps = save_popup.createChild("TaharezLook/MenuItem",
                                           "FileSaveMaps")
        save_maps.setText(_("Maps") + "  ")
        save_maps.setAutoPopupTimeout(0.5)
        save_maps_popup = save_maps.createChild("TaharezLook/PopupMenu",
                                                "SaveMapsPopup")
        self.save_maps_popup = save_maps_popup
        save_entities = save_popup.createChild("TaharezLook/MenuItem",
                                               "FileSaveEntities")
        save_entities.setText(_("Entities"))
        save_entities.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                                     self.cb_save_entities)
        file_close = file_popup.createChild(
            "TaharezLook/MenuItem", "FileClose")
        file_close.subscribeEvent(PyCEGUI.MenuItem.EventClicked, self.cb_close)
        file_close.setText(_("Close Project"))
        file_close.setEnabled(False)
        self.file_close = file_close
        file_quit = file_popup.createChild("TaharezLook/MenuItem", "FileQuit")
        file_quit.setText(_("Quit"))
        file_quit.subscribeEvent(PyCEGUI.MenuItem.EventClicked, self.cb_quit)

        # Edit Menu

        self.edit_menu = self.menubar.createChild("TaharezLook/MenuItem",
                                                  "Edit")
        self.edit_menu.setText(_("Edit"))
        edit_popup = self.edit_menu.createChild("TaharezLook/PopupMenu",
                                                "EditPopup")
        edit_add = edit_popup.createChild("TaharezLook/MenuItem",
                                          "Edit/Add")
        edit_add.setText(_("Add") + "  ")
        add_popup = edit_add.createChild("TaharezLook/PopupMenu",
                                         "Edit/AddPopup")
        self.add_popup = add_popup
        add_map = add_popup.createChild("TaharezLook/MenuItem",
                                        "Edit/Add/Map")
        add_map.setText(_("Map"))
        add_map.subscribeEvent(PyCEGUI.MenuItem.EventClicked, self.cb_add_map)

        self.edit_add = edit_add
        self.edit_add.setEnabled(False)

        # View Menu
        self.view_menu = self.menubar.createChild("TaharezLook/MenuItem",
                                                  "View")
        self.view_menu.setText(_("View"))
        view_popup = self.view_menu.createChild("TaharezLook/PopupMenu",
                                                "ViewPopup")
        view_maps = view_popup.createChild("TaharezLook/MenuItem", "ViewMaps")
        view_maps.setText(_("Maps") + "  ")
        self.view_maps_menu = view_maps.createChild("TaharezLook/PopupMenu",
                                                    "ViewMapsMenu")
        view_maps.setAutoPopupTimeout(0.5)
        self.project_menu = self.menubar.createChild("TaharezLook/MenuItem",
                                                     "Project")
        self.project_menu.setText(_("Project"))
        project_popup = self.project_menu.createChild("TaharezLook/PopupMenu",
                                                      "ProjectPopup")
        project_settings = project_popup.createChild(
            "TaharezLook/MenuItem", "ProjectSettings")
        project_settings.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                                        self.cb_project_settings)
        project_settings.setText(_("Settings"))
        project_settings.setEnabled(False)
        self.project_settings = project_settings

    def reset_layerlist(self):
        """Resets the layerlist to be empty"""
        self.listbox.resetList()

    def update_layerlist(self):
        """Update the layerlist to the layers of the current map"""
        layers = self.editor.current_map.fife_map.getLayers()
        for layer in layers:
            layer_name = layer.getId()
            item = self.listbox.createChild(
                "TaharezLook/CheckListboxItem",
                "layer_%s" % layer_name)
            checkbox = item.getChild(0)
            checkbox.setSelected(True)
            # pylint:disable=cell-var-from-loop
            checkbox.subscribeEvent(
                PyCEGUI.ToggleButton.EventSelectStateChanged,
                lambda args, layer=layer_name:
                    self.cb_layer_checkbox_changed(args, layer))
            # pylint:enable=cell-var-from-loop
            item.setText(layer_name)

    def create_toolbars(self):
        """Creates the editors toolbars"""
        new_toolbar = BasicToolbar(self.editor)
        if new_toolbar.name in self.toolbars:
            raise RuntimeError("Toolbar with name %s already exists" %
                               (new_toolbar.name))
        self.toolbar.setTabHeight(PyCEGUI.UDim(0, -1))
        self.toolbars[new_toolbar.name] = new_toolbar
        gui = new_toolbar.gui
        self.toolbar.addTab(gui)
        new_toolbar = ObjectToolbar(self.editor)
        if new_toolbar.name in self.toolbars:
            raise RuntimeError("Toolbar with name %s already exists" %
                               (new_toolbar.name))
        self.toolbar.setTabHeight(PyCEGUI.UDim(0, -1))
        self.toolbars[new_toolbar.name] = new_toolbar
        gui = new_toolbar.gui
        self.toolbar.addTab(gui)
        self.toolbar.setSelectedTabAtIndex(0)

    def update_toolbar_contents(self):
        """Updates the contents of the toolbars"""
        for toolbar in self.toolbars.itervalues():
            toolbar.update_contents()

    def update_property_editor(self):
        """Update the property editor"""
        property_editor = self.property_editor
        property_editor.clear_properties()
        identifier = self.editor.selected_object.getId()
        world = self.editor.world
        components = ComponentManager.get_components()
        if world.is_identifier_used(identifier):
            entity = world.get_entity(identifier)
            for comp_name, component in components.iteritems():
                com_data = getattr(entity, comp_name)
                if com_data:
                    for field in component.saveable_fields:
                        value = getattr(com_data, field)
                        if isinstance(value, helpers.DoublePointYaml):
                            pos = (value.x, value.y)
                            property_editor.add_property(
                                comp_name, field,
                                ("point", pos))
                        elif isinstance(value, helpers.DoublePoint3DYaml):
                            pos = (value.x, value.y, value.z)
                            property_editor.add_property(
                                comp_name, field,
                                ("point3d", pos))
                        else:
                            str_val = yaml.dump(value).split('\n')[0]
                            property_editor.add_property(
                                comp_name, field,
                                ("text", str_val))
        else:
            property_editor.add_property(
                "Instance", "Identifier",
                ("text", identifier))
            property_editor.add_property(
                "Instance", "CostId",
                ("text", self.editor.selected_object.getCostId()))
            property_editor.add_property(
                "Instance", "Cost",
                ("text", self.editor.selected_object.getCost()))
            property_editor.add_property(
                "Instance", "Blocking",
                ("check", self.editor.selected_object.isBlocking()))
            property_editor.add_property(
                "Instance", "Rotation",
                ("text", self.editor.selected_object.getRotation()))
            visual = self.editor.selected_object.get2dGfxVisual()
            property_editor.add_property(
                "Instance", "StackPosition",
                ("text",  visual.getStackPosition()))

    def reset_maps_menu(self):
        """Recreate the view->maps menu"""
        menu = self.view_maps_menu
        menu.resetList()
        item = menu.createChild("TaharezLook/MenuItem", "NoMap")
        item.setUserData(None)
        item.subscribeEvent(PyCEGUI.MenuItem.EventClicked, self.cb_map_switch)
        if self.editor.current_map is None:
            item.setText("+" + _("No Map"))
        else:
            item.setText("   " + _("No Map"))
        self.save_maps_popup.resetList()
        item = self.save_maps_popup.createChild("TaharezLook/MenuItem",
                                                "All")
        item.setText(_("All"))
        item.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                            self.cb_save_maps_all)
        for game_map in self.editor.maps.iterkeys():
            item = menu.createChild("TaharezLook/MenuItem", game_map)
            item.setUserData(game_map)
            item.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                                self.cb_map_switch)
            if (self.editor.current_map is not None and
                    self.editor.current_map.name is game_map):
                item.setText("+" + game_map)
            else:
                item.setText("   " + game_map)
            item = self.save_maps_popup.createChild("TaharezLook/MenuItem",
                                                    game_map)
            item.setText(game_map)
            item.setUserData(game_map)
            item.subscribeEvent(PyCEGUI.MenuItem.EventClicked,
                                self.cb_save_map)

    def cb_tb_page_changed(self, args):
        """Called then the toolbar page gets changed"""
        old_tab = self.toolbar.getTabContentsAtIndex(self.cur_toolbar_index)
        old_toolbar = self.toolbars[old_tab.getText()]
        old_toolbar.deactivate()
        index = self.toolbar.getSelectedTabIndex()
        new_tab = self.toolbar.getTabContentsAtIndex(index)
        new_toolbar = self.toolbars[new_tab.getText()]
        new_toolbar.activate()
        self.cur_toolbar_index = index

    def cb_layer_checkbox_changed(self, args, layer_name):
        """Called when a layer checkbox state was changed

        Args:
            layer_name: Name of the layer the checkbox is for
        """
        layer = self.editor.current_map.fife_map.getLayer(layer_name)
        is_selected = args.window.isSelected()
        layer.setInstancesVisible(is_selected)

    def cb_quit(self, args):
        """Callback when quit was clicked in the file menu"""
        self.editor.quit()

    def cb_close(self, args):
        """Callback when close was clicked in the file menu"""
        # TODO: Ask to save project/files
        self.editor.clear()

    def cb_new(self, args):
        """Callback when new was clicked in the file menu"""
        import Tkinter
        import tkMessageBox
        window = Tkinter.Tk()
        window.wm_withdraw()
        dialog = NewProject(self)
        values = dialog.show_modal(self.editor.editor_window,
                                   self.editor.engine.pump)
        if not dialog.return_value:
            return
        new_project_path = values["ProjectPath"]
        settings_path = os.path.join(new_project_path, "settings-dist.xml")
        if (os.path.exists(settings_path)
                or os.path.exists(os.path.join(new_project_path,
                                               "settings.xml"))):
            answer = tkMessageBox.askyesno(
                _("Project file exists"),
                _("There is already a settings.xml or settings-dist.xml file. "
                  "If you create a new project the settings-dist.xml will "
                  "be overwritten. If you want to convert a project open it "
                  "instead. Continue with creating a new project?"))
            if not answer:
                return
            os.remove(settings_path)
        self.editor.new_project(settings_path, values)

    def cb_save_all(self, args):
        """Callback when save->all was clicked in the file menu"""
        self.editor.project.save()
        self.editor.save_all_maps()
        self.editor.save_entities()
        self.save_popup.closePopupMenu()

    def cb_save_project(self, args):
        """Callback when save->project was clicked in the file menu"""
        self.editor.project.save()
        self.save_popup.closePopupMenu()

    def cb_save_maps_all(self, args):
        """Callback when save->maps->all was clicked in the file menu"""
        self.editor.save_all_maps()
        self.save_popup.closePopupMenu()
        self.save_maps_popup.closePopupMenu()

    def cb_save_map(self, args):
        """Callback when save->maps->map_name was clicked in the file menu"""
        map_name = args.window.getUserData()
        self.editor.save_map(map_name)
        self.save_popup.closePopupMenu()
        self.save_maps_popup.closePopupMenu()

    def cb_save_entities(self, args):
        """Callback when save->entities was clicked in the file menu"""
        self.editor.save_entities()

    def cb_open(self, args):
        """Callback when open was clicked in the file menu"""
        import Tkinter
        import tkFileDialog
        import tkMessageBox
        window = Tkinter.Tk()
        window.wm_withdraw()
        # Based on code from unknown-horizons
        try:
            selected_file = tkFileDialog.askopenfilename(
                filetypes=[("fife-rpg project", ".xml",)],
                title="Open project")
        except ImportError:
            # tkinter may be missing
            selected_file = ""
        if selected_file:
            loaded = self.editor.try_load_project(selected_file)
            if not loaded:
                project = SimpleXMLSerializer(selected_file)
                try:
                    project.load()
                except (InvalidFormat, ET.ParseError):
                    print _("%s is not a valid fife or fife-rpg project" %
                            selected_file)
                    return
                answer = tkMessageBox.askyesno(
                    _("Convert project"),
                    _("%s is not a fife-rpg project. Convert it? " %
                      selected_file))
                if not answer:
                    return
                bak_file = self.editor.convert_fife_project(selected_file)
                if not self.editor.try_load_project(selected_file):
                    tkMessageBox.showerror("Load Error",
                                           "There was a problem loading the "
                                           "converted project. Reverting. "
                                           "Converted file will be stored as "
                                           "original_file.converted")
                    conv_file = "%s.converted" % selected_file
                    if os.path.exists(conv_file):
                        os.remove(conv_file)
                    os.rename(selected_file, conv_file)
                    os.rename(bak_file, selected_file)

            self.file_close.setEnabled(True)
            self.file_save.setEnabled(True)
            self.file_import.setEnabled(True)
            self.project_settings.setEnabled(True)
            self.edit_add.setEnabled(True)

            tkMessageBox.showinfo(_("Project loaded"),
                                  _("Project successfully loaded"))

    def cb_project_settings(self, args):
        """Callback when project settings was clicked in the file menu"""
        self.editor.edit_project_settings(self.editor.project_dir,
                                          self.editor.project)

    def cb_map_switch(self, args):
        """Callback when a map from the menu was clicked"""
        self.view_maps_menu.closePopupMenu()
        self.editor.switch_map(args.window.getUserData())
        self.reset_maps_menu()

    def cb_import_objects(self, args):
        """Callback when objects was clicked in the file->import menu"""
        self.import_popup.closePopupMenu()
        import Tkinter
        import tkFileDialog
        window = Tkinter.Tk()
        window.wm_withdraw()

        # Based on code from unknown-horizons
        try:
            selected_file = tkFileDialog.askopenfilename(
                filetypes=[("fife object definition", ".xml",)],
                initialdir=self.editor.project_dir,
                title="import objects")
        except ImportError:
            # tkinter may be missing
            selected_file = ""

        if selected_file:
            selected_file = os.path.relpath(selected_file,
                                            self.editor.project_dir)
            self.editor.import_object(selected_file)

    def cb_add_map(self, args):
        """Callback when Map was clicked in the edit->Add menu"""
        import Tkinter
        import tkMessageBox

        self.add_popup.closePopupMenu()
        dialog = MapOptions(self)
        values = dialog.show_modal(self.editor.editor_window,
                                   self.editor.engine.pump)
        if not dialog.return_value:
            return
        map_name = values["MapName"]
        model = self.editor.engine.getModel()
        fife_map = None
        try:
            fife_map = model.createMap(map_name)
        except RuntimeError as error:
            window = Tkinter.Tk()
            window.wm_withdraw()
            tkMessageBox.showerror("Could not create map",
                                   "Creation of the map failed with the "
                                   "following FIFE Error: %s" % str(error))
            return
        grid_types = ["square", "hexagonal"]
        dialog = LayerOptions(self, grid_types)
        values = dialog.show_modal(self.editor.editor_window,
                                   self.editor.engine.pump)
        if not dialog.return_value:
            model.deleteMap(fife_map)
            return

        layer_name = values["LayerName"]

        cell_grid = model.getCellGrid(values["GridType"])
        layer = fife_map.createLayer(layer_name, cell_grid)

        resolution = self.editor.settings.get("FIFE", "ScreenResolution",
                                              "1024x768")
        width, height = [int(s) for s in resolution.lower().split("x")]
        viewport = Rect(0, 0, width, height)

        camera_name = self.editor.settings.get(
            "fife-rpg", "Camera", "main")
        camera = fife_map.addCamera(camera_name, layer, viewport)

        dialog = CameraOptions(self, camera)
        values = dialog.show_modal(self.editor.editor_window,
                                   self.editor.engine.pump)
        if not dialog.return_value:
            model.deleteMap(fife_map)
            return
        camera.setId(values["CameraName"])
        camera.setViewPort(values["ViewPort"])
        camera.setRotation(values["Rotation"])
        camera.setTilt(values["Tilt"])
        cid = values["CellImageDimensions"]
        camera.setCellImageDimensions(cid.x, cid.y)
        renderer = InstanceRenderer.getInstance(camera)
        renderer.activateAllLayers(fife_map)
        game_map = GameMap(fife_map, map_name, camera_name, {}, self)

        self.editor.add_map(map_name, game_map)
        self.reset_maps_menu()

    def cb_project_cleared(self):
        """Called when the project was cleared"""
        self.file_save.setEnabled(False)
        self.file_import.setEnabled(False)
        self.file_close.setEnabled(False)
        self.project_settings.setEnabled(False)
        self.edit_add.setEnabled(False)
        self.view_maps_menu.closePopupMenu()
        self.save_popup.closePopupMenu()
        self.import_popup.closePopupMenu()
        self.save_maps_popup.closePopupMenu()
        self.reset_maps_menu()

    def cb_show_agent_selection_changed(self, args):
        """Called when the "Show Entities" checkbox was changed"""
        if self.editor.current_map is None:
            return
        if self.show_agents_check.isSelected():
            self.editor.show_map_entities(self.editor.current_map.name)
        else:
            self.editor.hide_map_entities(self.editor.current_map.name)

    def cb_value_changed(self, section, property_name, value):
        """Called when the value of a property changed

        Args:

            section: The section of the property

            property_name: The name of the property

            value: The new value of the property
        """
        identifier = self.editor.selected_object.getId()
        world = self.editor.world
        if world.is_identifier_used(identifier):
            entity = world.get_entity(identifier)
            com_data = getattr(entity, section)
            try:
                if isinstance(value, basestring):
                    value = yaml.load(value)
                setattr(com_data, property_name, value)
                self.editor.update_agents(self.editor.current_map)
            except (ValueError, yaml.parser.ParserError):
                pass
        else:
            if section != "Instance":
                return
            if property_name == "Identifier":
                self.editor.selected_object.setId(value)
            elif property_name == "CostId":
                cur_cost = self.editor.selected_object.getCost()
                try:
                    value = value.encode()
                    self.editor.selected_object.setCost(value, cur_cost)
                except UnicodeEncodeError:
                    print "The CostId has to be an ascii value"
            elif property_name == "Cost":
                cur_cost_id = self.editor.selected_object.getCostId()
                try:
                    self.editor.selected_object.setCost(cur_cost_id,
                                                        float(value))
                except ValueError:
                    pass
            elif property_name == "Blocking":
                self.editor.selected_object.setBlocking(value)
            elif property_name == "Rotation":
                try:
                    self.editor.selected_object.setRotation(int(value))
                except ValueError:
                    pass
            elif property_name == "StackPosition":
                try:
                    visual = self.editor.selected_object.get2dGfxVisual()
                    visual.setStackPosition(int(value))
                except ValueError:
                    pass
        self.update_property_editor()