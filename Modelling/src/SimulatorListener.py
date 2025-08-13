# This script is a Windows service that listens for PostgreSQL NOTIFY event which will trigger a simulator model run.

import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import logging
import psycopg2
import select

class PGListenerService(win32serviceutil.ServiceFramework):
    _svc_name_ = "PGListenerService"
    _svc_display_name_ = "PostgreSQL Listener Service"
    _svc_description_ = "Listens for PostgreSQL NOTIFY events and triggers actions."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)
        self.running = True

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))
        self.main()

    def main(self):
        logging.basicConfig(filename='pg_listener.log', level=logging.INFO,
                            format='%(asctime)s [%(levelname)s] %(message)s')
        try:
            conn = psycopg2.connect("dbname=your_db user=your_user password=your_pass host=your_host")
            conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
            cur = conn.cursor()
            cur.execute("LISTEN data_ready;")
            logging.info("Listening for PostgreSQL notifications...")

            while self.running:
                if select.select([conn], [], [], 5) == ([], [], []):
                    continue
                conn.poll()
                while conn.notifies:
                    notify = conn.notifies.pop(0)
                    logging.info(f"Received notification: {notify.payload}")
                    # Trigger your script or logic here
        except Exception as e:
            logging.error(f"Service error: {e}")


if __name__ == '__main__':
    PGListenerService.parse_command_line()
