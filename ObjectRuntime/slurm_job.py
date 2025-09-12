import base64
import subprocess
import os
from .wp_object import WPObject


class WPSlurmJob(WPObject):
    """
    Minimal representation of a Slurm job object.
    """
    state: str # Pending or Running

    def __init__(self, title: str, path: str) -> None:
        super().__init__(title, path)
        # get number of jobs in the partition
        self.children = []
        self.state = "Pending"
    
    def getBadge(self) -> str:
        return self.state



