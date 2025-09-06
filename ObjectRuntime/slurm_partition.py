import base64
import subprocess
import os
from .slurm_batch_system import WPSlurmBatchSystem
from .slurm_job import WPSlurmJob


class WPSlurmPartition(WPSlurmBatchSystem):
    """
    Minimal representation of a Slurm partition object.
    """


    def __init__(self, title: str, path: str, slurm_host: str) -> None:
        super().__init__(title, path, slurm_host)
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Partition.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")
            self.setIcon(self.icon)

    def getJobs(self) -> list[WPSlurmJob]:
        with subprocess.Popen(["ssh", self.slurm_host, "squeue", "-p", self.title, "-h", "-o", "%i"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get number of jobs: {stderr.decode('utf-8')}")
            for job in stdout.decode('utf-8').splitlines():
                self.children.append(WPSlurmJob(job, f"{self.path}/{job}", self.host, self.port))
    
    def getBadge(self) -> str:
        return f"{len(self.children)}"
    


