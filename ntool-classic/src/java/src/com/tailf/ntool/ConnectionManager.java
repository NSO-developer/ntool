package com.tailf.ntool;

import java.io.IOException;
import java.util.Iterator;
import java.util.ArrayList;
import java.util.Date;
import java.util.EnumSet;
import java.net.Socket;
import java.net.InetAddress;
import org.apache.log4j.Logger;
import java.util.List;
import com.tailf.cdb.*;
import com.tailf.maapi.*;
import com.tailf.ncs.NcsMain;
import com.tailf.conf.*;
import com.tailf.cdb.CdbDBType;
import com.tailf.cdb.CdbLockType;


class ConnectionManager {

    public static Socket newNcsSock()
        throws IOException
    {
        NcsMain ncsServ = NcsMain.getInstance();
        return new Socket(ncsServ.getNcsHost(),ncsServ.getNcsPort());
    }

    public static void closeNcsSock(Socket ncsSock, Logger log) {
        if (ncsSock!=null)
            try {
                ncsSock.close();
            } catch (Exception e) {
                if (log!=null)
                    log.warn("NCS socket is not closed: "+e.getMessage());
            };
    }

    public static CdbSession getNewCdbOperSession(Class caller)
        throws IOException, ConfException
    {
        Cdb cdb = new Cdb(caller.getName()+"-cdb-operational", newNcsSock());
        return cdb.startSession(CdbDBType.CDB_OPERATIONAL,  EnumSet.of(CdbLockType.LOCK_REQUEST,
                                                                       CdbLockType.LOCK_WAIT));
    }

    public static CdbSession getNewCdbRunnSession(Class caller)
        throws IOException, ConfException
    {
        Cdb cdb = new Cdb(caller.getName()+"-cdb-running", newNcsSock());
        return cdb.startSession(CdbDBType.CDB_RUNNING);
    }

    public static CdbSession getNewCdbUpgradeSession(Class caller)
        throws IOException, ConfException
    {
        Cdb cdb = new Cdb("upgrade-"+caller.getName()+"-cdb-running",
                          newNcsSock());
        cdb.setUseForCdbUpgrade();
        return cdb.startSession(CdbDBType.CDB_RUNNING);
    }

    public static void closeCdbSession(CdbSession session, Logger log) {
        if (session!=null) {
            Socket ncsSock = session.getCdb().getSocket();
            try {
                session.endSession();
            } catch (Exception e) {
                if (log!=null)
                    log.warn("CDB session is not closed: "+e.getMessage());
            }
            closeNcsSock(ncsSock, log);
        }
    }

    public static Maapi getNewMaapi()
        throws IOException, ConfException
    {
        return new Maapi(newNcsSock());
    }

    public static int openMaapiWrite(Maapi maapi)
        throws IOException, ConfException
    {
            maapi.startUserSession("admin",
                                  InetAddress.getLocalHost(),
                                  "maapi",
                                  new String[] { "admin" },
                                  MaapiUserSessionFlag.PROTO_TCP);

           int th = maapi.startTrans(Conf.DB_RUNNING,Conf.MODE_READ_WRITE);

        return th;
    }
    public static int openMaapiRead(Maapi maapi)
        throws IOException, ConfException
    {
            maapi.startUserSession("admin",
                                  InetAddress.getLocalHost(),
                                  "maapi",
                                  new String[] { "admin" },
                                  MaapiUserSessionFlag.PROTO_TCP);

           int th = maapi.startTrans(Conf.DB_RUNNING,Conf.MODE_READ);

        return th;
    }
    public static int startTrans(Maapi maapi) 
       throws IOException, ConfException
    {
        int th = maapi.startTrans(Conf.DB_RUNNING,Conf.MODE_READ);

        return th;
    }
    public static void finishTrans(Maapi maapi, int th) 
       throws IOException, ConfException
    {
        maapi.finishTrans(th);

        return;
    } 
    public static void applyMaapi(Maapi maapi, int th, Logger log) {

    }
    public static void closeMaapi(Maapi maapi, int th, Logger log) {
        closeMaapiSock(maapi, log);
    }

    public static void closeMaapiSock(Maapi maapi, Logger log) {
        if (maapi!=null)
            closeNcsSock(maapi.getSocket(), log);
    }
}
