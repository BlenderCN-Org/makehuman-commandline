#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Save Tab GUI
============

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Marc Flerackers

**Copyright(c):**      MakeHuman Team 2001-2014

**Licensing:**         AGPL3 (see also http://www.makehuman.org/node/318)

**Coding Standards:**  See http://www.makehuman.org/node/165

Abstract
--------

This module implements the 'Files > Save' tab.
"""

import os

import mh
import gui
import gui3d
from core import G


class SaveTaskView(gui3d.TaskView):
    """Task view for saving MakeHuman model files."""

    def __init__(self, category):
        """SaveTaskView constructor.

        The Save Task view contains a filename entry box at the top,
        and lets the model be displayed in the center,
        accompanied by a square border which the user can utilize
        to create a thumbnail for the saved model.
        """

        gui3d.TaskView.__init__(self, category, 'Save')

        self.fileentry = self.addTopWidget(gui.FileEntryView('Save', mode='save'))
        self.fileentry.setFilter('MakeHuman Models (*.mhm)')

        @self.fileentry.mhEvent
        def onFileSelected(filename):
            self.saveMHM(filename)

    def saveMHM(self, filename):
        """Method that does the saving of the .mhm and the thumbnail once
        the save path is selected."""
        if not filename.lower().endswith('.mhm'):
            filename += '.mhm'

        modelPath = self.fileentry.directory
        if not os.path.exists(modelPath):
            os.makedirs(modelPath)

        path = os.path.normpath(os.path.join(modelPath, filename))
        name = os.path.splitext(filename)[0]

        # Save square sized thumbnail
        size = min(G.windowWidth, G.windowHeight)
        img = mh.grabScreen(
            (G.windowWidth - size) / 2, (G.windowHeight - size) / 2, size, size)

        # Resize thumbnail to max 128x128
        if size > 128:
            img.resize(128, 128)
        img.save(os.path.join(modelPath, name + '.thumb'))

        # Save the model
        G.app.selectedHuman.save(path, name)
        #G.app.clearUndoRedo()

        gui3d.app.prompt('Info', u'Your model has been saved to %s.' % modelPath, 'OK')

    def onShow(self, event):
        """Handler for the TaskView onShow event.
        Once the task view is shown, preset the save directory
        and give focus to the file entry."""
        gui3d.TaskView.onShow(self, event)

        modelPath = G.app.selectedHuman.dir
        if modelPath is None:
            modelPath = mh.getPath("models")

        name = G.app.selectedHuman.filetitle
        if name is None:
            name = ""

        self.fileentry.setDirectory(modelPath)
        self.fileentry.edit.setText(name)
        self.fileentry.setFocus()
