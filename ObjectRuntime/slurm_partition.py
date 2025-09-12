import base64
import subprocess
import os
from .wp_object import WPObject
from .slurm_job import WPSlurmJob


class WPSlurmPartition(WPObject):
    """
    Minimal representation of a Slurm partition object.
    """
    slurm_host: str

    def __init__(self, title: str, path: str, slurm_host: str) -> None:
        super().__init__(title, path)
        self.slurm_host = slurm_host

    def setSlurmHost(self, slurm_host: str) -> None:
        self.slurm_host = slurm_host

    def getJobs(self) -> list[WPSlurmJob]:
        with subprocess.Popen(["ssh", self.slurm_host, "squeue", "-p", self.title, "-h", "-o", "%i"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get number of jobs: {stderr.decode('utf-8')}")
            for job in stdout.decode('utf-8').splitlines():
                job_obj = WPSlurmJob(job, f"{self.path}/{job}")
                job_obj.setHost(self.host)
                job_obj.setPort(self.port)
                job_obj.setSlurmHost(self.slurm_host)
                self.children.append(job_obj)
    
    def getBadge(self) -> str:
        if self.children_count > 0:
            return f"{self.children_count}"
        else:
            return ""
    


