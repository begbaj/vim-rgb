# -*- coding: utf-8 -*-
"""
    python3.vim_rgb
    ~~~~~~~~~~~~~~~~

    vim-rgb is a simple python script for managing keyboard leds themes in neovim.
    
    for opergb-python documentation, visit: https://openrgb-python.readthedocs.io/

    :license: GPLv2

    Copyright © 2022 Began Bajrami

    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, see <http://www.gnu.org/licenses/>.
"""

import pynvim
from openrgb import OpenRGBClient
from openrgb.utils import DeviceType
from openrgb.utils import RGBColor

@pynvim.plugin
class VimRGB(object):

    """VimRGB main class"""

    def __init__(self, nvim: pynvim.Nvim):
        """ initialization process """
        self.nvim = nvim
        self.debug = self.nvim.vars["vimrgb_debug"] # TODO: get value from init.vim
        self.theme_name = self.nvim.vars["vimrgb_theme"]

        self.allow_queue = False
        self.updater_is_on = False
        self.print_enabled = False
        self.mode = 'default'
        self.connected = False
        self.leds = []
        self.key_queue = []
        self.is_close = False
        self.can_update = False
        self.cached_layouts = {}



        self.ocli = OpenRGBClient() #openrgb client
        self.keyb = self.ocli.get_devices_by_type(DeviceType.KEYBOARD)[0] #keyboard object, assuming there is only one keyboard plugged
        self.keyb.set_mode('direct') 
        self.vimmode = 'n'

    def refresh(self, mode, force=False):
        pass
    
    def layout_updater(self):
        """
        Actually load current mode layout.
        """
        def nprint(message):
            self.nvim.async_call(self._debug, message)
        nprint("Layout updater launched.")
        if not self.updater_is_on:
            self.updater_is_on = True
            while not self.is_close:
                try:
                    if len(self.key_queue) != 0 and self.can_update:
                        nprint("Loading layout")
                        self.can_update = False
                        leds = self.leds
                        while len(self.key_queue) != 0:

                except Exception as err:
                    nprint("LAYOUT UPDATER STOPPED!!")
                    nprint(f"Error {err} \n {traceback.format_exc()}")
                    self.key_queue = []
            self.updater_is_on = False
        else:
            nprint("WARNING, Updater is already running")

    def set_key_color(self, key, color):
        # from official documentation:
        # red = RGBColor(255, 0, 0)
        # blue = RGBColor.fromHSV(240, 100, 100)
        # green = RGBColor.fromHEX('#00ff00')
        # mobo.set_color(RGBColor(0, 255, 0))
        if len(color) == 3:
            self.keyb.set_colors()
        if len(key) == 1:
            pass
        pass

    def get_layout_by_mode(self, mode):
        """
        Returns a list of colors that Updater can process
        []
        """
        key_layout = []
        self._debug(f"Generating layout for mode {mode}")
        # Check for groupings: if any, compile to g:theme
        keys = self.nvim.vars['vimrgb_keys']
        theme = self.nvim.vars['vimrgb_theme']
        # WORKFLOW EXPLAINED
        # First: check if there are groupings in the theme
        # if so, substitute the grouping with actual keynames contained in the group
        # Second: get layout per mode
        for di in range(len(self.leds)):
            device_leds = self.leds[di]
            for led in device_leds:
                if mode in theme and keys[str(led.value)] in theme[mode]:
                    nl = [theme[mode][keys[str(led.value)]], led, di]
                elif keys[str(led.value)] in theme['default']:
                    nl = [theme['default'][keys[str(led.value)]], led, di]
                elif mode in theme and 'default' in theme[mode]:
                    nl = [theme[mode]['default'], led, di]
                else:
                    nl = [theme['default']['default'], led, di]
                key_layout.append(nl)

        self._debug(f"Layout generated for {mode} mode. This layout contains {len(key_layout)} entries.")
        return key_layout


    def compile_theme(self):
        """
        Compiling is useful when the selected theme is using groupings feature.
        This makes VimRGB more confortable when reading current mode layout.
        """
        self._debug(f"Precompiling theme: {self.theme_name}.")
        if 'groupings' not in theme:
            # there's no need to precompile if there's no grouping in the theme
            return
        
        groupings = self.nvim.vars['vimrgb_theme']['groupings']
        for group in groupings:
                    self._debug(group)
                    for mode in theme:
                        if mode == "groupings":
                            continue
                        for key in theme[mode]:
                            if group == key:
                                for groupkey in groupings[group]:
                                    self._debug(f"MODE: {mode} GROUPKEY: {groupkey} mode_key: {theme[mode][key]}")
                                    if groupkey not in theme[mode] and groupkey not in theme["default"]:
                                        self.nvim.call("VimRGBAddToTheme", mode, groupkey, theme[mode][key])
                                    # self.nvim.vars['vimRGB_theme'][mode][groupkey] = theme[mode][key]
                                self._debug(f"{self.nvim.vars['vimRGB_theme'][mode]}")
        self._debug("Precomipling finished.")

    def cache_layouts(self):  
        """
        Loads layouts to memory for faster access to layout data.
        """
        self._debug("Caching layout...")
        self.cached_layouts = {}
        self.compile_theme()
        for mode in self.nvim.vars['vimrgb_theme'].keys():
            self._debug(f" Caching mode: {mode}")
            self.cached_layouts[mode] = self.__get_layout(mode)
        self._debug("Caching completed.")
        self.allow_queue = True
        self.refresh_forced(self.mode)

    def _debug(self, message, auto_newline=True):
        if self.print_enabled:
                    if auto_newline:
                        self.nvim.call('VimRGBPrintDebug', str(message) + "\n")
                    else:
                        self.nvim.call('VimRGBPrintDebug', str(message))

