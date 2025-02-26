from device_abc import abstractIPC
import os
import subprocess



class FluostarOmega(abstractIPC):
    def connect_device(self):

        # Replace these paths
        path_to_32bit_python = r"C:\Program Files (x86)\Python313-32\python.exe"

        # Get the directory of the 32 bit script
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Construct the full path to the 32-bit script
        script_path = os.path.join(current_dir, "python_ipc_32.py")
        #path_to_script = r"C:\Path\To\your\32bit_script.py"
        try:
            proc = subprocess.Popen([path_to_32bit_python, script_path])
            self.client_pid = proc
        except Exception as e:
            print("Failed to start subprocess:", e)
        else:
            print("Subprocess started successfully with PID:", proc.pid)
