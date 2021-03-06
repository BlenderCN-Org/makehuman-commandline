#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Manuel Bastioni, Jonas Hauquier

**Copyright(c):**      MakeHuman Team 2001-2015

**Licensing:**         AGPL3 (http://www.makehuman.org/doc/node/the_makehuman_application.html)

    This file is part of MakeHuman (www.makehuman.org).

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as
    published by the Free Software Foundation, either version 3 of the
    License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

**Coding Standards:**  See http://www.makehuman.org/node/165

Abstract
--------

TODO
"""

import algos3d
import gui3d
import animation
import bvh
import modifierslider
from core import G
import gui
import getpath
import json
import log

# TODO extract a common base class from this and modifierslider (and probably humanmodifier)
'''
class ExpressionSlider(gui.Slider):

    def __init__(self, name):
        super(ExpressionSlider, self).__init__(label=name, min=0.0, max=1.0)
        self.eventType = 'expression'

    def mousePressEvent(self, event):
        if self._handleMousePress(event):
            super(modifierslider.ModifierSlider, self).mousePressEvent(event)

    def sliderMousePressEvent(self, event):
        return self._handleMousePress(event)

    def _handleMousePress(self, event):
        if event.button() == gui.QtCore.Qt.RightButton:
            self.resetValue()
            return False
        else:
            # Default behaviour
            return True

    def onChanging(self, value):
        if self.changing is not None:
            # Avoid concurrent updates
            self.changing = value
            return
        self.changing = value
        G.app.callAsync(self._onChanging)

    def _onChanging(self):
        value = self.changing
        self.changing = None

        if G.app.getSetting('realtimeUpdates'):
            human = G.app.selectedHuman
            if self.value is None:
                self.value = self.modifier.getValue()
                if human.isSubdivided():
                    if human.isProxied():
                        human.getProxyMesh().setVisibility(1)
                    else:
                        human.getSeedMesh().setVisibility(1)
                    human.getSubdivisionMesh(False).setVisibility(0)
            self.modifier.updateValue(value, G.app.getSetting('realtimeNormalUpdates'))
            human.updateProxyMesh(fit_to_posed=True)


    def onChange(self, value):
        pass

    def _onChange(self):
        if self.slider.isSliderDown():
            # Don't do anything when slider is being clicked or dragged (onRelease triggers it)
            return

        value = self.getValue()
        human = self.modifier.human
        if self.value is None:
            self.value = self.modifier.getValue()
        if self.value != value:
            G.app.do(ExpressionAction(self.modifier, self.value, value, self.update))
        else:
            # Indicate that onChanging event is ended with onChanged event (type == 'modifier', not 'targets')
            import events3d
            event = events3d.HumanEvent(human, self.modifier.eventType)
            event.modifier = self.modifier.fullName
            human.callEvent('onChanged', event)
        if human.isSubdivided():
            if human.isProxied():
                human.getProxyMesh().setVisibility(0)
            else:
                human.getSeedMesh().setVisibility(0)
            human.getSubdivisionMesh(False).setVisibility(1)
        self.value = None

    def onRelease(self, w):
        G.app.callAsync(self._onChange)

    def onFocus(self, event):
        if self.view:
            if G.app.getSetting('cameraAutoZoom'):
                self.view()

    def update(self):
        """Synchronize slider value with value of its modifier, make it up to
        date.
        """
        human = self.modifier.modifier
        self.blockSignals(True)
        if not self.slider.isSliderDown():
            # Only update slider position when it is not being clicked or dragged
            self.setValue(self.modifier.getValue())
        self.blockSignals(False)
'''



class ExpressionAction(gui3d.Action):

    def __init__(self, human, filename, taskView, include):
        super(ExpressionAction, self).__init__('Load expression')
        self.human = human
        self.filename = filename
        self.taskView = taskView
        self.include = include
        self.before = {}

        for name, modifier in self.taskView.modifiers.iteritems():
            self.before[name] = modifier.getValue()

    def do(self):
        task = self.taskView
        task.resetTargets()
        task.loadExpression(self.filename, self.include)
        self.human.applyAllTargets(gui3d.app.progress, True)
        for name in task.modifiers:
            modifier = task.modifiers[name]
            for target in modifier.targets:
                task.addTarget(target)
        for slider in task.sliders:
            slider.update()
        return True

    def undo(self):
        task = self.taskView
        task.resetTargets()
        for name, value in self.before.iteritems():
            modifier = task.modifiers[name]
            modifier.setValue(value)
            task.addTarget(modifier.target)
        self.human.applyAllTargets(gui3d.app.progress, True)
        for slider in task.sliders:
            slider.update()
        return True

# TODO make right click reset slider to 0
class ExprSlider(gui.Slider):

    def __init__(self, posename):
        super(ExprSlider, self).__init__(label=posename.capitalize(), min=0.0, max=1.0)
        self.posename = posename
        self.eventType = 'expression'

    def _changed(self, value):
        #print 'caller', self
        self.callEvent('onChange', self)
        # TODO temporary
        taskView = gui3d.app.getTask(0, 'Expressions')
        print json.dumps(dict([(m,v) for m, v in taskView.modifiers.iteritems() if v != 0]))

    def _changing(self, value):
        value = self._i2f(value)
        self._sync(value)
        self.changingValue = value
        self.callEvent('onChanging', self)


class ExpressionTaskView(gui3d.TaskView):

    def __init__(self, category):
        gui3d.TaskView.__init__(self, category, 'Expressions')

        self.human = gui3d.app.selectedHuman

        # TODO defer loading to first onShow()
        bvhfile = bvh.load(getpath.getSysDataPath('poseunits/face-poseunits.bvh'), allowTranslation="none")
        self.base_bvh = bvhfile

        from collections import OrderedDict
        poseunit_json = json.load(open(getpath.getSysDataPath('poseunits/face-poseunits.json'),'rb'), object_pairs_hook=OrderedDict)
        self.poseunit_names = poseunit_json['framemapping']

        self.sliders = []
        self.modifiers = dict(zip(self.poseunit_names, len(self.poseunit_names)*[0.0]))


    def updateGui(self):
        # Create box
        box = self.addLeftWidget(gui.SliderBox("Expressions"))
        # Create sliders
        for posename in self.poseunit_names:
            slider = box.addWidget(ExprSlider(posename))
            @slider.mhEvent
            def onChange(event):
                slider = event
                self.modifiers[slider.posename] = slider.getValue()
                self.updatePose()

            @slider.mhEvent
            def onChanging(event):
                slider = event
                self.modifiers[slider.posename] = slider.changingValue
                self.updatePose()

            self.sliders.append(slider)

        for slider in self.sliders:
            slider.update()

    def updatePose(self):
        posenames = []
        posevalues = []
        for pname,pval in self.modifiers.items():
            if pval != 0:
                posenames.append(pname)
                posevalues.append(pval)
        if len(posenames) == 0:
            return

        panim = self.base_poseunit.getBlendedPose(posenames, posevalues)
        panim.disableBaking = True  # Faster for realtime updating a single pose
        self.human.addAnimation(panim)
        self.human.setActiveAnimation(panim.name)
        self.human.refreshPose()

    def onShow(self, event):
        gui3d.TaskView.onShow(self, event)

        anim = self.base_bvh.createAnimationTrack(self.human.getBaseSkeleton(), name="Expression-Face-PoseUnits")
        log.message('unit pose frame count:%s', len(self.poseunit_names))
        self.base_poseunit = animation.PoseUnit(anim.name, anim.data[:anim.nBones*len(self.poseunit_names)], self.poseunit_names)

        self.updateGui()

        if gui3d.app.getSetting('cameraAutoZoom'):
            gui3d.app.setFaceCamera()


    def onHumanChanging(self, event):
        if event.change not in ['expression', 'material']:
            self.resetTargets()


    def resetTargets(self):
        return

        #log.debug("EXPRESSION RESET %d targets" % len(self.targets))
        if self.targets:
            human = gui3d.app.selectedHuman
            for target in self.targets:
                human.setDetail(target, 0)
            try:
                del algos3d._targetBuffer[target]
            except KeyError:
                pass
            self.targets = {}
            human.applyAllTargets()


    def onHumanChanged(self, event):
        # TODO reset?
        for slider in self.sliders:
            slider.update()


    def loadHandler(self, human, values, strict):
        if values[0] == 'status':
            return

        if values[0] == 'expression' and len(values) > 1:
            # TODO catch error when expression does not exist
            modifier = self.modifiers.get(values[1], None)
            if modifier:
                value = float(values[2])
                modifier.setValue(value)
                modifier.updateValue(value)  # Force recompilation


    def saveHandler(self, human, file):
        pass

    def loadExpression(self, filename, include):
        pass


# This method is called when the plugin is loaded into makehuman
# The app reference is passed so that a plugin can attach a new category, task, or other GUI elements

def load(app):
    category = app.getCategory('Pose/Animate')
    expressionChooser = ExpressionTaskView(category)
    expressionChooser.sortOrder = 4
    category.addTask(expressionChooser)

    app.addLoadHandler('expression', expressionChooser.loadHandler)
    app.addSaveHandler(expressionChooser.saveHandler)

    # TODO
    '''
    visemeView = VisemeLoadTaskView(category, expressionTuning)
    visemeView.sortOrder = 9
    category.addTask(visemeView)
    '''


# This method is called when the plugin is unloaded from makehuman
# At the moment this is not used, but in the future it will remove the added GUI elements

def unload(app):
    pass
