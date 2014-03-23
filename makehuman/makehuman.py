#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

"""
MakeHuman python entry-point.

**Project Name:**      MakeHuman

**Product Home Page:** http://www.makehuman.org/

**Code Home Page:**    https://bitbucket.org/MakeHuman/makehuman/

**Authors:**           Glynn Clements, Joel Palmius, Jonas Hauquier

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

This file starts the MakeHuman python application.
"""

from __future__ import absolute_import  # Fix 'from . import x' statements on python 2.6
import sys
import os
import re
import subprocess

## Version information #########################################################
version = [1, 0, 0]                     # Major, minor and patch version number
release = False                         # False for nightly
versionSub = ""                         # Short version description
meshVersion = "hm08"                    # Version identifier of the basemesh
################################################################################

def getVersionDigitsStr():
    """
    String representation of the version number only (no additional info)
    """
    return ".".join( [str(v) for v in version] )

def _versionStr():
    if versionSub:
        return getVersionDigitsStr() + " " + versionSub
    else:
        return getVersionDigitsStr()

def isRelease():
    """
    True when release version, False for nightly (dev) build
    """
    return release

def isBuild():
    """
    Determine whether the app is frozen using pyinstaller/py2app.
    Returns True when this is a release or nightly build (eg. it is build as a
    distributable package), returns False if it is a source checkout.
    """
    return getattr(sys, 'frozen', False)

def getVersion():
    """
    Comparable version as list of ints
    """
    return version

def getVersionStr(verbose=True):
    """
    Verbose version as string, for displaying and information
    """
    if isRelease():
        return _versionStr()
    else:
        if 'HGREVISION' not in os.environ:
            get_hg_revision()
        result = _versionStr() + " (r%s %s)" % (os.environ['HGREVISION'], os.environ['HGNODEID'])
        if verbose:
            result += (" [%s]" % os.environ['HGREVISION_SOURCE'])
        return result

def getShortVersion():
    """
    Useful for tagging assets
    """
    if versionSub:
        return versionSub.replace(' ', '_').lower()
    else:
        return "v" + getVersionDigitsStr()

def getBasemeshVersion():
    """
    Version of the human basemesh
    """
    return meshVersion

def getCwd():
    """
    Retrieve the folder where makehuman.py or makehuman.exe is located.
    This is not necessarily the CWD (current working directory), but it is what
    the CWD should be.
    """
    if isBuild():
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.realpath(__file__))

def getHgRoot(subpath=''):
    cwd = getCwd()
    return os.path.realpath(os.path.join(cwd, '..', subpath))

def get_revision_hg_info():
    # Return local revision number of hg tip
    hgRoot = getHgRoot()
    output = subprocess.Popen(["hg","-q","tip","--template","{rev}:{node|short}"], stdout=subprocess.PIPE, stderr=sys.stderr, cwd=hgRoot).communicate()[0]
    output = output.strip().split(':')
    rev = output[0].strip().replace('+', '')
    revid = output[1].strip().replace('+', '')
    try:
        branch = subprocess.Popen(["hg","-q","branch"], stdout=subprocess.PIPE, stderr=sys.stderr, cwd=hgRoot).communicate()[0].replace('\n','').strip()
    except:
        branch = None
    return (rev, revid, branch)

def get_revision_entries(folder=None):
    # First fallback: try to parse the files in .hg manually
    cachefile = open(getHgRoot('.hg/cache/tags'), 'r')
    for line in iter(cachefile):
        if line == "\n":
            break
        line = line.split()
        rev = int(line[0].strip())
        nodeid = line[1].strip()
        nodeid_short = nodeid[:12]
        # Tip is at the top of the file
        return (str(rev), nodeid_short)
    raise RuntimeError("No tip revision found in tags cache file")

def get_revision_hglib():
    # The following only works if python-hglib is installed.
    import hglib
    hgclient = hglib.open(getHgRoot())
    tip = hgclient.tip()
    branch = hgclient.branch()
    return (tip.rev.replace('+',''), tip.node[:12], branch)

def get_revision_file():
    # Default fallback to use if we can't figure out HG revision in any other
    # way: Use this file's hg revision.
    pattern = re.compile(r'[^0-9]')
    return pattern.sub("", "$Revision: 6893 $")

def get_hg_revision_1():
    """
    Retrieve (local) revision number and short nodeId for current tip.
    """
    hgrev = None

    try:
        hgrev = get_revision_hg_info()
        os.environ['HGREVISION_SOURCE'] = "hg tip command"
        os.environ['HGREVISION'] = str(hgrev[0])
        os.environ['HGNODEID'] = str(hgrev[1])
        if hgrev[2]:
            os.environ['HGBRANCH'] = hgrev[2]
        return hgrev
    except Exception as e:
        print >> sys.stderr,  "NOTICE: Failed to get hg version number from command line: " + format(str(e)) + " (This is just a head's up, not a critical error)"

    try:
        hgrev = get_revision_hglib()
        os.environ['HGREVISION_SOURCE'] = "python-hglib"
        os.environ['HGREVISION'] = str(hgrev[0])
        os.environ['HGNODEID'] = str(hgrev[1])
        if hgrev[2]:
            os.environ['HGBRANCH'] = hgrev[2]
        return hgrev
    except Exception as e:
        print >> sys.stderr,  "NOTICE: Failed to get hg version number using hglib: " + format(str(e)) + " (This is just a head's up, not a critical error)"

    try:
        hgrev = get_revision_entries()
        os.environ['HGREVISION_SOURCE'] = ".hg cache file"
        os.environ['HGREVISION'] = str(hgrev[0])
        os.environ['HGNODEID'] = str(hgrev[1])
        return hgrev
    except Exception as e:
        print >> sys.stderr,  "NOTICE: Failed to get hg version from file: " + format(str(e)) + " (This is just a head's up, not a critical error)"

    #TODO Disabled this fallback for now, it's possible to do this using the hg keyword extension, but not recommended and this metric was never really reliable (it only caused more confusion)
    '''
    print >> sys.stderr,  "NOTICE: Using HG rev from file stamp. This is likely outdated, so the number in the title bar might be off by a few commits."
    hgrev = get_revision_file()
    os.environ['HGREVISION_SOURCE'] = "approximated from file stamp"
    os.environ['HGREVISION'] = hgrev[0]
    os.environ['HGNODEID'] = hgrev[1]
    return hgrev
    '''

    if hgrev is None:
        rev = "?"
        revid = "UNKNOWN"
    else:
        rev, revid = hgrev
    os.environ['HGREVISION_SOURCE'] = "none found"
    os.environ['HGREVISION'] = str(rev)
    os.environ['HGNODEID'] = str(revid)

    return hgrev

def get_hg_revision():
    # Use the data/VERSION file if it exists. This is created and managed by build scripts
    import getpath
    versionFile = getpath.getSysDataPath("VERSION")
    if os.path.exists(versionFile):
        version_ = open(versionFile).read().strip()
        print >> sys.stderr,  "data/VERSION file detected using value from version file: %s" % version_
        os.environ['HGREVISION'] = str(version_.split(':')[0])
        os.environ['HGNODEID'] = str(version_.split(':')[1])
        os.environ['HGREVISION_SOURCE'] = "data/VERSION static revision data"
    elif not isBuild():
        print >> sys.stderr,  "NO VERSION file detected retrieving revision info from HG"
        # Set HG rev in environment so it can be used elsewhere
        hgrev = get_hg_revision_1()
        print >> sys.stderr,  "Detected HG revision: r%s (%s)" % (hgrev[0], hgrev[1])
    else:
        # Don't bother trying to retrieve HG info for a build release, there should be a data/VERSION file
        os.environ['HGREVISION'] = ""
        os.environ['HGNODEID'] = ""
        os.environ['HGREVISION_SOURCE'] = "skipped for build"

    return (os.environ['HGREVISION'], os.environ['HGNODEID'])
    
def set_sys_path():
    """
    Append local module folders to python search path.
    """
    #[BAL 07/11/2013] make sure we're in the right directory
    if sys.platform != 'darwin':
        os.chdir(sys.path[0])
    syspath = ["./", "./lib", "./apps", "./shared", "./apps/gui","./core"]
    syspath.extend(sys.path)
    sys.path = syspath

stdout_filename = None
stderr_filename = None

def get_platform_paths():
    global stdout_filename, stderr_filename
    import getpath

    home = getpath.getPath()

    if sys.platform == 'win32':
        stdout_filename = os.path.join(home, "python_out.txt")
        stderr_filename = os.path.join(home, "python_err.txt")

    elif sys.platform.startswith("darwin"):
        stdout_filename = os.path.join(home, "makehuman-output.txt")
        stderr_filename = os.path.join(home, "makehuman-error.txt")

def redirect_standard_streams():
    if stdout_filename:
        sys.stdout = open(stdout_filename, "w")
    if stderr_filename:
        sys.stderr = open(stderr_filename, "w")

def close_standard_streams():
    sys.stdout.close()
    sys.stderr.close()

def make_user_dir():
    """
    Make sure MakeHuman folder storing per-user files exists.
    """
    import getpath
    userDir = getpath.getPath()
    if not os.path.isdir(userDir):
        os.makedirs(userDir)
    userDataDir = getpath.getPath('data')
    if not os.path.isdir(userDataDir):
        os.makedirs(userDataDir)

def init_logging():
    import log
    log.init()
    log.message('Initialized logging')
    
def debug_dump():
    try:
        import debugdump
        debugdump.dump.reset()
    except debugdump.DependencyError as e:
        print >> sys.stderr,  "Dependency error: " + format(str(e))
        import log
        log.error("Dependency error: %s", e)
        sys.exit(-1)
    except Exception as _:
        import log
        log.error("Could not create debug dump", exc_info=True)

def parse_arguments():
    if len(sys.argv) < 2:
        return dict()

    while 'endcommand' in sys.argv:
        sys.argv.remove('endcommand')

    # Hack around the limitations of argparse:
    # endcommand is needed because argparse does not allow optional subcommands
    # --ignoreMe is Needed in case --clothes is the final arg, (which consumes 
    # all strings until something with -- is found, so it does not consume the
    # subcommand 'endcommand').
    #sys.argv.extend(['--ignoreMe', 'nothing', 'endcommand'])
    print sys.argv

    import argparse    # requires python >= 2.7
    parser = argparse.ArgumentParser(description="MakeHuman, an open source tool for making 3D characters", epilog="MakeHuman - http://www.makehuman.org")

    # Input argument
    # Can no longer be an optional positional argument as this conflicts with subcommands
    inputGroup = parser.add_argument_group('Input file', description="Specify an input file to load the human from")
    inputGroup.add_argument("-i","--inputMhm", metavar="mhmFile", default=None, nargs='?', help="Load human from .mhm file (optional)")

    # optional arguments
    parser.add_argument('-v', '--version', action='version', version=getVersionStr())
    parser.add_argument("--ignoreMe", default=None, metavar="ignoreThis", help=argparse.SUPPRESS)

    # headless options
    headlessGroup = parser.add_argument_group('Headless options', description="Result in no-GUI mode operation")
    headlessGroup.add_argument("-o", "--output", default=None, nargs='?', help="File to export to, extension determines format. If set, no GUI is started.")

    # Debug options
    debugGroup = parser.add_argument_group('Debug options', description="For testing, debugging and problem solving")
    debugGroup.add_argument("--noshaders", action="store_true", help="disable shaders")
    debugGroup.add_argument("--nomultisampling", action="store_true", help="disable multisampling (used for anti-aliasing and alpha-to-coverage transparency rendering)")
    debugGroup.add_argument("--debugopengl", action="store_true", help="enable OpenGL error checking and logging (slow)")
    debugGroup.add_argument("--fullloggingopengl", action="store_true", help="log all OpenGL calls (very slow)")
    debugGroup.add_argument("--debugnumpy", action="store_true", help="enable numpy runtime error messages")
    if not isRelease():
        debugGroup.add_argument("-t", "--runtests", action="store_true", help="run test suite (for developers)")

    # Macro properties
    macroGroup = parser.add_argument_group('Macro properties', description="Optional macro properties to set on human")
    macroGroup.add_argument("--age", default=25, type=float, help="Human age, in years")
    macroGroup.add_argument("--gender", default=0.5, type=float, help="Human gender (0.0: female, 1.0: male)")
    macroGroup.add_argument("--male", action="store_true", help="Produces a male character (overrides the gender argument)")
    macroGroup.add_argument("--female", action="store_true", help="Produces a female character (overrides the gender argument)")
    macroGroup.add_argument("--race", default="caucasian", help="One of [caucasian, asian, african] (default: caucasian)")
    macroGroup.add_argument("--rig", default=None, help="Setup a rig. One of [basic, game, muscles, humanik, xonotic, second_life, second_life_bones] (default: none)") # TODO dynamically list

    subparsers = parser.add_subparsers(title="Subcommands",metavar='<command>', help="Use '<command> --help' for more info")

    def _createModifierSubcommand(subparsers_parent):
        modifierParser = subparsers_parent.add_parser("modifier", help="Specify modeling modifiers to apply to the human")
        #modifierParser.set_defaults(which="modifier")
        modifierParser.add_argument("modifierName", nargs=1, action="append", help="Name of the modifier")
        modifierParser.add_argument("modifierValue", nargs=1, action="append", type=float, help="Value to set the modifier")

        # Needed to be able to reliable close proxy subcommand
        modifierParser.add_argument("--ignoreMe", default=None, metavar="ignoreThis", help=argparse.SUPPRESS)
        return modifierParser

    def _createProxySubcommand(subparsers_parent):
        proxymeshParser = subparsers_parent.add_parser("proxy", help="Specify proxy meshes to attach")
        import proxy
        for pType in proxy.ProxyTypes:
            if pType == "Proxymeshes":  # TODO make this the default
                desc = "Attach a proxy with an alternative body topology (Only one)"
                multi = False
            else:
                desc = "Attach %s proxy" % pType.lower()
                multi = not(pType in proxy.SimpleProxyTypes)
                desc = desc + " (%s)" % ("Only one" if multi else "Multiple allowed")
            if multi:
                proxymeshParser.add_argument("--"+pType.lower(), action="append", nargs='+', default=None, metavar="proxyFile", help=desc)
            else:
                proxymeshParser.add_argument("--"+pType.lower(), default=None, metavar="proxyFile", help=desc)
        # Needed to be able to reliable close proxy subcommand
        proxymeshParser.add_argument("--ignoreMe", default=None, metavar="ignoreThis", help=argparse.SUPPRESS)
        #choices = [ pType.lower() for pType in proxy.ProxyTypes ]
        #proxymeshParser.add_argument("type", nargs='?', help="Type of the proxy to add, available options: {%s}" % " ".join(choices))
        #proxymeshParser.add_argument("proxyfile", nargs='?', help="The file path of the proxy to load")
        return proxymeshParser

    def _createEndSubcommand(subparsers_parent):
        return subparsers_parent.add_parser("endcommand", help="")

    def _endConnector(endNode):
        subparsers_parent = endNode.add_subparsers(help=argparse.SUPPRESS)
        _createEndSubcommand(subparsers_parent)

    modifierParser = _createModifierSubcommand(subparsers)
    proxymeshParser = _createProxySubcommand(subparsers)
    _createEndSubcommand(subparsers)


    ## Add subparsers as subcommands to each other, allowing chaining of multiple subcommands
    sub_subparsers = modifierParser.add_subparsers(help=argparse.SUPPRESS)
    _createModifierSubcommand(sub_subparsers)
    _createProxySubcommand(sub_subparsers)
    _createEndSubcommand(sub_subparsers)

    sub_subparsers = proxymeshParser.add_subparsers(help=argparse.SUPPRESS)
    _createModifierSubcommand(sub_subparsers)
    #_createProxySubcommand(sub_subparsers)
    _createEndSubcommand(sub_subparsers)




    # Perform some validation on the input
    argOptions = vars(parser.parse_args())
    if argOptions["male"]:
        argOptions["gender"] = 0.9
    elif argOptions["female"]:
        argOptions["gender"] = 0.1

    print argOptions
    sys.exit()

    return argOptions

def main():
    print "MakeHuman v%s" % getVersionDigitsStr()
    try:
        set_sys_path()
        make_user_dir()
        get_platform_paths()
        redirect_standard_streams()
        if not isRelease():
            get_hg_revision()
        os.environ['MH_VERSION'] = getVersionStr()
        os.environ['MH_SHORT_VERSION'] = getShortVersion()
        os.environ['MH_MESH_VERSION'] = getBasemeshVersion()
        args = parse_arguments()
        init_logging()
    except Exception as e:
        print >> sys.stderr,  "error: " + format(str(e))
        import traceback
        bt = traceback.format_exc()
        print >> sys.stderr, bt
        return

    # Pass release info to debug dump using environment variables
    os.environ['MH_FROZEN'] = "Yes" if isBuild() else "No"
    os.environ['MH_RELEASE'] = "Yes" if isRelease() else "No"

    debug_dump()
    from core import G
    G.args = args

    # Set numpy properties
    if not args.get('debugnumpy', False):
        import numpy
        # Suppress runtime errors
        numpy.seterr(all = 'ignore')

    # -o or --output option given -> run in headless mode
    runHeadless = bool( args.get("output", None) )

    if runHeadless:
        import headless
        headless.run(args)
    else:
        # Here pyQt and PyOpenGL will be imported
        from mhmain import MHApplication

        application = MHApplication()
        application.run()

    #import cProfile
    #cProfile.run('application.run()')

    close_standard_streams()

if __name__ == '__main__':
    main()
