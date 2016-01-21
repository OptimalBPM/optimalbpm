import os
import servicemanager
import socket
import sys
import win32event
import win32service

import win32serviceutil

# The directory of the current file
script_dir = os.path.dirname(__file__)

# Add relative optimal bpm path
sys.path.append(os.path.join(script_dir, "../../"))

from of.common.win32svc import write_to_event_log
import of.agent.agent


class AppServerSvc (win32serviceutil.ServiceFramework):
    _svc_name_ = "Optimal BPM Agent"
    _svc_display_name_ = "The Optimal BPM Agent Service"

    def __init__(self,args):
        win32serviceutil.ServiceFramework.__init__(self,args)
        self.hWaitStop = win32event.CreateEvent(None,0,0,None)
        socket.setdefaulttimeout(60)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        _exit_status = of.agent.agent.stop_agent()
        self.ReportServiceStatus(win32service.SERVICE_STOPPED)
        os.exit(_exit_status)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_,''))
        self.main()

    def main(self):
        try:
            of.agent.agent.start_agent()
        except Exception as e:
            write_to_event_log("Application", 1, "Error starting agent", str(e))

if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)