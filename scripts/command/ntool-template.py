#!/usr/local/bin/python
# Copyright 2014 Tail-f Systems
#

#
# Name: ntool-check.py
#
# Author: Dan Sullivan
# Created: 03-Mar-2016
#
#

import _ncs 
import _ncs.deprecated.maapi as maapi
import sys
import argparse
import os
import subprocess
import socket
import re

_V = _ncs.Value
_TV = _ncs.TagValue
_XT = _ncs.XmlTag

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
          help: Comannd to parse
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

def createTemplateFile(maapiSock, cmdStr, fileName, outFile, deviceType, templateType, verbose):

      if (deviceType == "iosxr"):
        devType = "cisco-ios-xr"
      elif (deviceType == "nexus"):
        devType = "nx"
      elif (deviceType == "arista"):
        devType = "dcs"
      else:
        devType = deviceType

      cmdList = []
      if (cmdStr):
        cmdList = cmdStr.splitlines()
        index = 0
        for cmd in cmdList:
            cmdList[index] = cmdList[index] + "\n"
            index = index + 1
      else :
        print "   Reading input command file %s" % fileName
     
        with open(fileName, "r") as ins:
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
      result = _ncs.maapi.request_action(sock = maapiSock,
                params = [
                           _TV(_XT(436315975, 2040883914), _V(templateType)),
                           _TV(_XT(436315975, 1723459864), _V(deviceType)),
                           _TV(_XT(436315975, 542126253), _V(pCmds))
                        ], 
                hashed_ns = 0,
                path = '/ntool:ntool-commands/ntool:create-template')
   
      #if (result[0].v):
      #  print "   Template created"

      if (outFile):
        print "   Saving output to file %s" % outFile
        outlines = []
        outStr = str(result[0].v)
        outlines = outStr.splitlines()
        file = open(outFile, "w")
        for outStr in outlines:
          if (outStr != "") :
            file.write(outStr + "\n")
        file.close()
      else :
        print result[0].v

def main(argv):

   parser = argparse.ArgumentParser()
   parser.add_argument("-c", "--command", action='store_true', dest='command', help="command")
   parser.add_argument("-s", "--standalone", action='store_true', dest='standalone', help="standalone")
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

   if (args.standalone) :
     with maapi.wctx.connect(ip = '127.0.0.1', port = _ncs.NCS_PORT) as c :
        with maapi.wctx.session(c, 'admin') as s :
            with maapi.wctx.trans(s, readWrite = _ncs.READ_WRITE) as t :
                  createTemplateFile(t.sock, args.line, args.file, args.ofile, args.type, args.template, args.verbose)
   else :
      t = maapi.scripts.attach_and_trans()
      createTemplateFile(t.sock, args.line, args.file, args.ofile, args.type, args.template, args.verbose)
    
   print "   Template create completed"
   print " "

if __name__ == '__main__' :
    main(sys.argv[1:])

