#!/usr/bin/env python
# Copyright 2014 Tail-f Systems
#

#
# Name: ntool-check.py
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

def print_ncs_command_details():
        print """
        begin command
            modes: oper config
            styles: c i j
            cmdpath: ntool template
            help: Create a device or config template
        end

        begin param
          name: type
          presence: mandatory
          flag: -t
          help: ios, iosxr, nexus or junos
        end

        begin param
          name: template-type
          presence: mandatory
          flag: -m
          help: config or device template type
        end

        begin param
          name: command
          words:any
          presence: optional
          flag: -l
          help: Command to parse
        end

        begin param
          name: file
          presence: optional
          flag: -f
          help: input command file
        end

        begin param
          name: output-file
          presence: optional
          flag: -o
          help: output template file
        end

        begin param
          name: verbose
          presence: optional
          flag: -v
          help: verbose output
        end

        """

def createTemplateFile(root, cmd_str, file_name, out_file, device_type, template_type, verbose):
      if not cmd_str and not file_name:
          print "  syntax error: needs either command or file input"
          exit(0)

      if not cmd_str and not os.path.isfile(file_name):
          print "  syntax error: cant find file " + file_name
          print "  current directory: " + os.getcwd()
          exit(0)

      if (device_type == "iosxr"):
        devType = "cisco-ios-xr"
      elif (device_type == "nexus"):
        devType = "nx"
      elif (device_type == "arista"):
        devType = "dcs"
      else:
        devType = device_type

      cmdList = []
      if (cmd_str):
        cmdList = cmd_str.splitlines()
        index = 0
        for cmd in cmdList:
            cmdList[index] = cmdList[index] + "\n"
            index = index + 1
      else :
        print "   Reading input command file %s" % file_name

        with open(file_name, "r") as ins:
          for line in ins:
           cmdList.append(line)
      ####
      ## Add namespace to all top level commands
      ####
      #print "   Processing command input"
      index=0
      for cmd in cmdList :
          if cmd != "" and cmd[0].isalpha():
             if cmd.startswith("no ") :
               cmdList[index] = cmdList[index].replace("no ", "no " + devType + ":", 3)
             else :
               cmdList[index] = devType + ":" + cmdList[index]
          index = index + 1
      ####
      ## Loop through all build a single string
      ####
      #print "   Creating input string"
      pCmds = ""
      for cmds in cmdList :
        pCmds = pCmds + cmds

      print "   Executing template create action...."

      action = root.ntool__ntool_commands.create_template
      inp = action.get_input()
      inp.type = 'config'
      inp.device_type = device_type
      inp.command_list = pCmds
      res = action(inp)
      outStr = res.result

      if (out_file):
        print "   Saving output to file %s" % out_file
        outlines = []
        outlines = outStr.splitlines()
        file = open(out_file, "w")
        for outStr in outlines:
          if (outStr != "") :
            file.write(outStr + "\n")
        file.close()
      else :
        print outStr

def main(argv):

   parser = argparse.ArgumentParser()
   parser.add_argument("-c", "--command", action='store_true', dest='command', help="command")
   parser.add_argument("-f", "--file", action='store', dest='file', help="file")
   parser.add_argument("-o", "--ofile", action='store', dest='ofile', help="ofile")
   parser.add_argument("-l", "--line", action='store', dest='line', help="line")
   parser.add_argument("-t", "--type", action='store', dest='type', help="type")
   parser.add_argument("-v", "--verbose", action='store_true', dest='verbose', help="verbose")
   parser.add_argument("-m", "--template", action='store', dest='template', help="template")
   args = parser.parse_args()

   if (args.command) :
      print_ncs_command_details()
      exit(0)
   print " "
   print "   Creating template  [%s] ...." % args.type

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

   createTemplateFile(root, args.line, args.file, args.ofile, args.type, args.template, args.verbose)

   print "   Template create completed"
   print " "

if __name__ == '__main__' :
    main(sys.argv[1:])

