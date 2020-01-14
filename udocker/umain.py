# -*- coding: utf-8 -*-
"""Implements most of the command line interface."""

import sys
import os
from udocker.msg import Msg
from udocker.cmdparser import CmdParser
from udocker.config import Config
from udocker.container.localrepo import LocalRepository
from udocker.cli import UdockerCLI
# from udocker.helper.hostinfo import HostInfo


class UMain(object):
    """These methods correspond directly to the commands that can
    be invoked via the command line interface.
    """

    def __init__(self, argv):
        """Initialize variables of the class"""
        self.argv = argv
        self.cmdp = None
        self.local = None
        self.cli = None

    def _prepare_exec(self):
        """Prepare configuration, parse and execute the command line"""
        self.cmdp = CmdParser()
        self.cmdp.parse(self.argv)
        if not (os.geteuid() or self.cmdp.get("--allow-root", "GEN_OPT")):
            Msg().err("Error: do not run as root !")
            sys.exit(1)

        if self.cmdp.get("--config=", "GEN_OPT"):
            conf_file = self.cmdp.get("--config=", "GEN_OPT")
            Config().getconf(conf_file)
        else:
            Config().getconf()

        if (self.cmdp.get("--debug", "GEN_OPT") or
                self.cmdp.get("-D", "GEN_OPT")):
            Config.conf['verbose_level'] = Msg.DBG
        elif (self.cmdp.get("--quiet", "GEN_OPT") or
              self.cmdp.get("-q", "GEN_OPT")):
            Config.conf['verbose_level'] = Msg.MSG

        Msg().setlevel(Config.conf['verbose_level'])
        if self.cmdp.get("--insecure", "GEN_OPT"):
            Config.conf['http_insecure'] = True

        self.local = "localrepo"   # Temporary hack

        if self.cmdp.get("--repo=", "GEN_OPT"):  # override repo root tree
            Config.conf['topdir'] = self.cmdp.get("--repo=", "GEN_OPT")
            self.local = LocalRepository()
            if not self.local.is_repo():
                Msg().err("Error: invalid udocker repository:",
                          Config.conf['topdir'])
                sys.exit(1)

        self.local = LocalRepository()
        if not self.local.is_repo():
            Msg().out("Info: creating repo: " + Config.conf['topdir'],
                      l=Msg.INF)
            self.local.create_repo()

        self.cli = UdockerCLI(self.local)

    def execute(self):
        """Command parsing and selection"""
        exit_status = 0
        self._prepare_exec()
        cmds = {
            "search": self.cli.do_search, "help": self.cli.do_help,
            "images": self.cli.do_images, "pull": self.cli.do_pull,
            "create": self.cli.do_create, "ps": self.cli.do_ps,
            "run": self.cli.do_run, "version": self.cli.do_version,
            "rmi": self.cli.do_rmi, "mkrepo": self.cli.do_mkrepo,
            "import": self.cli.do_import, "load": self.cli.do_load,
            "export": self.cli.do_export, "clone": self.cli.do_clone,
            "protect": self.cli.do_protect, "rm": self.cli.do_rm,
            "name": self.cli.do_name, "rmname": self.cli.do_rmname,
            "verify": self.cli.do_verify, "logout": self.cli.do_logout,
            "unprotect": self.cli.do_unprotect,
            "showconf": self.cli.do_showconf,
            "inspect": self.cli.do_inspect, "login": self.cli.do_login,
            "setup": self.cli.do_setup, "install": self.cli.do_install,
        }

        if ((len(self.argv) == 1) or self.cmdp.get("-h", "GEN_OPT") or
                self.cmdp.get("--help", "GEN_OPT")):
            exit_status = self.cli.do_help(self.cmdp)
            return exit_status

        command = self.cmdp.get("", "CMD")
        if command in cmds:
            if self.cmdp.get("--help", "CMD_OPT"):
                Msg().out(cmds[command].__doc__)
                return exit_status
            if command in ["version", "showconf"]:
                exit_status = cmds[command](self.cmdp)
                return exit_status
            if command != "install":
                self.cli.do_install(None)
            exit_status = cmds[command](self.cmdp)  # executes command
            if self.cmdp.missing_options():
                Msg().err("Error: syntax error at: %s" %
                          " ".join(self.cmdp.missing_options()))
                exit_status = 1
                return exit_status
            return exit_status
        else:
            Msg().err("Error: invalid command:", command, "\n")
            exit_status = 1

        return exit_status
