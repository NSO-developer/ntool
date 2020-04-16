#!/usr/bin/env python
# Copyright 2014 Tail-f Systems
#

#
# Name: interface
#
# Author: Dan Sullivan
# Created: 03-Mar-2016
#
#
import ncs
import _ncs
import sys
import argparse
import os
import subprocess
import socket
import re
import getpass
import time
import ncs.maagic as maagic
import ncs.maapi as maapi
import time
from datetime import datetime, time

def print_ncs_command_details():
    print ("""
        begin command
            modes: oper config
            styles: c i j
            cmdpath: ntool verify
            help: Command to verfiy NED support exists for various commands
        end
        
        begin param
          name: verbose
          type: void
          presence: optional
          flag: -v
          help: verbose output
        end

        begin param
          name: ned-id
          presence: optional
          flag: -n
          help: Valid cli ned-id (Ned must be loaded in NSO)
        end

        begin param
          name: file
          presence: optional
          flag: -f
          help: Command file
        end

        begin param
          name: output-file
          presence: optional
          flag: -o
          help: Command file
        end

        begin param
          name: command
          words: any
          presence: optional
          flag: -l
          help: Command to parse
        end
        """)

class NtoolVerify:
   '''Python class which can be used to verify CLI NED commands'''

   def __init__(self, username, output='none', verbose=False, debug=True):
       '''Initialization function'''
       self.nedid = 'none'
       self.username = username
       self.debug = debug
       self.verbose = verbose
       self.cmd_list = []
       self.last_error = ''
       self.outfile = output
       self.outf = False

   def process_cmd_line(self, line):
       '''Process command string'''
       self.cmd_list = line.split('\n')

   def load_cmd_file(self, filename):
      '''Read in the specificed command file'''

      try:
         if filename == 'None':
            return
         with open(filename, "r") as ins:
             for line in ins:
                self.cmd_list.append(line)
         print("\tRead (%d) lines from file: %s" % (len(self.cmd_list), filename))
      except:
         print("\tUnable to read file [%s]" % filename)
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

   def verify(self):
      '''Verify the validity of the cmds loaded previously'''
     
      # Add all commands and sub commands into the same
      # line before processing

      try:
        if self.outfile != 'none':
          self.outf = open(self.outfile, "w")
        else:
           self.outf = False
      except:
         print("\tCannot open outputfile for writing {0}".format(self.outfile))
         
      self.processed_lines = 0
      self.error_lines = 0
      self.duplicate_lines = 0
      self.duplicates = []
      self.start = datetime.now()
      process_cmds = [""]
      index = 0
      banner = False
      for mod in self.cmd_list:
         if mod.startswith("banner"):
            banner = True
         if banner and ((mod == "!\n") or (mod == "\n")):
            banner = False
         if (mod != "") and (not banner or mod.startswith("banner")) and \
                (mod[0].isalpha() or mod[0] == "!") and (mod !="end-set\n") and \
                (mod != "end-policy\n"):
            process_cmds.append(mod)
            index += 1
         else:
            if banner or (mod != "\n" and mod != "\r" and mod != "!" and mod != "" and mod != "#\n"):
                if mod.find("description"):
                    if mod.find("|"):
                        mod = mod.replace("|", "\|")
                    elif mod.find(";"):
                        mod = mod.replace(";", "\;")
                process_cmds[index] = process_cmds[index] + mod

      # Loop through all commands and verify them
      index = 0
      for pc in process_cmds:
        if pc and (pc.isspace() == False):
        #if pc != "" or pc != "\n" or pc  or not pc.isspace():
            res = ""
            cfg_lines = pc.splitlines()
            error = 'start'
            errors = False       
            if NtoolVerify.verify_line(pc):
                self.processed_lines += len(cfg_lines)
                while error :
                    error = NtoolVerify.verify_cli_cmds(self.username, 
                                                        self.nedid, 
                                                        pc)
                    if error:
                        line_num = int(NtoolVerify.extract_line_num(error))
                        errors = True;
                        pc = NtoolVerify.trim_config_lines(cfg_lines, line_num)

                for e in cfg_lines:
                   if e.startswith('** '):
                      self.error_lines +=1
                      if e in self.duplicates:
                        self.duplicate_lines +=1
                      else:
                        self.duplicates.append(e)

                if not self.verbose and errors:
                   NtoolVerify.print_config_lines(cfg_lines)
                if self.outf and errors:
                  NtoolVerify.print_config_lines(cfg_lines, outfile=self.outf)
                  self.outf.write("\n")

            if self.verbose:
                NtoolVerify.print_config_lines(cfg_lines)

        index += 1

      self.finish = datetime.now() 
      self.elapsed = self.finish - self.start

   @staticmethod
   def verify_line(pc):
    # Ignore commands starting with the following as they are supported in NSO.
    # Passing them as-is for verification will not work as the NED pre-processes
    # these commands.
    if pc.startswith("banner") \
            or pc.startswith("Building configuration...") \
            or pc.startswith("Current configuration :") \
            or pc.startswith("crypto pki certificate") \
            or pc.startswith("prefix-set") \
            or pc.startswith("community-set") \
            or pc.startswith("route-policy") \
            or pc.startswith("end") \
            or pc.startswith("xxxx") \
            or pc == "boot-start-marker\n" \
            or pc == "boot-end-marker\n" \
            or pc == "radius-server source-ports\n" \
            or pc == "hw-module\n" \
            or pc == "license udi\n" \
            or pc ==  "end\n" \
            or pc == "quit\n" \
            or pc == "exit":
        return False
    else:
        return True

   @staticmethod
   def print_config_lines(cfg_lines, outfile=False):
      for line in cfg_lines:
         if line.find("description") != -1:
           if line.find("|") != -1:
              line = line.replace("\|", "|")
           elif line.find(";") != -1:
                line = line.replace("\;", ";")
         if line.startswith("** "):
            if outfile:
              outfile.write(line + "\n")
            else:
              print(line)
         else:
            if outfile:
              outfile.write("   " + line + "\n")
            else:
              print("   " + line)

   @staticmethod
   def extract_line_num(result):
      '''Find the failing line number in the error message'''

      p = re.compile('Error: on line ([0-9]+):')
      m = p.search(str(result))
      if m:
        return m.group(1)
      else:
        return 0

   @staticmethod
   def trim_config_lines(cfg_lines, line_num):
      '''Remove error lines from configuration stanza'''

      line_num -= 1
      count = 0
      new_str = ""

      for line in cfg_lines:
         if line.startswith("** "):
            count += 1
            line_num += 1
            continue
         else:
            if line_num == count:
                cfg_lines[count] = "** " + cfg_lines[count]
                break
            else:
                count += 1

      for line2 in cfg_lines:
         if line2.startswith("** "):
            continue
         new_str = new_str + line2 + "\n"
      return new_str

   @staticmethod
   def verify_cli_cmds(username, nedid, cmds):
      '''Verify a set of CLI commands by applying them to a fake device'''

      with ncs.maapi.Maapi() as m:
        with ncs.maapi.Session(m, username, 'system'):
          with m.start_write_trans() as trans:

             root = ncs.maagic.get_root(trans)
             path = '/ncs:devices/ncs:device{TEMP0-DEVICE}'
             tempd = root.ncs__devices.ncs__device.create('TEMP0-DEVICE')
             tempd.device_type.cli.ned_id = nedid

             flags = _ncs.maapi.CONFIG_C_IOS
             if 'xr' in nedid:
                flags = _ncs.maapi.CONFIG_C

             try:
               result = _ncs.maapi.load_config_cmds(m.msock,
                                                   trans.th,
                                                   flags | \
                                                   _ncs.maapi.CONFIG_REPLACE | \
                                                   _ncs.maapi.CONFIG_SUPPRESS_ERRORS,
                                                   cmds, 
                                                   path + "/config")
             except Exception as e:
                return e

      return False

def main(argv):

   parser = argparse.ArgumentParser()
   parser.add_argument("-c", "--command", action='store_true', dest='command', help="command")
   parser.add_argument("-u", "--username", action='store', dest='username', default='admin', help="username")
   parser.add_argument("-n", "--ned", action="store", dest='ned', nargs='?', default='none', help="Configure NSOP host default=localhost")
   parser.add_argument("-f", "--file", action="store", dest='file', nargs='?', help="NSO device config file name")
   parser.add_argument("-l", "--line", action="store", dest='line', nargs='?', help="NSO device config line")
   parser.add_argument("-v", "--verbose", action="store_true", dest='verbose', default=False, help="Verbose output flag")
   parser.add_argument("-o", "--output-file", action="store", dest='ofile', default='none', help="Output file")
   args = parser.parse_args()
   
   if args.command:
        print_ncs_command_details()
        exit(0)

   print('\nStarting ntool-verify\n')
  
   ntl = NtoolVerify(args.username, output=args.ofile, verbose=args.verbose)

   ##
   # First verify the file exists and read it in
   ##
   if args.line:
     ntl.process_cmd_line(args.line)
   else:
     ntl.load_cmd_file(args.file)
   ##
   # Find the valid NED ids 
   ##
   print("\tSearching for existing NSO CLI based network element drivers\n")
   cli_neds = ntl.find_ned_ids()
   ntl.nedid = args.ned
   
   if args.ned == 'none':
      for i in range(len(ntl.cli_neds)):
         print("\t\t{0}) {1}".format(i, ntl.cli_neds[i]))
      ##
      # Choose the appropriate NED to move forward with
      ##
      value = input("\n\t\tSelect a ned-id from above: ")   
      ntl.nedid = ntl.cli_neds[int(value)]            
   else:
      if args.ned not in ntl.cli_neds:
        print("Invalid NED id specified exiting!!")
        exit(0)

   print("\n\tProceeding with ned-id: {0}".format(ntl.nedid))
   print("\tVerifying file        : {0}\n".format(args.file))
 
   ###
   # Convert fortinet config into IOS format before consuming it
   ###
   if 'fortinet-fortios-cli-5' in ntl.nedid:
      ntl.preprocess_fortinet()  
 
   ntl.verify()
 
   print("\nNSO Configuration Verify operation completed\n")
   print("============================================================")
   print("Verify Results Summary")
   print("============================================================\n")
   print("Elapsed Time                       : {0}".format(ntl.elapsed))
   print("Network Config Command File        : {0}".format(args.file))
   print("NSO Cli network element driver id  : {0}".format(ntl.nedid))
   print("Total Processed Configuration Lines: {0}".format(ntl.processed_lines))
   print("Upsupported Configuration Lines    : {0}".format(ntl.error_lines))
   print("Duplicate unsupported Lines        : {0}".format(ntl.duplicate_lines))
   prct = ((float(ntl.processed_lines) - float(ntl.error_lines))/float(ntl.processed_lines)) * 100
   print("Percent Supported                  : {0}%".format(round(prct,2)))
   dprct = ((float(ntl.processed_lines) - (float(ntl.error_lines) - float(ntl.duplicate_lines)))/float(ntl.processed_lines)) * 100
   print("Percent Supported (No duplicates)  : {0}% \n".format(round(dprct,2)))
   
if __name__ == '__main__' :
    main(sys.argv[1:])

