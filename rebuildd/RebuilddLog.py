# rebuildd - Debian packages rebuild tool
#
# (c) 2007 - Julien Danjou <acid@debian.org>
#
#   This software is free software; you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation; version 2 dated June, 1991.
#
#   This software is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this software; if not, write to the Free Software
#   Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301 USA
#

import logging
import sqlobject
from RebuilddConfig import RebuilddConfig

class Log(sqlobject.SQLObject):
    """Class implementing a Log"""

    job = sqlobject.ForeignKey('Job', cascade=True)
    text = sqlobject.BLOBCol(default="No build log available")

class RebuilddLog(object):
    """Singleton used for logging"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = object.__new__(cls)
            cls._instance.init()
        return cls._instance

    def init(self):
        cfg = RebuilddConfig()
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(levelname)s %(message)s',
                            filename=cfg.get('log', 'file'),
                            datefmt=cfg.get('log', 'time_format'),
                            filemode='a')

    @classmethod
    def info(self, str):
        """Log a string with info priority"""

        logging.info(str)

    @classmethod
    def warn(self, str):
        """Log a string with warn priority"""
        
        logging.warning(str)

    @classmethod
    def error(self, str):
        """Log a string with error priority"""
        
        logging.error(str)

