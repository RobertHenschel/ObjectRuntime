import base64
import subprocess
import os
from .wp_object import WPObject


class WPSlurmJob(WPObject):
    """
    Minimal representation of a Slurm job object.
    """


    def __init__(self, title: str, path: str, host: str | None = None, port: int | None = None) -> None:
        super().__init__(title, path, host=host, port=port)
        resource_path = os.path.join(os.path.dirname(__file__), "Resources", "Job.png")
        with open(resource_path, "rb") as f:
            self.icon = base64.b64encode(f.read()).decode("utf-8")
            self.setIcon(self.icon)
        # get number of jobs in the partition
        self.children = []



