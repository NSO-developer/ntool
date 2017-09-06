package com.tailf.ntool;

import java.io.IOException;
import java.util.Iterator;
import java.util.ArrayList;
import java.util.Date;
import java.net.Socket;
import java.net.InetAddress;
import org.apache.log4j.Logger;

import com.tailf.ntool.namespaces.*;
import java.util.List;
import com.tailf.cdb.*;
import com.tailf.conf.*;
import com.tailf.ncs.*;
import com.tailf.dp.*;
import com.tailf.ncs.NcsMain;
import com.tailf.ncs.ns.Ncs;
import com.tailf.navu.*;
import com.tailf.maapi.*;
import com.tailf.dp.DpCallbackException;
import com.tailf.dp.annotations.ActionCallback;
import com.tailf.dp.annotations.DataCallback;
import com.tailf.dp.proto.ActionCBType;
import com.tailf.dp.proto.DataCBType;

public class ntoolAction {

    private static Logger LOGGER  = Logger.getLogger(ntoolAction.class);

    public ntoolAction() {

    }
    @ActionCallback(callPoint="ntool-commands-action-point",callType=ActionCBType.INIT)
    public void init(DpActionTrans trans) throws DpCallbackException {
    }

    @ActionCallback(callPoint="ntool-commands-action-point",callType=ActionCBType.ACTION)
    public ConfXMLParam[] action(DpActionTrans trans, ConfTag name,
                                 ConfObject[] kp, ConfXMLParam[] params)
        throws DpCallbackException, IOException
        {
            ConfXMLParam[] result = null;
            ////
            // Check which UNI action we should invoke
            ////
            try {

               ntoolActionHandler nTool = 
                       new ntoolActionHandler(params);

               switch (name.getTagHash()) {
            
                 case ntool._verify:
                    trans.actionSetTimeout(300);
                    nTool.validate(params);
                    break;
                 case ntool._create_template:
                    nTool.createTemplate(params);
                    break;
               }
 
               // Create the return array
               result = nTool.output.toArray(new ConfXMLParam[0]);

               return(result);
            }
            catch (Exception e) {
               LOGGER.error("ntool Action exception:", e);
            }
            return(null);
        }

    public static String getStringParam(ConfXMLParam [] params,
                                        String name) {

        for (int i=0; i <  params.length; i++) {

            if (params[i].getTag().equals(name)) {
                return(params[i].getValue().toString());
            }
        }
        return (null);
    }
}
