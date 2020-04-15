# -*- mode: python; python-indent: 4 -*-
import ncs
import _ncs
from ncs.application import Service
import ncs.template
import ncs.maagic as maagic
import ncs.maapi as maapi
import re
import threading
import time
from ncs.dp import Action, _tm
from ncs.application import Application
import socket
from ntool_template import NtoolTemplate

########################################################
# Onboard Action
########################################################
class ActionHandler(Action):
    """This class implements the Device Onboarding Action class."""

    @Action.action
    def cb_action(self, uinfo, name, kp, input, output):
        
        output.status = 'success'
        
        try:
           self.log.info("NtoolTemplateCreate: Creating {0} template ned-id: {1}".format(input.type, input.ned_id))
           

           cto = NtoolTemplate(uinfo.username, input.ned_id, input.type)

           cto.find_ned_ids()

           if input.ned_id not in cto.cli_neds:
              self.log.info("NtoolTemplateCreate: Invalid ned id {0}".format(input.ned_id))
              output.status = 'invalid ned id specified'      
              return

           self.log.info("NtoolTemplateCreate: Valid ned id {0} proceeding".format(input.ned_id))  
           self.log.debug("NtoolTemplateCreate: [{0}]".format(input.command_list))
           cto.process_cmd_line(input.command_list)
           
           for cmd in cto.cmd_list:
              self.log.debug("\n[{0}]".format(cmd))

           # Convert fortinet config into IOS format before consuming it
           if 'fortinet-fortios-cli-5' in input.ned_id:
               cto.preprocess_fortinet() 

           self.log.info("NtoolTemplateCreate: generating template".format(input.ned_id))
           cto.template_build()
           self.log.debug("NtoolTemplateCreate: Template Created\n{0}".format(cto.template))

           output.result = cto.template

        except Exception as e:
           self.log.error("NTool template generation operation failed")
           output.status = 'failed'
           output.error_message = 'NTool template generaton error:{0}'.format(e) 
           self.log.error(e)


        return ncs.CONFD_OK

class ServiceActions(ncs.application.Application):
    def setup(self):
       
        self.log.info('NTool Template Action(s) Registering')
        self.register_action('ntool-template-action-point', ActionHandler, [])
        self.log.info('Ntool Template Action(s) Registration Completed...')

    def teardown(self):

        self.log.info('Actions FINISHED')
