# -*- coding: utf-8 -*-

"""
**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Séverin Lemaignan

**Copyright(c):**      MakeHuman Team 2001-2014

**Licensing:**         AGPL3 (see also http://www.makehuman.org/node/318)

**Coding Standards:**  See http://www.makehuman.org/node/165

Abstract
--------

Implements the command-line version of MakeHuman.
"""

from core import G
import gui3d
from human import Human
import files3d
import mh
import humanmodifier
from humanobjchooser import HumanObjectSelector
import material
import proxy

# skeleton imports
import skeleton
from armature.options import ArmatureOptions

import sys
sys.path.append("./plugins")
ExporterMHX = (__import__("9_export_mhx", fromlist = ["ExporterMHX"])).ExporterMHX

class dummytaskview():
    def enterPoseMode(self):
        pass
    def exitPoseMode(self):
        pass
    def getScale(self):
        return (0.1, "meter")

class dummyselected():
    def __init__(self, value = True):
        self.selected = value

class dummyapp():
    def __init__(self,human):
        self.selectedHuman = human
        self.log_window = None
        self.splash = None
        self.statusBar = None

    def progress(self, *args, **kwargs):
        pass

def run(args):

    human = Human(files3d.loadMesh(mh.getSysDataPath("3dobjs/base.obj"), maxFaces = 5))

    G.app = dummyapp(human)
    gui3d.app = dummyapp(human)

    modifiers = [("macrodetails", "Age"),
                 ("macrodetails", "Gender"),
                 ("macrodetails", "Caucasian"),
                 ("macrodetails", "African"),
                 ("macrodetails", "Asian")]

    for cat, var in modifiers:
        modifier = humanmodifier.MacroModifier(cat, var)
        modifier.setHuman(human)
        human.addModifier(modifier)

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

    save(human, args["output"])

def save(human, filepath):

    if not filepath.endswith("mhx"):
        raise RuntimeError("Only MHX export is currently supported")

    ## Export
    def filename(nop):
        return filepath

    exporter = ExporterMHX()
    exporter.taskview = dummytaskview()
    exporter.feetOnGround = dummyselected(True)
    exporter.useRotationLimits = dummyselected(True)
    exporter.useRigify = dummyselected(False)
    exporter.export(human, filename)

def addproxy(human, mhclofile, type):

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

    obj = gui3d.Object(mesh, human.getPosition())
    obj.setRotation(human.getRotation())

    #self.adaptProxyToHuman(_proxy, obj)
    #obj.setSubdivided(human.isSubdivided()) # Copy subdivided state of human


    if type == "hair":
        human.hairProxy = _proxy
        human.hairObj = obj


