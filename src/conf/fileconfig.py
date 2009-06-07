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
# Alex 20090203
# eLyXer parsers

import codecs
import datetime
from util.trace import Trace
from util.options import *
from io.fileline import *


class ConfigReader(object):
  "Read a configuration file"

  def __init__(self, reader):
    self.reader = reader
    self.objects = dict()
    self.section = None

  def parse(self):
    "Parse the whole file"
    while not self.reader.finished():
      self.parseline(self.reader.currentline())
      self.reader.nextline()

  def parseline(self, line):
    "Parse a single line"
    if line == '\n':
      return
    line = line[:-1]
    if line.startswith('#'):
      return
    if line.startswith('['):
      self.parsesection(line)
    else:
      self.parseparam(line)

  def parsesection(self, line):
    "Parse a section header"
    if not line.endswith(']'):
      Trace.error('Incorrect section header ' + line)
      return
    name = line[1:-1]
    self.section = name
    self.objects[name] = dict()

  def parseparam(self, line):
    "Parse a parameter line"
    if len(line.strip()) == 0:
      return
    if line.startswith(ConfigWriter.listmarker):
      self.parselist(line)
      return
    if not ':' in line:
      Trace.error('Invalid configuration parameter ' + line)
      return
    pieces = line.split(':')
    if len(pieces) > 2:
      Trace.error('Too many colons in ' + line)
      return
    key = self.unescape(pieces[0])
    value = self.unescape(pieces[1])
    object = self.objects[self.section]
    object[key] = value

  def parselist(self, line):
    "Parse a list"
    result = []
    contents = line[len(ConfigWriter.listmarker):].split(',')
    for piece in contents:
      result.append(self.unescape(piece))
    self.objects[self.section] = result

  def unescape(self, string):
    "Escape a string"
    for escape, value in ConfigWriter.escapes:
      string = string.replace(value, escape)
    return string

class ConfigWriter(object):
  "Write a configuration file"

  escapes = [
      ('\n', '&10;'), (':', '&58;'), ('#', '&35;'), (',', '&44;')
      ]

  listmarker = ',list:'

  def __init__(self, writer):
    self.writer = writer

  def writeall(self, types):
    "Write a list of configuration objects given their class names"
    for type in types:
      object = type.__new__(type)
      self.write(object)

  def write(self, object):
    "Write a configuration object"
    for attr in dir(object):
      self.writeattr(object, attr)

  def writeattr(self, object, attr):
    "Write an attribute"
    if attr.startswith('__'):
      return
    self.writesection(object, attr)
    value = getattr(object, attr)
    if isinstance(value, list):
      self.writelist(attr, value)
    elif isinstance(value, dict):
      self.writedict(attr, value)
    else:
      Trace.error('Unknown config type ' + value.__class__.__name__ +
          ' in ' + attr)

  def writelist(self, attr, values):
    "Write a list attribute"
    result = ''
    for value in values:
      result += self.escape(value) + ','
    if len(values) > 0:
      result = result[:-1]
    self.writer.writeline(ConfigWriter.listmarker + result)

  def writedict(self, attr, valuedict):
    "Write a dictionary attribute"
    names = valuedict.keys()
    names.sort()
    for name in names:
      value = valuedict[name]
      self.writer.writeline(self.escape(name) + ':' + self.escape(value))

  def writesection(self, object, attr):
    "Write a new section"
    self.writer.writeline('')
    header = '[' + object.__class__.__name__ + '.' + attr + ']'
    self.writer.writeline(header)

  def escape(self, string):
    "Escape a string"
    for escape, value in ConfigWriter.escapes:
      string = string.replace(escape, value)
    return string

class ConfigTranslator(object):
  "Translates a number of dictionaries from a config file to a Python class"

  escapes = [ ('\\', '\\\\'), ('\n', '\\n'), ('\'', '\\\'') ]

  def __init__(self, writer):
    self.writer = writer

  def write(self, objects):
    "Write the whole set of objects"
    self.writer.writeline('#! /usr/bin/env python')
    self.writer.writeline('# -*- coding: utf-8 -*-')
    self.writer.writeline('')
    self.writer.writeline('# eLyXer configuration')
    self.writer.writeline('# autogenerated from config file on ' +
        datetime.date.today().isoformat())
    self.writer.writeline('')
    classes = self.sort(objects)
    names = classes.keys()
    names.sort()
    for classname in names:
      self.writeclass(classname, classes[classname])

  def writeclass(self, name, current):
    "Write an object class"
    self.writer.writeline('class ' + name + '(object):')
    self.writer.writeline('  "Configuration class from config file"')
    self.writer.writeline('')
    names = current.keys()
    names.sort()
    for attrname in names:
      self.writeattr(attrname, current[attrname])

  def writeattr(self, name, contents):
    "Write an attribute"
    self.writer.writestring('  ' + name + ' = ')
    if isinstance(contents, list):
      self.writelist(contents)
    elif isinstance(contents, dict):
      self.writedict(contents)
    else:
      Trace.error('Unknown config type ' + contents.__class__.__name__)
    self.writer.writeline('')

  def writelist(self, values):
    "Write a list of values"
    self.writer.writeline('[')
    string = '      '
    for value in values:
      piece = 'u\'' + self.escape(value) + '\', '
      string = self.append(string, piece)
    self.writer.writeline(string)
    self.writer.writeline('      ]')

  def writedict(self, values):
    "Write a dictionary of values"
    self.writer.writeline('{')
    string = '      '
    names = values.keys()
    names.sort()
    for name in names:
      value = values[name]
      piece = 'u\'' + self.escape(name) + '\':u\'' + self.escape(value) + '\', '
      string = self.append(string, piece)
    self.writer.writeline(string)
    self.writer.writeline('      }')

  def append(self, string, piece):
    "Write a piece to the string or to disk"
    if len(string + piece) > 80:
      self.writer.writeline(string)
      string = '      '
    return string + piece

  def sort(self, objects):
    "Sort the objects into classes"
    classes = dict()
    for name, object in objects.iteritems():
      pieces = name.split('.')
      if len(pieces) != 2:
        Trace.error('Wrong method name ' + name)
        return
      classname = pieces[0]
      methodname = pieces[1]
      if not classname in classes:
        classes[classname] = dict()
      currentclass = classes[classname]
      currentclass[methodname] = object
    return classes

  def escape(self, string):
    "Escape a string"
    for escape, value in ConfigTranslator.escapes:
      string = string.replace(escape, value)
    return string

