import base64
import subprocess
import os
from .wp_object import WPObject


class WPSlurmJob(WPObject):
    """
    Minimal representation of a Slurm job object.
    """
    state: str # Pending or Running
    slurm_host: str

    def __init__(self, title: str, path: str) -> None:
        super().__init__(title, path)
        # get number of jobs in the partition
        self.children = []
        self.state = "Pending"
        self.slurm_host = None
    
    def setSlurmHost(self, slurm_host: str) -> None:
        self.slurm_host = slurm_host

    def getBadge(self) -> str:
        return self.state
    
    def wp_open(self, view: str = None) -> None:
        super().wp_open(view)



