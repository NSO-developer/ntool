package com.tailf.ntool;

import java.io.IOException;
import java.util.Iterator;
import java.util.ArrayList;
import java.util.Date;
import java.net.Socket;
import java.net.InetAddress;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.util.EnumSet;
import java.io.BufferedReader;
import java.io.InputStreamReader;
import org.apache.log4j.Logger;

import com.tailf.ntool.namespaces.*;
import java.util.*;
import com.tailf.cdb.*;
import com.tailf.ha.*;
import com.tailf.conf.*;
import com.tailf.ncs.NcsMain;
import com.tailf.dp.*;
import com.tailf.ncs.NcsMain;
import com.tailf.ncs.ns.Ncs;
import com.tailf.navu.*;
import com.tailf.maapi.*;

public class ntoolActionHandler {

  private static Logger LOGGER  = Logger.getLogger(ntoolActionHandler.class);

  public ConfNamespace ns;
  public ConfXMLParam [] params;
  public int errorCode = 0;
  public int sreh;
  public String errorMsg = null;
  public List<ConfXMLParam> output;
  public Maapi  maapi;
  public int th;
  public CdbSession session;
  public NavuContext ctx;
  public String lineNo = null;
  public String line = null;
  private final String tempDevName = "TEMP_DEVICE";
  private final String templateName = "mytmpl";
  private String result = "verfied";
  public ntoolActionHandler(ConfXMLParam[] paramList) {

    errorCode = 0;
    errorMsg = null;
    try {
      this.params = paramList;
      this.ns     = new ntool();
      this.sreh   = new ntool().hash();
      this.output    = new ArrayList<ConfXMLParam>();
      this.maapi = ConnectionManager.getNewMaapi();
      this.th = ConnectionManager.openMaapiWrite(maapi);
      this.session = ConnectionManager.getNewCdbOperSession(this.getClass());
      this.ctx = new NavuContext(maapi, th);
    }
    catch(Exception e) {
      LOGGER.error("ActionHandler: Constructor failed to initialize: ", e);
    }
  }
   //////////////////////////////////////////////////////////////////
   // createTemplate
   //////////////////////////////////////////////////////////////////
   public void createTemplate(ConfXMLParam[] params) {

      try {

        String tempType     = getStringParam(ntool._type_);
        String devType = getStringParam(ntool._device_type_);
        String cmds       = getStringParam(ntool._command_list_);
        
        String tempDev = "/devices/device{" + tempDevName + "}";
        String template = "/devices/template{" + templateName + "}";

        EnumSet<MaapiConfigFlag> 
             flags = EnumSet.of(MaapiConfigFlag.CISCO_IOS_FORMAT,
                                MaapiConfigFlag.MAAPI_CONFIG_REPLACE,
                                MaapiConfigFlag.MAAPI_CONFIG_CONTINUE_ON_ERROR);
                                
        
        if (devType.equals("iosxr")) {
          flags = EnumSet.of(MaapiConfigFlag.CISCO_XR_FORMAT,
                             MaapiConfigFlag.MAAPI_CONFIG_REPLACE,
                             MaapiConfigFlag.MAAPI_CONFIG_CONTINUE_ON_ERROR);
                            
        }
        if (devType.equals("junos")) {
          flags = EnumSet.of(MaapiConfigFlag.JUNIPER_CLI_FORMAT,
                             MaapiConfigFlag.MAAPI_CONFIG_REPLACE,
                             MaapiConfigFlag.MAAPI_CONFIG_CONTINUE_ON_ERROR);
                             
        }

        LOGGER.debug("verify: [" + devType + "]\n" + cmds);

        maapi.create(th, tempDev);
        maapi.loadConfigCmds(th,
                             flags,
                             cmds,
                             tempDev + "/config");
       MaapiInputStream mis = maapi.saveConfig(th, EnumSet.of(
                                               MaapiConfigFlag.MAAPI_CONFIG_XML_PRETTY
                                                ),
                                                tempDev + "/config");
        BufferedReader br = new BufferedReader(new InputStreamReader(mis));
        String line = "";
        StringBuilder config = new StringBuilder();
        while (line != null) {
            config.append(line + "\n");
            line = br.readLine();
        }
        result = config.toString();

        
        result = result.replaceFirst("<config ", "<config-template ");
        result = result.replace("<name>TEMP_DEVICE</name>", "<name>{$DEVICE}</name>");
        result = result.replace("  </devices>\n</config>", "</devices>\n</config-template>");

        LOGGER.debug("Config generated: " + result);
        
        maapi.delete(th, tempDev);

      }
      catch (ConfException e) {
        result = e.getMessage();
        LOGGER.info("Parsing issues " + result);
        //LOGGER.error ("unknown command: ", e);
      }
      catch (Exception e) {
        result = "ntool: Unexpected exception";
        LOGGER.error ("createTemplate: ", e);
      }
      finally {
       setReturn();
       ConnectionManager.closeMaapiSock(maapi, LOGGER);
       ConnectionManager.closeCdbSession(session, LOGGER);
      }
    }
   //////////////////////////////////////////////////////////////////
   // validate
   //////////////////////////////////////////////////////////////////
   public void validate(ConfXMLParam[] params) {
      String cmds = null;
      try {

        String devType = getStringParam(ntool._device_type_);
        cmds       = getStringParam(ntool._command_list_);        
        String tempDev = "/devices/device{" + tempDevName + "}";
        String template = "/devices/template{" + templateName + "}";

        EnumSet<MaapiConfigFlag> 
             flags = EnumSet.of(MaapiConfigFlag.CISCO_IOS_FORMAT,
                                MaapiConfigFlag.CONFIG_SUPPRESS_ERRORS,
                                MaapiConfigFlag.MAAPI_CONFIG_REPLACE);
                                
        
        if (devType.equals("iosxr")) {
          flags = EnumSet.of(MaapiConfigFlag.CISCO_XR_FORMAT,
                             MaapiConfigFlag.CONFIG_SUPPRESS_ERRORS,
                             MaapiConfigFlag.MAAPI_CONFIG_REPLACE);
                            
        }
        if (devType.equals("arista")) {
          flags = EnumSet.of(MaapiConfigFlag.CISCO_IOS_FORMAT,
                             MaapiConfigFlag.CONFIG_SUPPRESS_ERRORS,
                             MaapiConfigFlag.MAAPI_CONFIG_REPLACE);
                            
        }
        if (devType.equals("junos")) {
          flags = EnumSet.of(MaapiConfigFlag.JUNIPER_CLI_FORMAT,
                             MaapiConfigFlag.CONFIG_SUPPRESS_ERRORS,
                             MaapiConfigFlag.MAAPI_CONFIG_REPLACE);
                             
        }

        maapi.create(th, tempDev);

             maapi.loadConfigCmds(th,
                               flags,
                               cmds,
                               tempDev + "/config");

        maapi.delete(th, tempDev);
      }
      catch (ConfException e) {
        LOGGER.error("Error validating command sequence: \n" + cmds);
        LOGGER.error ("unknown command: " + e.getMessage());
        result = e.getMessage();
      }
      catch (Exception e) {
        result = "ntool: Unexpected exception";
        LOGGER.error ("verify: ", e);
      }
      finally {
       setReturn();
       ConnectionManager.closeMaapiSock(maapi, LOGGER);
       ConnectionManager.closeCdbSession(session, LOGGER);
      }
    }

    //////////////////////////////////////////////////////////////////
    //  Helper functions
    //////////////////////////////////////////////////////////////////

   private void setReturn() {

        try {
        
          output.add(new ConfXMLParamValue(sreh,
                                           ntool._result,
                                           new ConfBuf(result)));

        }
        catch (Exception e) {

            LOGGER.error ("Error setting error header", e);
        }
    }

    private String getStringParam(String name) {

        for (int i=0; i <  params.length; i++) {

            if (params[i].getTag().equals(name)) {
                return(params[i].getValue().toString());
            }
        }
        return (null);
    }
}
