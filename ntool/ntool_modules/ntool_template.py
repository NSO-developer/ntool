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
        print("""
        begin command
            modes: oper config
            styles: c i j
            cmdpath: ntool template
            help: Create a device or config template
        end

        begin param
          name: ned-id
          presence: optional
          flag: -n
          help: NSO CLI NED identifier
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
          type: void
          presence: optional
          flag: -v
          help: verbose output
        end

        """)

class NtoolTemplate:

    def __init__(self, username, nedid, type, debug=True):
       '''Initialization function'''

       self.username = username
       self.nedid = nedid
       self.type = type
       self.template = ''
       self.debug = debug
       self.cmd_list = []
       self.last_error = ''


    def process_cmd_line(self, line):
       '''Read in the specificed command file'''
       self.cmd_list = line.split('\n')

    def load_cmd_file(self, filename):
       '''Read in the specificed command file'''

       try:
          with open(filename, "r") as ins:
             for line in ins:
                self.cmd_list.append(line)
          print("\tRead (%d) lines from file: %s" % (len(self.cmd_list), filename))
       except:
          print("\tUnable to read file [%s]" % filename)
          exit(0)

    def write_tempate_file(self, template, filename):
       '''Write the template file'''

       try:
          with open(filename, "w") as ins:
             ins.write(template)
       except:
          print("\tFailed to write file [%s]" % filename)
          exit(0)

    def find_ned_ids(self):
       ''' Find all active CLI NED Ids '''

       self.cli_neds = []
       with ncs.maapi.single_read_trans(self.username, 'Onboard') as t:
  
         root = maagic.get_root(t, shared=False)  
         for pkg in root.ncs__packages.package:
           for comp in pkg.component:
             if comp.ned.cli and comp.ned.cli.ned_id and "cli" in comp.ned.cli.ned_id:
               vals = comp.ned.cli.ned_id.split(':')
               self.cli_neds.append(vals[1])      

    def template_build(self):
        '''Build the template'''
        pCmds = ''
        for cmds in self.cmd_list:
          pCmds = pCmds + cmds + "\n"
        
        self.template = NtoolTemplate.create_template(pCmds, 
                                                      self.username, 
                                                      self.nedid)
  
    def preprocess_fortinet(self):
       '''Fortinet NED requires actually converting config to NSO
          something normally done in the NED'''
       index=0
       for line in self.cmd_list:
           if line.startswith("config "):
               self.cmd_list[index] = self.cmd_list[index].replace('config ', '')
           elif line.startswith("edit "):
               self.cmd_list[index] = self.cmd_list[index][4:]
           elif line.startswith("set "):
               self.cmd_list[index] = self.cmd_list[index][3:]
           elif line.startswith("unset "):
               self.cmd_list[index] = self.cmd_list[index][3:]
               self.cmd_list[index] = 'no ' + self.cmd_list[index]
           elif line.startswith('next'):
               self.cmd_list[index] = self.cmd_list[index][4:]
           elif line.startswith('end'):
               self.cmd_list[index] = self.cmd_list[index][3:]
           index +=1

    @staticmethod
    def recv_all_and_close(c_sock, c_id):
       data = ''
       while True:
          buf = c_sock.recv(4096)
          if buf:
             data += buf.decode('utf-8')
          else:
            c_sock.close()
            return data

    @staticmethod
    def create_template(cmds, username, nedid):
       ''' Find all active CLI NED Ids '''
       
       with ncs.maapi.Maapi() as m:
         with ncs.maapi.Session(m, username, 'system'):
           with m.start_write_trans() as trans:

              path = '/ncs:devices/ncs:device{TEMP1-DEVICE}/config'
              root = ncs.maagic.get_root(trans)
              tempd = root.ncs__devices.ncs__device.create('TEMP1-DEVICE')
              tempd.device_type.cli.ned_id = nedid

              flags = _ncs.maapi.CONFIG_C_IOS
              if 'xr' in nedid:
                 flags = _ncs.maapi.CONFIG_C

              try:
                 result = _ncs.maapi.load_config_cmds(m.msock,
                                                      trans.th,
                                                      flags | \
                                                      _ncs.maapi.CONFIG_REPLACE | \
                                                      _ncs.maapi.CONFIG_CONTINUE_ON_ERROR,
                                                      cmds, 
                                                      path)
                 c_id =  _ncs.maapi.save_config(m.msock,
                                                trans.th,
                                                flags | \
                                                _ncs.maapi.CONFIG_XML_PRETTY,
                                                path)
                 c_sock = socket.socket()
                 _ncs.stream_connect(c_sock, c_id, 0, '127.0.0.1', _ncs.NCS_PORT)
                 data = NtoolTemplate.recv_all_and_close(c_sock, c_id)
                 template = str(data)

                 template = template.replace("<device>\n    <name>TEMP1-DEVICE</name>",
                                             "<template>\n    <name>TEMP-NAME</name>\n" + \
                                                          "      <ned-id>\n" + \
                                                          "       <id>" + nedid + "</id>") 
                 template = template.replace("</device>\n  </devices>",
                                             "   </ned-id>\n    </template>\n   </devices>")

                 return template

              except Exception as e:
                 print ("Exception creating template: %s" % e)
                 return e

def main(argv):

   parser = argparse.ArgumentParser()
   parser.add_argument("-c", "--command", action='store_true', dest='command', help="command")
   parser.add_argument("-f", "--file", action='store', dest='file', help="file")
   parser.add_argument("-o", "--ofile", action='store', dest='ofile', help="ofile")
   parser.add_argument("-l", "--line", action='store', dest='line', help="line")
   parser.add_argument("-n", "--nedid", action='store', dest='nedid', default='none', help="NED id")
   parser.add_argument("-t", "--type", action='store', dest='type', default = 'device', help="Template type")
   parser.add_argument("-v", "--verbose", action='store_true', dest='verbose', help="verbose")
   parser.add_argument("-m", "--template", action='store', dest='template', help="template")
   parser.add_argument("-u", "--username", action='store', dest='username', default='admin', help="Username")
   args = parser.parse_args()

   if (args.command) :
      print_ncs_command_details()
      exit(0)

   print("\nCreating template  type [%s] ....\n" % args.type)

   cto = NtoolTemplate(args.username, args.type, args.verbose)

   print("\tSearching for existing NSO CLI based network element drivers")
   cto.find_ned_ids()
   
   # Choose the appropriate NED to move forward with
   if args.nedid == 'none':
      for i in range(len(cto.cli_neds)):
         print("\t\t{0}) {1}".format(i, cto.cli_neds[i]))
      
      value = input("\n\t\tSelect a ned-id from above: ")   
      cto.nedid = cto.cli_neds[int(value)]            
   else:
      if args.nedid not in cto.cli_neds:
        print("Invalid NED id specified exiting!!")
        exit(0)
      cto.nedid = args.nedid
      
   print("\n\tProceeding with ned-id: {0}".format(cto.nedid))

   if (args.file):
      cto.load_cmd_file(args.file)
   elif (args.line):
      cto.process_cmd_line(args.line)

   ###
   # Convert fortinet config into IOS format before consuming it
   ###
   if 'fortinet-fortios-cli-5' in cto.nedid:
      cto.preprocess_fortinet()   


   cto.template_build()

   print("Template: \n{0}".format(cto.template))
 
   print("\nTemplate create completed\n")
   print(" ")

if __name__ == '__main__' :
    main(sys.argv[1:])

