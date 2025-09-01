import base64
import subprocess
from .wp_object import WPObject


class WPSlurmPartition(WPObject):
    """
    Minimal representation of a Slurm partition object.
    """
    title: str # partition name
    icon: str
    path: str
    num_jobs: int
    host: str
    port: int

    def __init__(self, title: str, path: str, host: str | None = None, port: int | None = None) -> None:
        import os
        super().__init__(title, host=host, port=port)
        self.path = path
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Partition.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")
        # get number of jobs in the partition
        self.num_jobs = self._get_num_jobs()

    def getTitle(self) -> str:
        return self.title

    def getIcon(self) -> str:
        return self.icon
    
    def getNumJobs(self) -> int:
        return self.num_jobs

    def _get_num_jobs(self) -> int:
        with subprocess.Popen(["squeue", "-p", self.title], stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            stdout, stderr = proc.communicate()
            if proc.returncode != 0:
                raise RuntimeError(f"Failed to get number of jobs: {stderr.decode('utf-8')}")
            return len(stdout.decode('utf-8').splitlines()) -1 #-1 because of the header
    
    def wp_open_icon_view(self) -> None:
        print(f"Opening icon view for {self.title}")


