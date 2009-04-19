#! /usr/bin/env python
# -*- coding: utf-8 -*-

#   eLyXer -- convert LyX source files to HTML output.
#
#   Copyright (C) 2009 Alex Fernández
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

# --end--
# Alex 20090420
# eLyXer postprocessor for tables

from util.trace import Trace
from gen.table import *
from post.postprocess import *


class PostTable(object):
  "Postprocess a table"

  def postprocess(self, current, last):
    "Look for a table and postprocess it"
    tables = current.searchall(Table)
    if len(tables) == 0:
      return current
    for table in current.searchall(Table):
      self.posttable(table)
    return current

  def posttable(self, table):
    "Postprocess the table"
    Trace.debug('Params: ' + str(len(table.parameters)))
    for parameter, value in table.parameters.iteritems():
      Trace.debug('Table param ' + parameter + ': ' + unicode(value))

Postprocessor.unconditional.append(PostTable)
