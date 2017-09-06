# tail-ntool

A few tools to help with verifying CLI configurations and generating NSO templates

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

* NSO 4.4.2.1+
* Python 2.7+ or 3+

# Build instructions

   make -C packages/tailf-ntool/src clean all

# Usage examples

## Cli Generated Templates

This option can be used to autogenerate if not entire, partial template files
for NSO service packages. The tool when called will search for a particular
directory within the NSO package called 'cli'. Each file within the CLI directory
will be a config file which will contain a set of variables and CLI
commands. Ntool will parse the .cfg files and generate a template based on 
the loaded NED version into a 'gen' directory. 
 
.cfg files have the following format:
+NED:cisco-iosxr            First line of every .cfg file is the NED
                            package name
variables                   Variables are denoted by {$XXXXX}
                              - Variables can be assigned a unique  
                                default value for template generation
                              - Variables which require a null check
                                in the XML template can be assigned
                                the initial value nonull
+TAGMOD:tagname, value        - TAGMOD can be inserted into the cfg file
                                in order to substitue a value for a given
                                element in the template.

Consider the following example:

bridge_group.cfg:

+NED:cisco-iosxr            First line of every .cfg file is the NED required

l2vpn
  bridge group {$BG-NAME}
   bridge-domain {$BG-NAME}
    mac
      withdraw state-down
    exit
    mtu 9800
    vfi {$BG-NAME}
     vpn-id {$VPN-ID=34}
     autodiscovery bgp
      rd auto
      route-target {$BG-ROUTE-TARGET}
     exit
    exit
   exit
  exit
exit


## Verify

Any "**" means the the specific command isn't supported

admin@ncs> ntool verify type iosxr file /Users/dan/Desktop/router_cfg.txt
   mpls ldp
    log
**   hello-adjacency
     neighbor
     nsr
     session-protection
    !
    nsr
    igp sync delay on-session-up 20
    router-id 1.1.0.1
    neighbor
     password encrypted 060506324F41
    !
    session protection
    address-family ipv4
     label
      local
       allocate for host-routes
      !
     !
    !

## Template

You can also generate a template directory from a CLI command if necessary
Using the ospf.text file contents:
  router ospf 1
   nsr
   router-id 1.1.0.1
   authentication message-digest keychain KEY-OSPF-1
   packet-size 800
   network point-to-point
   mpls ldp sync
   mtu-ignore enable
   mpls ldp auto-config
   fast-reroute per-link
   timers throttle lsa all 10 100 1000
   timers throttle spf 50 200 1000
   timers lsa min-arrival 50
   timers pacing flood 5
   auto-cost reference-bandwidth 100000
   redistribute static metric 1 metric-type 1 route-policy RPY-OSPF-RedistStatic
   redistribute bgp 65000
   redistribute ospf OSPF-Legacy metric-type 1 route-policy RPY-OSPF1-FromOSPFLegacy-v00
   area 0
    bfd minimum-interval 150
    bfd fast-detect
    bfd multiplier 3
    mpls traffic-eng
    interface Loopback0
     passive enable
    !
    interface GigabitEthernet0/0/0/0.102
     cost 60000
    !
    interface GigabitEthernet0/0/0/0.104
     cost 60000
    !
    interface GigabitEthernet0/0/0/0.105
     cost 60000
    !
    interface GigabitEthernet0/0/0/0.108
     cost 60000
    !
  !

admin@ncs> ntool template type iosxr template-type config file /Users/Dan/Desktop/ospf.text                      

   Creating template  [iosxr] ....
   Reading input command file /Users/Dan/Desktop/ospf.text
   Executing template create action....

<config-template xmlns="http://tail-f.com/ns/config/1.0">
  <devices xmlns="http://tail-f.com/ns/ncs">
  <device>
    <name>{$DEVICE}</name>
      <config>
        <router xmlns="http://tail-f.com/ned/cisco-ios-xr">
          <ospf>
            <name>1</name>
            <authentication>
              <message-digest>
                <keychain>KEY-OSPF-1</keychain>
              </message-digest>
            </authentication>
            <nsr/>
            <router-id>1.1.0.1</router-id>
            <mtu-ignore>
              <mode>enable</mode>
            </mtu-ignore>
            <fast-reroute>
              <per-link>
              </per-link>
            </fast-reroute>
            <timers>
              <throttle>
                <lsa>
                  <all>
                    <delay>10</delay>
                    <min-delay>100</min-delay>
                    <max-delay>1000</max-delay>
                  </all>
                </lsa>
                <spf>
                  <delay>50</delay>
                  <min-delay>200</min-delay>
                  <max-delay>1000</max-delay>
                </spf>
              </throttle>
              <lsa>
                <min-arrival>50</min-arrival>
              </lsa>
              <pacing>
                <flood>5</flood>
              </pacing>
            </timers>
            <auto-cost>
              <reference-bandwidth>100000</reference-bandwidth>
            </auto-cost>
            <network>
              <point-to-point/>
            </network>
            <redistribute>
              <ospf>
                <id>OSPF-Legacy</id>
                <metric-type>1</metric-type>
                <route-policy>RPY-OSPF1-FromOSPFLegacy-v00</route-policy>
              </ospf>
              <bgp>
                <id>65000</id>
              </bgp>
              <static>
                <metric>1</metric>
                <metric-type>1</metric-type>
                <route-policy>RPY-OSPF-RedistStatic</route-policy>
              </static>
            </redistribute>
            <area>
              <id>0</id>
              <bfd>
                <minimum-interval>150</minimum-interval>
                <fast-detect>
                </fast-detect>
                <multiplier>3</multiplier>
              </bfd>
              <mpls>
                <traffic-eng/>
              </mpls>
              <interface>
                <name>GigabitEthernet0/0/0/0.102</name>
                <cost>60000</cost>
              </interface>
              <interface>
                <name>GigabitEthernet0/0/0/0.104</name>
                <cost>60000</cost>
              </interface>
              <interface>
                <name>GigabitEthernet0/0/0/0.105</name>
                <cost>60000</cost>
              </interface>
              <interface>
                <name>GigabitEthernet0/0/0/0.108</name>
                <cost>60000</cost>
              </interface>
              <interface>
                <name>Loopback0</name>
                <passive>
                  <mode>enable</mode>
                </passive>
              </interface>
            </area>
            <mpls>
              <ldp>
                <sync/>
                <auto-config/>
              </ldp>
            </mpls>
          </ospf>
        </router>
      </config>
  </device>
</devices>
</config-template>

   Template create completed

