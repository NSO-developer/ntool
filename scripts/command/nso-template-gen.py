#!/usr/local/bin/python
# Name: nso-template-gen.py
#
# Author: Dan Sullivan
# Created: 03-Mar-2016
#
#
import ncs
import _ncs
import ncs.maagic as maagic
import sys
import argparse
import os
import subprocess
import socket
import re
import tarfile
import shutil
from collections import Counter

step = 1

prefixList = {'cisco-ios': 'ios', 'cisco-iosxr' : 'cisco-ios-xr', 'arista-dcs' : 'dcs',
              'adva-825' : 'adva-825', 'adtran-aos' : 'adtran-aos', 'alu-sr': 'alu',
              'unknown' : 'unknown'}

def print_ncs_command_details():
        print """
        begin command
            modes: oper config
            styles: c i j
            cmdpath: ntool cli template
            help: Auto render an NSO config template
        end

        begin param
          name: package
          presence: mandatory
          flag: -p
          help: NSO package file
        end

        begin param
          name: debug
          type: void
          presence: optional
          flag: -d
          help: Verbose debug mode
        end

        """

class generateCliTemplate:

    def __init__(self, m, th, root, file, path, debug):
      
        self.maapi = m
        self.th = th
        self.file = file
        self.template = file.rsplit( ".", 1 )[ 0 ] + ".xml"
        self.path = path
        self.root = root
        self.debug = debug
        return

    def generateTemplate(self):
        "Generate template from .cfg file"

        print ""
        progressDisplay("Parsing [%s]" % (self.file))
   
        try:
          with open(self.path + "/cli/" + self.file) as f:
            self.lines = f.read().splitlines()
            progSuccess()
        except:
            progFail()

        self.nedId = self.extractNED()
        self.extractNedVersion()
        self.tags = self.extractTags()
       
        print "\n\t\tNED Type:    %s" % (self.nedId)
        print "\t\tNED Version: %s\n" % (self.version)
     
        vars = self.extractVars()
        if self.debug:
          print "\t\tTemplate Variables"
          print "\t\t------------------"
          for k,v in vars.items():
            print "\t\t%-10s Default [%s]" % (k,v)
          print
        
        ###
        # Now substitue in variable names into CLI 
        # command output
        ###
        outlines = self.substituteVars(prefixList[self.nedId])
   
        # Create a string out of list
        cmdString = '\n'.join(outlines)
        deviceType = 'iosxr'
        if self.nedId != 'cisco-iosxr':
          deviceType = 'ios'
  
        self.displayStr("CLI Commands", cmdString)

        ###
        # Generate the template from the CLI commands
        ###
        progressDisplay("Generating template from [%s]" % (self.file))
        outStr = ""
        try:
          action = self.root.ntool__ntool_commands.create_template
          inp = action.get_input()
          inp.type = 'config'
          inp.device_type = deviceType
          inp.command_list = cmdString
          res = action(inp)
          outStr = res.result
          progSuccess()
        except:
          progDisplay()

        ###
        # Add the variables back into the template subsituting
        # them for the initial values
        ###
        self.displayStr("Raw template output", outStr)
        outStr = self.addVars(vars, outStr)
        self.displayStr("Template after variable substitution", outStr)

        ###
        # Modify the template output to account for the TAGMOD
        # statements in the .cfg file
        ###
        outStr = self.addConstraints(vars, outStr)
        outStr = self.addTags(outStr)
       
        self.displayStr("Template with constraints added", outStr)

        progressDisplay("Saving template file [%s]" % (self.template))
        self.saveTemplate(outStr)

        progressDisplay("Parsing [%s]" % (self.file))
        progSuccess("Completed")

    def addTags(self, outStr):
        "Add XML tag substituion to output file"
        outlines = outStr.split('\n')
        update = []
        for line in outlines:
          newLine = line
          for k,v in self.tags.items(): 
               if "<" + k + ">" in line:
                 newLine = newLine.replace("<" + k + ">", 
                                           "<" + k + " " + v + ">")
               elif "<" + k + "/>" in line:
                 newLine = newLine.replace("<" + k + "/>", 
                                           "<" + k + " " + v + "/>")
          if (line != ""):
            update.append(newLine)
    
        return "\n".join(update)       

    def addConstraints(self, vars, outStr):
        "Add when constraints to XML output file "
        
        outlines = outStr.split('\n')
        update = []

        for line in outlines:
          newLine = line
          for k,v in vars.items():

             if v == 'nonull':   
               if ">{$" + k + "}<" in line:
                 newLine = newLine.replace(">{$" + k + "}<", 
                                        " when=\"{$" + k + "!=\'\'}\">{$" + k + "}<")
          update.append(newLine)
    
        return "\n".join(update)

    def addVars(self, vars, outStr):
        "Add variable names back to XML template"

        for k,v in vars.items():

           if v == 'none':
             outStr = outStr.replace(k, "{$" + k + "}")
           elif v == 'nonull':
             outStr = outStr.replace(k, "{$" + k + "}")
           else:
             #outStr = outStr.replace(">" + v + "<", ">{$" + k + "}<")
             outStr = outStr.replace(v, "{$" + k + "}")

        return outStr

    def substituteVars(self, prefix):
        "Prepare commands for template creation "

        outlines = []
        vp = re.compile("{\$([a-zA-Z0-9\-\_]*)=([a-zA-Z0-9\-\._\/]*)}|{\$([a-zA-Z0-9\-\_\/)]*)}")
        for line in self.lines:
      
          if not line:
            continue

          if line[0] == "+":
            continue
          outline = line
          mv = vp.findall(line)
          if mv:
            for m in mv:
               if m[0]:
                 if m[1] != 'nonull':
                   outline = outline.replace("{$" + m[0] + '=' + m[1] + "}", m[1])
                 else:
                   outline = outline.replace("{$" + m[0] + '=' + m[1] + "}", m[0])
               else:
                 outline = outline.replace("{$" + m[2] + "}", m[2])
          ###
          # Add NED prefix to all top level commands
          ###
          if outline != '' and outline[0].isalpha():
             if outline.startswith("no "):
                outline = outline.replace("no ", "no " + prefix + ":")
             else:
               outline = prefix + ':' + outline

          outlines.append(outline)
        return outlines

    def extractVars(self):
        "Read through file contents and extract variables"
    
        vars = {}
        ###
        # Search for all variables and save in a list
        ###
        vp = re.compile("{\$([a-zA-Z0-9\-\_]*)=([a-zA-Z0-9\-\._\/]*)}|{\$([a-zA-Z0-9\-\_\/)]*)}")
        for line in self.lines:
          mv = vp.findall(line)
          if mv:
            for m in mv:
               if m[0]:
                 vars[m[0]] = m[1]
               else:
                 vars[m[2]] = "none"
        return vars

    def extractTags(self):
        "Extract XML TAG modifications from cfg file"
        tagList = {}
        for line in self.lines:
           if line.startswith("+TAGMOD:"):
              subStr = line.replace("+TAGMOD:", "")
              tags = subStr.split("::")
              tagList[tags[0]] = tags[1]
        return tagList

    def extractNED(self):
        "Read the NED type from the cfg file"
        nedId = self.lines[0]
        np = re.compile("\+NED:([a-zA-Z0-9\-_]*)")    
        m = np.search(nedId)
        if m:
          if m.group(1):
            return(m.group(1))
        else:
          return('unknown')

    def displayStr(self, msg, displayStr):
         "Display debug output"
         if not self.debug:
            return
         print ""
         print "\t    %s" % (msg) 
         print "\t    -----------------------------------"
         lines = displayStr.split("\n")
         for line in lines:
            print "\t       %s" % (line)

    def extractNedVersion(self):
         "Determine the version of specified NED package"
         vp = re.compile("package-version ([0-9]\.[0-9]\.+[0-9]+)")
         version = runCliCommand('show packages package %s package-version' % (self.nedId))
         m = vp.search(version)
         self.version = m.group(1)

    def saveTemplate(self, outStr):
        "Write template to gen directory"
        try:
          os.stat(self.path + '/gen')
        except:
          os.mkdir(self.path + '/gen')
          
        try:
           os.stat(self.path + '/gen/' + self.nedId + '-' + self.version)
        except:
           os.mkdir(self.path + '/gen/' + self.nedId + '-' + self.version)

        try:
           os.stat(self.path + '/gen/latest')
        except:
           os.mkdir(self.path + '/gen/latest')

        try:
           file = open(self.path + '/gen/' + self.nedId + '-' + self.version + '/' + self.template, "w")

           outStr = outStr.replace("<config-template xmlns=\"http://tail-f.com/ns/config/1.0\">",
                                 "<config-template xmlns=\"http://tail-f.com/ns/config/1.0\">" +
                                 "\n  <!-- \n" +
                                 "     tailf-ntool Generated File using NED package " + self.nedId + " version [" + self.version + "]\n" +
                                 "   -->")
           file.write(outStr)
           file.close()
           file = open(self.path + '/gen/latest/' + self.template, "w")
           file.write(outStr)
           file.close()
           progSuccess()

        except:
           progFail()

def progressDisplay(message):
    "Display message for current task"

    global step
    display = "\t%s" % (message)
    spaces = 70 - len(display)
    print display,
    print spaces * '.',
    step += 1

def progFail():
    "Display failure message"
    print 'Failed'
    exit(0);

def progSuccess(msg='Success'):
    "Display success message"
    print msg
def runCliCommand(command):
     #try:
       cmd=['ncs-maapi','--clicmd','--get-io', command]
       p1 = subprocess.check_output(cmd, shell=False)
       return p1
     #except:
       #return False;

def main(argv):
   ###
   # Setup up command line arguements
   ###
   parser = argparse.ArgumentParser()
   parser.add_argument("-c", "--command", action='store_true', dest='command', help="command")
   parser.add_argument("-p", "--package", action='store', dest='package', help="package")
   parser.add_argument("-d", "--debug", action='store_true', dest='debug', help="Debug mode")
   args = parser.parse_args()

   if (args.command) :
      print_ncs_command_details()
      exit(0)
   ##
   # Read environment variables
   ##
   port = int(os.getenv('NCS_IPC_PORT', _ncs.NCS_PORT))
   usid = int(os.getenv('NCS_MAAPI_USID'))
   th = int(os.getenv('NCS_MAAPI_THANDLE'))

   ###
   # Attach to current transaction
   ###
   maapi = ncs.maapi.Maapi(ip='127.0.0.1', port = port)
   maapi.attach(th, usid=usid)
   root = maagic.get_root(maapi, shared=False)

   print "\nGenerating Service Configuration Template(s)\n " 

   progressDisplay("Changing directory to package directory")
   os.chdir("./packages")
   progSuccess()

   progressDisplay("Searching for package [%s]" % (args.package))
   if args.package in os.listdir("."):
      progSuccess("Found")
   else:
      progFail()
      exit(0)
   
   ###
   # Save the current latest directory as previous if it exists
   ###
   try:
     os.stat("./" + args.package + "/gen")
   
     try: 
       os.stat("./" + args.package + "/gen/latest")
       os.rename("./" + args.package + "/gen/latest",
                "./" + args.package + "/gen/previous")
     except:
      pass
   except:
      pass 
   
   ###
   # Start generation templates for all cfg files in the cli directory
   ###
   for file in os.listdir("./" + args.package + "/cli"):
      if file.startswith("."):
        continue
      genTmp = generateCliTemplate(maapi, th, root, file, "./" + args.package, args.debug)
      genTmp.generateTemplate()

   print "\nCompleted\n " 
if __name__ == '__main__' :
    main(sys.argv[1:])
