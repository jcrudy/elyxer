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
# Alex 20101506
# eLyXer macro processing

from gen.inset import *
from util.trace import Trace
from conf.config import *
from parse.formulaparse import *
from parse.headerparse import *
from maths.formula import *
from maths.hybrid import *


class MathMacro(object):
  "A math macro: command, parameters, default values, definition."

  macros = dict()

  def __init__(self):
    self.newcommand = None
    self.parameternumber = 0
    self.defaults = []
    self.definition = None

  def instantiate(self):
    "Return an instance of the macro."
    return self.definition.clone()

class MacroParameter(FormulaBit):
  "A parameter from a macro."

  def detect(self, pos):
    "Find a macro parameter: #n."
    return pos.checkfor('#')

  def parsebit(self, pos):
    "Parse the parameter: #n."
    if not pos.checkskip('#'):
      Trace.error('Missing parameter start #.')
      return
    self.number = int(pos.skipcurrent())
    self.original = '#' + unicode(self.number)
    self.contents = [TaggedBit().constant('#' + unicode(self.number), 'span class="unknown"')]

class DefiningFunction(ParameterFunction):
  "Read a function that defines a new command (a macro)."

  commandmap = FormulaConfig.definingfunctions

  def parsebit(self, pos):
    "Parse a function with [] and {} parameters."
    if self.factory.detecttype(Bracket, pos):
      newcommand = self.parseliteral(pos)
    elif self.factory.detecttype(FormulaCommand, pos):
      newcommand = FormulaCommand().extractcommand(pos)
    else:
      Trace.error('Unknown formula bit in defining function at ' + pos.identifier())
      return
    Trace.debug('New command: ' + newcommand)
    template = self.translated
    self.factory.defining = True
    Trace.debug('Defining: yes')
    self.readparams(template, pos)
    self.factory.defining = False
    Trace.debug('Defining: no')
    self.contents = []
    macro = MathMacro()
    macro.newcommand = newcommand
    macro.parameternumber = self.readparameternumber()
    macro.definition = self.params['$d'].value
    self.extractdefaults(macro)
    MathMacro.macros[newcommand] = macro

  def readparameternumber(self):
    "Read the number of parameters in the macro."
    if not self.params['$n'].literalvalue:
      return 0
    return int(self.params['$n'].literalvalue)

  def extractdefaults(self, macro):
    "Extract the default values for existing parameters."
    for index in range(9):
      value = self.extractdefault(index + 1)
      if value:
        macro.defaults.append(value)
      else:
        return

  def extractdefault(self, index):
    "Extract the default value for parameter index."
    value = self.params['$' + unicode(index)].value
    if not value:
      return None
    if len(value.contents) == 0:
      return FormulaConstant('')
    return value.contents[0]

class MacroFunction(CommandBit):
  "A function that was defined using a macro."

  commandmap = MathMacro.macros

  def parsebit(self, pos):
    "Parse a number of input parameters."
    self.values = []
    macro = self.translated
    while self.factory.detecttype(Bracket, pos):
      self.values.append(self.parseparameter(pos))
    defaults = list(macro.defaults)
    remaining = macro.parameternumber - len(self.values) - len(defaults)
    if remaining > 0:
      self.parsenumbers(remaining, pos)
    while len(self.values) < macro.parameternumber and len(defaults) > 0:
      self.values.insert(0, defaults.pop())
    if len(self.values) < macro.parameternumber:
      Trace.error('Missing parameters in macro ' + unicode(self))
    self.completemacro(macro)

  def parsenumbers(self, remaining, pos):
    "Parse the remaining parameters as a running number."
    "For example, 12 would be {1}{2}."
    if pos.finished():
      return
    if not self.factory.detecttype(FormulaNumber, pos):
      return
    number = FormulaNumber().setfactory(self.factory)
    number.parsebit(pos)
    if not len(number.original) == remaining:
      self.values.append(number)
      return
    for digit in number.original:
      value = FormulaNumber().setfactory(self.factory)
      value.add(FormulaConstant(digit))
      value.type = number
      self.values.append(value)

  def completemacro(self, macro):
    "Complete the macro with the parameters read."
    self.contents = [macro.instantiate()]
    for parameter in self.searchall(MacroParameter):
      index = parameter.number - 1
      if index >= len(self.values):
        return
      parameter.contents = [self.values[index].clone()]

class FormulaMacro(Formula):
  "A math macro defined in an inset."

  def __init__(self):
    self.parser = MacroParser()
    self.output = EmptyOutput()

  def __unicode__(self):
    "Return a printable representation."
    return 'Math macro'

FormulaCommand.commandbits += [
    DefiningFunction(), MacroFunction(),
    ]

FormulaFactory.types += [ MacroParameter ]

