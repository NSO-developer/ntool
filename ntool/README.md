# tail-ntool
  
(NSO 5.2+) A few tools to help with verifying CLI configurations and generating NSO templates

# Purpose

Ntool is a collection of actions and NSO CLI scripts (utilizing plug-and-play) that
are useful for verifying a particular CLI configuration and also generation of NSO
configuration templates using NSO.

* The verify option allows the user to verify a set of CLI commands are supported
  by a specific NSO network element driver (NED)

* The template command allows the user to generate a deivice or config template
  directly from a specific set of CLI commands

* The cli template option allows the user the ability to create service templates using
  template variables and CLI configuration file.

# Documentation

Appart from this file, the main documentation is the python code and associated
YANG file(s).

# Dependencies

In order to utilize all the functionality, you will need to have (in the path)
the following components.

* NSO 5.x
* Python 2.7+ or 3+ (NSO 5.3 requires Python3)

Of course you will also need the appropriate NSO CLI Neds to use the utilities

## ntool verify

The ntool verfiy tool can be used in 2 specific ways.

    (1) Standalone mode execute the script by typing the following:
```
    dan@mycomp% python3 ntool_verify.py --help
    usage: ntool_verify.py [-h] [-c] [-u USERNAME] [-n [NED]] [-f [FILE]]
                       [-l [LINE]] [-v] [-o OFILE]

    optional arguments:
    -h, --help            show this help message and exit
    -c, --command         command
    -u USERNAME, --username USERNAME
    -n [NED], --ned [NED]
                        Configure NSOP host default=localhost
    -f [FILE], --file [FILE]
                        NSO device config file name
    -l [LINE], --line [LINE]
                        NSO device config line
    -v, --verbose         Verbose output flag
    -o OFILE, --output-file OFILE
                        Output file
dan@DANISULL-M-73NJ commit-queue-overlap % 
```
  (2) Executing the script from the NSO command line
```
  admin@ncs> ntool verify 
  Possible completions:
    command     - Command to parse
    file        - Command file
    ned-id      - Valid cli ned-id (Ned must be loaded in NSO)
    output-file - Command file
    verbose     - verbose output
  admin@ncs> ntool verify
```

Since NSO 5.x supports multiple NED versions it is required to tell
the ntool which NED version to use for verifying configuration. If 
a NED identifier isn't provided ntool verify will prompt you to 
select an available NED.

The first example shown below does not provide a NED identifier so ntool will 
prompt for one and the user selects (1) a Cisco IOS NED. Ntool then proceeds
to verify each of the commands contained with the sample.txt file. Any command
not supported by the NED is prefaced by '**'. A summary is provided detailing
the percentage of commands supported by the currently selected NED
```
admin@ncs> ntool verify verbose file /Users/dan/Desktop/commit-queue-overlap/sample.txt

Starting ntool-verify

	Read (24) lines from file: /Users/dan/Desktop/commit-queue-overlap/sample.txt
	Searching for existing NSO CLI based network element drivers

		0) arista-dcs-cli-5.11
		1) cisco-ios-cli-6.48
		2) cisco-iosxr-cli-7.23
		3) cisco-nx-cli-5.15
		4) fortinet-fortios-cli-5.4

		Select a ned-id from above: 1

	Proceeding with ned-id: cisco-ios-cli-6.48
	Verifying file        : /sample.txt

   no service pad
   service tcp-keepalives-in
   service tcp-keepalives-out
   service timestamps debug datetime msec localtime show-timezone
   service timestamps log datetime msec localtime show-timezone
   service password-encryption
   service sequence-numbers
   service call-home
   no platform punt-keepalive disable-kernel-core
   !
   hostname NYC
   !
   !
** my_unsuppored_cli_command
   vrf definition Mgmt-vrf
    !
    address-family ipv4
    exit-address-family
    !
    address-family ipv6
    exit-address-family
   !
   logging buffered informational
   no logging console

NSO Configuration Verify operation completed

============================================================
Verify Results Summary
============================================================

Elapsed Time                       : 0:00:05.115243
Network Config Command File        : /sample.txt
NSO Cli network element driver id  : cisco-ios-cli-6.48
Total Processed Configuration Lines: 24
Upsupported Configuration Lines    : 1
Duplicate unsupported Lines        : 0
Percent Supported                  : 95.83%
Percent Supported (No duplicates)  : 95.83% 

[ok][2020-04-15 16:52:28]
admin@ncs> 

```
## ntool template

The ntool template tool can be used in 3 ways.

    (1) Standalone mode execute the script by typing the following:
```
    dan@mycomp% python3 ntool_template.py --help
    usage: ntool_template.py [-h] [-c] [-f FILE] [-o OFILE] [-l LINE] [-n NEDID]
                             [-t TYPE] [-v] [-m TEMPLATE] [-u USERNAME]

    optional arguments:
      -h, --help            show this help message and exit
      -c, --command         command
      -f FILE, --file FILE  file
      -o OFILE, --ofile OFILE output file
      -l LINE, --line LINE  line
      -n NEDID, --nedid NEDID NSO NED identifier
      -t TYPE, --type TYPE  Template type
      -v, --verbose         verbose
      -u USERNAME, --username USERNAME
```
  (2) Executing the script from the NSO command line
```
  admin@ncs> ntool template
  Possible completions:
    command     - Command to parse
    file        - Command file
    ned-id      - Valid cli ned-id (Ned must be loaded in NSO)
    output-file - Command file
    verbose     - verbose output
```
  (3) An NSO action is provided to call the template generation tool programmatically

The first example shown below does not provide a NED identifier so ntool will
prompt for one and the user selects (1) a Cisco IOS NED. Ntool then proceeds
to verify each of the commands contained with the sample.txt file. Any command
not supported by the NED is prefaced by '**'. A summary is provided detailing
the percentage of commands supported by the currently selected NED
```
admin@ncs> ntool template verbose file ./sample.txt
Creating template  type [device] ....

	Searching for existing NSO CLI based network element drivers
		0) arista-dcs-cli-5.11
		1) cisco-ios-cli-6.48
		2) cisco-iosxr-cli-7.23
		3) cisco-nx-cli-5.15
		4) fortinet-fortios-cli-5.4

		Select a ned-id from above: 1

	Proceeding with ned-id: cisco-ios-cli-6.48
	Read (24) lines from file: /sample.txt
Template: 
<config xmlns="http://tail-f.com/ns/config/1.0">
  <devices xmlns="http://tail-f.com/ns/ncs">
  <template>
    <name>TEMP-NAME</name>
      <ned-id>
       <id>cisco-ios-cli-6.48</id>
      <config>
        <service xmlns="urn:ios">
          <conf>
            <pad>false</pad>
          </conf>
          <tcp-keepalives-in/>
          <tcp-keepalives-out/>
          <timestamps>
            <debug>
              <datetime>
                <msec/>
                <localtime/>
                <show-timezone/>
              </datetime>
            </debug>
            <log>
              <datetime>
                <msec/>
                <localtime/>
                <show-timezone/>
              </datetime>
            </log>
          </timestamps>
          <password-encryption/>
          <sequence-numbers/>
          <call-home/>
        </service>
        <platform xmlns="urn:ios">
          <punt-keepalive>
            <disable-kernel-core>false</disable-kernel-core>
          </punt-keepalive>
        </platform>
        <hostname xmlns="urn:ios">NYC</hostname>
        <vrf xmlns="urn:ios">
          <definition>
            <name>Mgmt-vrf</name>
            <address-family>
              <ipv4>
              </ipv4>
              <ipv6>
              </ipv6>
            </address-family>
          </definition>
        </vrf>
        <logging xmlns="urn:ios">
          <buffered>
            <severity-level>informational</severity-level>
          </buffered>
        </logging>
      </config>
     </ned-id>
    </template>
   </devices>
</config>

Template create completed

 
[ok][2020-04-15 17:04:25]
admin@ncs>
```

The next example provide shows how the template can be generated 
programmatically using the NSO RESTCONF API where the input data in the 
template.json file is show prior to the curl command

```
dan@DANISULL-M-73NJ % cat template.json
{
   "input" : {
      "ned-id" : "cisco-ios-cli-6.48",
      "command-list" : "aaa group server radius ISE\\n server name ISE-VIP-HKCM\\n!\\naaa authentication login aux group tacacs+ local\\naaa authentication login vty group tacacs+ local\\n"
   }
}
dan@DANISULL-M-73NJ % 


dan@DANISULL-M-73NJ % curl -X POST -u admin:admin -T template.json --header "Content-Type: application/yang-data+json" http://127.0.0.1:8080/restconf/operations/ntool:ntool-commands/create-template
{
  "ntool:output": {
    "result": "<config xmlns=\"http://tail-f.com/ns/config/1.0\">\n  <devices xmlns=\"http://tail-f.com/ns/ncs\">\n  <template>\n    <name>TEMP-NAME</name>\n      <ned-id>\n       <id>cisco-ios-cli-6.48</id>\n      <config>\n        <aaa xmlns=\"urn:ios\">\n          <group>\n            <server>\n              <radius>\n                <name>ISE\n</name>\n                <server>\n                  <name>\n                    <name>ISE-VIP-HKCM\n</name>\n                  </name>\n                </server>\n              </radius>\n            </server>\n          </group>\n        </aaa>\n      </config>\n     </ned-id>\n    </template>\n   </devices>\n</config>",
    "status": "success"
  }
}
```
