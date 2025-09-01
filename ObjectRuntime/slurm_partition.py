import base64
import subprocess
import os
from .wp_object import WPObject
from .slurm_job import WPSlurmJob


class WPSlurmPartition(WPObject):
    """
    Minimal representation of a Slurm partition object.
    """


    def __init__(self, title: str, path: str, host: str | None = None, port: int | None = None) -> None:
        super().__init__(title, path, host=host, port=port)
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Partition.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")
            self.setIcon(self.icon)
        # get number of jobs in the partition
        self.children = self._get_jobs()

    def getTitle(self) -> str:
        return self.title

    def getIcon(self) -> str:
        return self.icon

    def _get_jobs(self) -> list[WPSlurmJob]:
        with subprocess.Popen(["squeue", "-p", self.title, "-h", "-o", "%i"], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get number of jobs: {stderr.decode('utf-8')}")
            for job in stdout.decode('utf-8').splitlines():
                self.children.append(WPSlurmJob(job, f"{self.path}/{job}", self.host, self.port))
            return self.children
    


