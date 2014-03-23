#!/usr/bin/python2.7
# -*- coding: utf-8 -*-

"""
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Séverin Lemaignan

**Copyright(c):**      MakeHuman Team 2001-2014

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

Implements the command-line version of MakeHuman.
"""

from core import G
import guicommon
import log
from human import Human
import files3d
import getpath
import humanmodifier
import material
import proxy

# skeleton imports
import skeleton
from armature.options import ArmatureOptions

import sys
sys.path.append("./plugins")
MhxConfig = (__import__("9_export_mhx", fromlist = ["MhxConfig"])).MhxConfig
MHXExporter = (__import__("9_export_mhx", fromlist = ["mhx_main"])).mhx_main

class ConsoleApp():
    def __init__(self):
        self.selectedHuman = Human(files3d.loadMesh(getpath.getSysDataPath("3dobjs/base.obj"), maxFaces = 5))
        self.log_window = None
        self.splash = None
        self.statusBar = None

    def progress(self, *args, **kwargs):
        pass

def run(args):
    G.app = ConsoleApp()
    human = G.app.selectedHuman

    modifiers = [("macrodetails", "Age"),
                 ("macrodetails", "Gender"),
                 ("macrodetails", "Caucasian"),
                 ("macrodetails", "African"),
                 ("macrodetails", "Asian")]

    # TODO properly construct modifiers if not inited by plugin
    for cat, var in modifiers:
        if '%s/%s' % (cat, var) not in human.modifierNames:
            modifier = humanmodifier.MacroModifier(cat, var)
            modifier.setHuman(human)

    human.setAgeYears(args["age"])

    human.setGender(args["gender"])

    if args["race"] == "caucasian":
        human.setCaucasian(0.9)
    elif args["race"] == "african":
        human.setAfrican(0.9)
    elif args["race"] == "asian":
        human.setAsian(0.9)
    else:
        raise RuntimeError("Unknown race %s. Must be one of [caucasian, african, asian]" % args["race"])


    dominant_gender = "female" if args["gender"] < 0.5 else "male"
    human.material = material.fromFile('data/skins/young_%s_%s/young_%s_%s.mhmat'%(
        args["race"], 
        dominant_gender, 
        args["race"],
        dominant_gender))

    ### Skeleton
    if args["rig"]:
        armature_options = ArmatureOptions()
        descr = armature_options.loadPreset('data/rigs/%s.json' % args["rig"], None)
        # Load skeleton definition from options
        human._skeleton, boneWeights = skeleton.loadRig(armature_options, human.meshData)
        human._skeleton.options = armature_options
        def fn():
            return human._skeleton
        human.getSkeleton = fn

    if args["hairs"]:
        addproxy(human, "data/hair/%s.mhclo" % args["hairs"], "hair")
    if args["lowres"]:
        addproxy(human, "data/proxymeshes/proxy741/proxy741.proxy", "proxymeshes")

    if args["output"]:
        save(human, args["output"])


    # A little debug test
    if 'PyOpenGL' in sys.modules.keys():
        log.warning("Debug test detected that OpenGL libraries were imported in the console version! This indicates bad separation from GUI.")
    if 'PyQt4' in sys.modules.keys():
        log.warning("Debug test detected that Qt libraries were imported in the console version! This indicates bad separation from GUI.")

def save(human, filepath):
    if not filepath.endswith("mhx"):
        raise RuntimeError("Only MHX export is currently supported")

    ## Export
    exportCfg = MhxConfig()
    exportCfg.scale = 0.1
    exportCfg.unit = "meter"
    exportCfg.feetOnGround = True
    exportCfg.useRotationLimits = True
    exportCfg.useRigify = False
    exportCfg.setHuman(human)
    MHXExporter.exportMhx(filepath, exportCfg)

def addproxy(human, mhclofile, type):
    import os
    if not os.path.isfile(mhclofile):
        log.error("Proxy file %s does not exist (%s).", mhclofile, type)
        return

    if type not in ["proxymeshes", "hair"]:
        raise RuntimeError("Unknown proxy type %s" % type)

    _proxy = proxy.readProxyFile(human.meshData,
                                   mhclofile,
                                   type=type.capitalize())

    if type == "proxymeshes":
        human.setProxy(_proxy)
        return

    mesh = files3d.loadMesh(_proxy.obj_file, maxFaces = _proxy.max_pole)
    if not mesh:
        raise RuntimeError("Failed to load proxy mesh %s", _proxy.obj_file)

    mesh.material = _proxy.material
    mesh.priority = _proxy.z_depth           # Set render order

    obj = guicommon.Object(mesh, human.getPosition())
    obj.setRotation(human.getRotation())

    #self.adaptProxyToHuman(_proxy, obj)
    #obj.setSubdivided(human.isSubdivided()) # Copy subdivided state of human


    if type == "hair":
        human.hairProxy = _proxy
        human.hairObj = obj


