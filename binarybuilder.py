#// +--------------------------------------------------------------------------
#// |
#// |   Mermaid GPL Source Code
#// |   Copyright (c) 2013-2016 XNerv Ltda (http://xnerv.com). All rights reserved.
#// |
#// |   This file is part of the Mermaid GPL Source Code.
#// |
#// |   Mermaid Source Code is free software: you can redistribute it and/or
#// |   modify it under the terms of the GNU General Public License
#// |   as published by the Free Software Foundation, either version 3
#// |   of the License, or (at your option) any later version.
#// |
#// |   Mermaid Source Code is distributed in the hope that it will be useful,
#// |   but WITHOUT ANY WARRANTY; without even the implied warranty of
#// |   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#// |   GNU General Public License for more details.
#// |
#// |   You should have received a copy of the GNU General Public License
#// |   along with Mermaid Source Code. If not, see <http://www.gnu.org/licenses/>.
#// |
#// +--------------------------------------------------------------------------

import os
import sys
import string
import datetime

VERSION='1.0.0'

class Utils:
  @staticmethod
  def filter_text(text, valid_chars, replacements):
    text = "".join(c for c in text if c in valid_chars)
    text = "".join([replacements.get(c, c) for c in text])
    return text

  @staticmethod
  def normalise_filename(filename):
    filename = Utils.filter_text(text = filename, valid_chars = "-_. %s%s" % (string.ascii_letters, string.digits), replacements = {' ':'_', '.':'_', '-':'_'})
    return filename.lower()

class EntityType:
  UNKNOWN   = 'unknown'
  DIRECTORY = 'directory'
  FILE      = 'file'

class Entity:
  def __init__(self, entity_type=EntityType.UNKNOWN, entity_name='', entity_path=''):
    self.EntityType = entity_type
    self.EntityName = entity_name
    self.EntityPath = entity_path
    self.Entities   = []      

class EntityTree:
  def __init__(self, root_path=""):
    if root_path.strip() != "":
      self.Root  = self.__build_the_tree(root_path)
    else:
      print "root path must be provided."
      sys.exit(1)

  def __build_the_tree(self, path):
      entity = Entity(entity_type=EntityType.UNKNOWN, entity_name=os.path.basename(path), entity_path=path)
      if self.__is_hidden_file(entity):
        return entity

      if os.path.isdir(path):
          entity.EntityType = EntityType.DIRECTORY
          for item_path in sorted(os.listdir(path)):
              entity.Entities.append(self.__build_the_tree(os.path.join(path, item_path)))
          return entity
      elif os.path.isfile(path):
          entity.EntityType = EntityType.FILE
          return entity
      else:
          entity.EntityType = EntityType.UNDEFINED
          return entity

  def __is_hidden_file (self, entity):
    return (entity.EntityName == ".git" or 
            entity.EntityName == ".svn" or 
            entity.EntityName.endswith(".scc") or 
            entity.EntityName.startswith("."))

class ResourceGenerator:
  def __init__(self, root_namespace, entity_tree, source_directory, output_directory):
    self.root_namespace   = root_namespace
    self.entity_tree      = entity_tree
    self.source_directory = source_directory
    self.output_directory = output_directory
    self.generation_date  = datetime.datetime.now()
    
  def generate_resource(self, entity, namespace):
    base_path = os.path.abspath(os.path.join(self.output_directory, "source", os.path.relpath(os.path.dirname(entity.EntityPath), self.source_directory))) 

    if not os.path.exists(base_path):
      os.makedirs(base_path)

    header_file = os.path.join(base_path, Utils.normalise_filename(entity.EntityName) + ".h")
    cpp_file    = os.path.join(base_path, Utils.normalise_filename(entity.EntityName) + ".cpp")
    
    try:
      header = open(header_file, 'wb')
    except IOError:     
      print "Failed to open the header file " + header_file
      sys.exit(1)     
  
    try:
      cpp = open(cpp_file, 'wb')
    except IOError:     
      print "Failed to open the cpp file " + cpp_file
      sys.exit(1)

    try:
      resource           = open(entity.EntityPath, 'rb')
      resource_data_size = os.path.getsize(entity.EntityPath)
      print "Size: " + str(resource_data_size)
    except IOError:     
      print "Failed to open the resource file " + entity.EntityPath
      sys.exit(1)

    header.write ("/****************************************************    \n")
    header.write (" * (Auto-generated file; DO NOT EDIT MANUALLY!)          \n")
    header.write (" * Generation date: " + str(self.generation_date) +     "\n")
    header.write (" ****************************************************/ \n\n")

    header.write ("#pragma once\n\n")

    header.write ("namespace " + namespace + "\n")
    header.write ("{\n")
    header.write ("  extern const char* " + Utils.normalise_filename(entity.EntityName) + ";                                       \n")
    header.write ("  const int          " + Utils.normalise_filename(entity.EntityName) + "__SIZE = " + str(resource_data_size) + ";\n")
    header.write ("};\n")

    cpp.write ("/****************************************************    \n")
    cpp.write (" * (Auto-generated file; DO NOT EDIT MANUALLY!)          \n")
    cpp.write (" * Generation date: " + str(self.generation_date) + "    \n")
    cpp.write (" ****************************************************/ \n\n")

    cpp.write ("#include \"" + os.path.basename(header_file) + "\"\n\n")
    cpp.write ("static const unsigned char data[] = {") 
    for line in resource:
      for rd in line:
        byte_str = str(ord(rd))
        cpp.write (byte_str + ',') 
    cpp.write ("0,0};\n\n")
    
    cpp.write ("const char* " + namespace + "::" + Utils.normalise_filename(entity.EntityName) + " = (const char*) data;\n")

    self.main_header.write ("#include \"" + os.path.relpath(header_file, start=self.output_directory) + "\"\n")

    header.close()
    cpp.close()

  def generate(self):
    base_path = os.path.abspath(self.output_directory) 

    if not os.path.exists(base_path):
      os.makedirs(base_path)

    main_header_file = os.path.join(base_path, "resources.h")
    
    try:
      self.main_header = open(main_header_file, 'wb')
    except IOError:     
      print "Failed to open the main header file " + main_header_file
      sys.exit(1)  

    self.main_header.write ("/****************************************************    \n")
    self.main_header.write (" * (Auto-generated file; DO NOT EDIT MANUALLY!).         \n")
    self.main_header.write (" * Generation date: " + str(datetime.datetime.now()) +  "\n")
    self.main_header.write (" ****************************************************/ \n\n")

    self.__generate(self.entity_tree.Root.Entities, self.root_namespace)

    self.main_header.close()

  def __generate(self, entities, namespace):
    for entity in sorted(entities, key=lambda i: i.EntityType, reverse=True):
      if entity.EntityType == EntityType.DIRECTORY:
        inner_namespace = namespace + '::' + Utils.normalise_filename(entity.EntityName)
        self.__generate(entity.Entities, inner_namespace)
      elif entity.EntityType == EntityType.FILE:
        self.generate_resource(entity, namespace)
      else:
        print "Unknown file " + entity.EntityPath

global ScriptOptions
if __name__ == "__main__":
  from optparse import OptionParser
  optparse = OptionParser(version="%prog v" + VERSION)
  optparse.add_option("-s", "--source", action="store", dest="sourcedir", help="source directory")
  optparse.add_option("-o", "--output", action="store", dest="outputdir", help="output directory")

  (options, arguments) = optparse.parse_args()
  ScriptOptions=options
  
  if ScriptOptions.sourcedir is None or ScriptOptions.outputdir is None:
    optparse.print_help()
    sys.exit(1)

  if (os.path.isdir(ScriptOptions.sourcedir) == False):
    print "Source directory doesn't exist!"
    sys.exit(1)

  entity_tree       = EntityTree(root_path=ScriptOptions.sourcedir)
  resourceGenerator = ResourceGenerator("Resources", entity_tree=entity_tree, source_directory=ScriptOptions.sourcedir, output_directory=ScriptOptions.outputdir)
  resourceGenerator.generate()