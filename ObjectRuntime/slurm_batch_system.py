import base64
import subprocess
import socket
import struct
import json
import os
from typing import TYPE_CHECKING
from .wp_object import WPObject
if TYPE_CHECKING:
    from .slurm_partition import WPSlurmPartition  # for type hints only

class WPSlurmBatchSystem(WPObject):
    """
    Minimal representation of a Slurm batch system object.

    Properties:
        - icon: base64-encoded PNG image data (str)
        - title: human-readable title (str)

    Methods:
        - getTitle(): return the title for display in the viewer
    """
    slurm_host: str

    # Create a constructor that takes the title as an argument
    def __init__(self, title: str, path: str, slurm_host: str) -> None:
        super().__init__(title, path)
        self.slurm_host = slurm_host
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Slurm.png")
        with open(resource_path, "rb") as f:
            icon = base64.b64encode(f.read()).decode("utf-8")
            self.setIcon(icon)
    

    # create a function that uses the slurm binaries to list all partitions
    # ssh into "hostname" first using the current user
    def getPartitions(self):
        # Single SSH call: get partitions with job counts
        script = 'sinfo -h -o %P | sed "s/\\*$//" | while read p; do echo "$p $(squeue -h -p "$p" | wc -l)"; done'
        with subprocess.Popen(["ssh", self.slurm_host, script], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get partitions and counts: {stderr.decode('utf-8')}")

        self.children = []
        for line in stdout.decode('utf-8').splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                parts = line.split()
                if len(parts) >= 2:
                    part = parts[0]
                    count = int(parts[1])
                else:
                    continue
            except Exception:
                continue
            
            from .slurm_partition import WPSlurmPartition  # local import to avoid cycle
            obj = WPSlurmPartition(part, f"{self.path}/{part}", self.slurm_host)
            obj.children_count = count
            self.children.append(obj)
    
    