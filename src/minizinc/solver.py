import contextlib
import json
import re
import tempfile
from typing import List, Optional, Tuple

import minizinc

from .model import Instance


class Solver:
    # Solver identifier for MiniZinc driver
    _id: Optional[str]
    # Solver Configuration Options
    version: Tuple[int, int, int]
    mznlib: str
    tags: List[str]
    stdFlags = List[str]
    extraFlags = List[str]
    executable: str
    supportsMzn: bool
    supportsFzn: bool
    needsSolns2Out: bool
    needsMznExecutable: bool
    needsStdlibDir: bool
    isGUIApplication: bool

    def __init__(self, name: str, version: str, executable: str, driver=None):
        if driver is None:
            driver = minizinc.default_driver
        self.driver = driver

        # Set required fields
        self.name = name
        self._id = None
        match = re.search(r"(\d+)\.(\d+)\.(\d+)", version)
        self.version = tuple([int(i) for i in match.groups()])
        self.executable = executable

        # Initialise optional fields
        self.mznlib = ""
        self.tags = []
        self.stdFlags = []
        self.extraFlags = []
        self.supportsMzn = False
        self.supportsFzn = True
        self.needsSolns2Out = False
        self.needsMznExecutable = False
        self.needsStdlibDir = False
        self.isGUIApplication = False

    @property
    def id(self) -> str:
        if self._id is None:
            return "org.minizinc.python." + self.name.lower()
        else:
            return self._id

    @contextlib.contextmanager
    def configuration(self) -> str:
        file = None
        if self._id is None:
            file = tempfile.NamedTemporaryFile(prefix="minizinc_solver_", suffix=".msc")
            file.write(self.to_json().encode())
            file.flush()
            file.seek(0)
            self._id = file.name
        try:
            yield self._id
        finally:
            if file is not None:
                file.close()
                self._id = None

    def solve(self, instance: Instance, *args, **kwargs):
        """
        Forwarding method to the driver's solve method using the solver configuration
        :param instance: the MiniZinc instance to be solved
        :param args, kwargs: accepts all other arguments found in the drivers solve method
        :return: A result object containing the solution to the instance
        """
        if self.driver is not None:
            return self.driver.solve(self, instance, *args, **kwargs)
        else:
            raise LookupError("Solver is not linked to a MiniZinc driver")

    def to_json(self):
        info = {
            "name": self.name,
            "version": ".".join([str(i) for i in self.version]),
            "id": self.id,
            "executable": self.executable,
            "mznlib": self.mznlib,
            "tags": self.tags,
            "stdFlags": self.stdFlags,
            "extraFlags": self.extraFlags,
            "supportsMzn": self.supportsMzn,
            "supportsFzn": self.supportsFzn,
            "needsSolns2Out": self.needsSolns2Out,
            "needsMznExecutable": self.needsMznExecutable,
            "needsStdlibDir": self.needsStdlibDir,
            "isGUIApplication": self.isGUIApplication,
        }

        return json.dumps(info, sort_keys=True, indent=4)

    def __setattr__(self, key, value):
        if key in ["version", "executable", "mznlib", "tags", "stdFlags", "extraFlags", "supportsMzn", "supportsFzn",
                   "needsSolns2Out", "needsMznExecutable", "needsStdlibDir", "isGUIApplication"] \
                and getattr(self, key, None) is not value:
            self._id = None
        return super().__setattr__(key, value)