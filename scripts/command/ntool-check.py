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
import re

_V = _ncs.Value
_TV = _ncs.TagValue
_XT = _ncs.XmlTag


def print_ncs_command_details():
    print """
        begin command
            modes: oper config
            styles: c i j
            cmdpath: ntool verify
            help: Command to verfiy NED support exists for various commands
        end

        begin param
          name: verbose
          presence: optional
          flag: -v
          help: verbose output
        end

        begin param
          name: type
          presence: mandatory
          flag: -t
          help: ios, iosxr, nexus, arista
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
          help: command file
        end

        """


def print_config_lines(dev_type, cfg_lines):
    for line in cfg_lines:
        line = line.replace(dev_type + ":", "")
        if line.find("description") != -1:
            if line.find("|") != -1:
                line = line.replace("\|", "|")
            elif line.find(";") != -1:
                line = line.replace("\;", ";")
        if line.startswith("** "):
            print line
        else:
            print "   " + line


def extract_line_num(result):
    p = re.compile('Error: on line ([0-9]+):')
    m = p.search(str(result))
    if m:
        return m.group(1)
    else:
        return 0


def trim_config_lines(cfg_lines, line_num):
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


def verify_line(pc, dev_type):
    # Ignore commands starting with the following as they are supported in NSO.
    # Passing them as-is for verification will not work as the NED pre-processes
    # these commands.
    if pc.startswith(dev_type + ":banner") \
            or pc.startswith(dev_type + ":crypto pki certificate") \
            or pc.startswith(dev_type + ":prefix-set") \
            or pc.startswith(dev_type + ":community-set") \
             or pc.startswith(dev_type + ":route-policy") \
            or pc.startswith(dev_type + ":end") \
            or pc == dev_type + ":boot-start-marker\n" \
            or pc == dev_type + ":boot-end-marker\n" \
            or pc == dev_type + ":radius-server source-ports\n" \
            or pc == dev_type + ":hw-module\n" \
            or pc == dev_type + ":license udi\n" \
            or pc == dev_type + ":end\n" \
            or pc == dev_type + ":exit":
            
        return False
    else:
        return True


def verify_command_file(maapi_sock, cmd_str, file_name, device_type, verbose):
    if device_type == "iosxr":
        dev_type = "cisco-ios-xr"
    elif device_type == "nexus":
        dev_type = "nx"
    elif device_type == "arista":
        dev_type = "dcs"
    else:
        dev_type = device_type

    cmd_list = []
    if cmd_str:
        cmd_list = cmd_str.splitlines()
    else:
        with open(file_name, "r") as ins:
            for line in ins:
                cmd_list.append(line)

    # Add namespace to all top level commands
    index = 0

    for cmd in cmd_list:
        if cmd != "" and cmd[0].isalpha():
            if cmd.startswith("no "):
                cmd_list[index] = cmd_list[index].replace("no ", "no " + dev_type + ":", 3)
            else:
                cmd_list[index] = dev_type + ":" + cmd_list[index]
        index += 1

    pc = ""
    for cmd in cmd_list:
        pc = pc + cmd

    # Add all commands and sub commands into the same
    # line before processing
    process_cmds = [""]
    index = 0
    banner = False
    for mod in cmd_list:
        if mod.startswith(dev_type + ":banner"):
            banner = True
        if banner and mod == "!\n":
            banner = False
        if (mod != "") and (not banner or mod.startswith(dev_type + ":banner")) and \
                (mod[0].isalpha() or mod[0] == "!") and (mod != dev_type + ":end-set\n") and \
                (mod != dev_type + ":end-policy\n"):
            process_cmds.append(mod)
            index += 1
        else:
            if banner or (mod != "\n" and mod != "\r" and mod != "!" and mod != ""):
                if mod.find("description") != -1:
                    if mod.find("|") != -1:
                        mod = mod.replace("|", "\|")
                    elif mod.find(";") != -1:
                        mod = mod.replace(";", "\;")
                process_cmds[index] = process_cmds[index] + mod

    # Loop through all commands and verify them
    index = 0
    for pc in process_cmds:
        if pc != "":
            res = ""
            cfg_lines = pc.splitlines()
            if verify_line(pc, dev_type):
                while res != "verfied":
                    result = _ncs.maapi.request_action(sock=maapi_sock,
                                                       params=[
                                                           _TV(_XT(436315975, 1723459864), _V(device_type)),
                                                           _TV(_XT(436315975, 542126253), _V(pc))
                                                       ], hashed_ns=0,
                                                       path='/ntool:ntool-commands/ntool:verify')
                    res = result[0].v
                    if res != "verfied":
                        line_num = int(extract_line_num(res))
                        pc = trim_config_lines(cfg_lines, line_num)

            print_config_lines(dev_type, cfg_lines)

        index += 1


def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--command", action='store_true', dest='command', help="command")
    parser.add_argument("-s", "--standalone", action='store_true', dest='standalone', help="standalone")
    parser.add_argument("-f", "--file", action='store', dest='file', help="Configuration file to verify")
    parser.add_argument("-l", "--line", action='store', dest='line', help="line")
    parser.add_argument("-t", "--type", action='store', dest='type', help="ios, iosxr, nexus, arista")
    parser.add_argument("-v", "--verbose", action='store_true', dest='verbose', help="verbose")
    args = parser.parse_args()

    if args.command:
        print_ncs_command_details()
        exit(0)

    if args.verbose:
        print " "
        print "  Verifying [%s] command(s) sequence...." % args.type

    if args.standalone:
        with maapi.wctx.connect(ip='127.0.0.1', port=_ncs.NCS_PORT) as c:
            with maapi.wctx.session(c, 'admin') as s:
                with maapi.wctx.trans(s, readWrite=_ncs.READ_WRITE) as t:
                    verify_command_file(t.sock, args.line, args.file, args.type, args.verbose)
    else:
        t = maapi.scripts.attach_and_trans()
        verify_command_file(t.sock, args.line, args.file, args.type, args.verbose)

    if args.verbose:
        print "  Verification completed"
        print " "

if __name__ == '__main__':
    main(sys.argv[1:])
