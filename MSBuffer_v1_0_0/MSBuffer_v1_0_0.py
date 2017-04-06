#---------------------------------------------------------------------------------------
"""
 MSbuffer - MultiScale Buffer Analysis v. 1.0.0

 Bruno P. Leles - brunopleles@gmail.com
 Bernardo B. S. Niebuhr - bernardo_brandaum@yahoo.com.br
 John W. Ribeiro - jw.ribeiro.rc@gmail.com
 Milton C. Ribeiro - mcr@rc.unesp.br

 Universidade Estadual Paulista - UNESP
 Rio Claro - SP - Brasil

 This script runs inside ArcMap v. 10.2.1 using Python 2.7.
.
 The Multi-Scale Buffer (MSBuffer) is a free and open source package developed in the Python 2.7 
 as an ArcGIS geoprocessing tool. It that performs area/length calculation and feature counting in buffers 
 of multiple sizes around of an area of interest.
 
 Usage: Take a look at the online tutorial at https://github.com/LEEClab/MSBuffer.

 Copyright (C) 2017 by Bruno P. Leles, Bernardo B. S. Niebuhr, John W. Ribeiro, and Milton C. Ribeiro.

 This program is free software: you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation, either version 2 of the license, 
 or (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
#---------------------------------------------------------------------------------------

#------------------------------
# Import modules 
import arcpy
from arcpy import env
import os, sys
import arcpy.mapping

#------------------------------
# Name of the geo database where output buffer maps will be saved
geoDB_name = "output_buffer_maps.gdb"
# Do we want to overwrite output buffer maps in case the analysis is re-run?
overwrite_maps = True

#------------------------------
# Reading parameters from the GUI

# Input map
inputmap = arcpy.GetParameterAsText(0) # input map
inputCol = arcpy.GetParameterAsText(1) # column of the input map, correspondent to the variable of interest
inputmap_name = inputmap.split("\\") # extracting the name of the input map
inputmap_name = inputmap_name[-1].replace(".shp", '') # name of the input map (without the path)

# Input variable of interest
variable_interest = arcpy.GetParameterAsText(2) # map of the variable of interest
variable_interest_name = variable_interest.split('\\') # extracting the name of the variable of interest map
variable_interest_name = variable_interest_name[-1].replace('.shp', '') # name of the variable of interest map (without the path)

# Scale (buffer size in meters)
scale = arcpy.GetParameterAsText(3)
scale = int(scale)

# Number of buffers
nbuffers = arcpy.GetParameterAsText(4)
nbuffers = int(nbuffers)

# Should we count the number of features?
count_on_off = arcpy.GetParameterAsText(5) # boolean to count features
#feature_to_count = variable_interest

# Should we calculate the area or length inside the buffer?
area_length_on_off = arcpy.GetParameterAsText(6) # boolean to calculate area or length inside the donut buffer

# Should we calculate Functional Area (in case of a polygon variable of interest)?
func_area_length_on_off = arcpy.GetParameterAsText(7) # boolean to calculate functional area or length

# Save output maps?
save_maps = arcpy.GetParameterAsText(8) # boolean to save buffer maps in the geodatabase

# Prefix for output files 
OutPutTxt = arcpy.GetParameterAsText(9)

# Folder for output files
OutPutFolder = arcpy.GetParameterAsText(10)


#----------------------------------------------------------------------------------
# MSBuffer is the main class, in which the toolbox is initialized and runs

class MSBuffer(object):
    
    # Initializing parameters
    def __init__(self, inputmap, inputmap_name, inputCol, variable_interest, variable_interest_name, OutPutTxt, OutPutFolder, save_maps,
                 scale, nbuffers, count_on_off, area_length_on_off, func_area_length_on_off):	
	
	# Input maps and outputs
	self.inputmap = inputmap # Input map
	self.inputmap_name = inputmap_name # Name of the input map
	self.inputCol = inputCol # column of the input map that identifies the ID of the polygons around which the buffers will be drawn	
	self.variable_interest = variable_interest # Map correspondent to the variable of interest
	self.variable_interest_name = variable_interest_name # Name of the variable of interest map
	self.OutPutTxt = OutPutTxt # Prefix of the output file names
	self.OutPutFolder = OutPutFolder # Folder where text files will be saved
	self.save_maps = save_maps # Will buffer maps be saved in the ArcGIS geodatabase?
	
	# Parameters
	self.scale = scale # Scale parameter (minimum buffer size)
	self.nbuffers = nbuffers # Number of buffers - parameter
	self.count_on_off = count_on_off # Option: count or not the number of features
	self.area_length_on_off = area_length_on_off # Option: calculate or not the area/length inside the buffer, in case the variable of interest is of the type "polygon"/"polyline"
	self.func_area_length_on_off = func_area_length_on_off # Option: calculate or not the functional area/length, in case the variable of interest is of the type "polygon"/"polyline"
	
	# Auxiliary variables
	self.isArea = False # True if the geometry of the variable of interest is Polygon
	self.isLine = False # True if the geometry of the variable of interest is Polyline
	self.isPoint = False # True if the geometry of the variable of interest is Point
        
        self.listbuffers = '' # List of buffer map names (with input map) generated by createBuffer function
	self.Listerased = '' # List of donut buffer map names (buffer without input mao) generated by erase function
	self.listclip = '' # List of maps with the variable of interest clipped by donut buffer maps, generated by clip_variable_interest_by_donut_buffer function
	
	self.list_buffer_scales = [] # List of buffer sizes (e.g., 500, 1000, 1500, 2000)
	self.ListIDcod = [] # List of ID codes - features of the input map, around which buffers will be drawn
	self.FieldList = [] # List of column names in a shapefile, used for checking if a given column exists
	self.referenceListquery = [] # List of queries: SQL expressions used to select each feature of the input map
	self.listDonutMapAreas = [] # List of total areas of Donut maps (buffer without the input map feature)
	self.countList = [] # List of number of features inside the donut buffer maps, for each buffer size
	self.listAreaInsideBuffer = []	# List of area of polygons of the variable of interest that overlap the donut buffer maps, for each buffer size
	self.listFunctionalArea = [] # List of functional area of polygons that overlap the donut buffer maps, for each buffer size
	self.listLengthInsideBuffer = [] # List of length of polylines of the variable of interest that overlap the donut buffer maps, for each buffer size
	self.listFunctionalLength = [] # List of functional length of lines that overlap the donut buffer maps, for each buffer size
	
	self.counter = 0 # Counter to identify the elements of the polygon ID list
	self.onelist = '' # Global Class List to be used by the function selectINlist 
	self.pattern = '' # Global Class pattern string to be used by the function selectINlist
	
	#self.feature=feature_to_count # = variable of interest, i.e, the shapefile whose features should be counted

	# Output files and names
	self.txtArea = '' # Output file where area analysis will be saved
	self.txtFuncArea = '' # Output file where functional area analysis will be saved
	self.txtLength = '' # Output file where length analysis will be saved
	self.txtFuncLength = '' # Output file where functional length analysis will be saved
	self.txtCountFeat = '' # Output file where cont feature analysis will be saved
	self.txtBufferArea = '' # Output file where donut buffer areas will be saved
	
	# Names of the output files
	# Area
	self.txtArea_name = self.OutPutTxt+"_"+self.variable_interest_name+"_Area.txt"
	# Functional area
	self.txtFuncArea_name = self.OutPutTxt+"_"+self.variable_interest_name+"_FunctionalArea.txt"
	# Length
	self.txtLength_name = self.OutPutTxt+"_"+self.variable_interest_name+"_Length.txt"
	# Functional length
	self.txtFuncLength_name = self.OutPutTxt+"_"+self.variable_interest_name+"_FunctionalLength.txt"	
	# Count feaures
	self.txtCountFeat_name = self.OutPutTxt+"_"+self.variable_interest_name+"_Count.txt"
	# Donut buffer area
	self.txtBufferArea_name = self.OutPutTxt+"_"+self.variable_interest_name+'_BufferArea.txt'
	
	# Defining the workspace for ArcGIS as the output folder
	arcpy.env.workspace=self.OutPutFolder
	
    #------------------------
    def defineScale(self):
	'''
	Function defineScale
	
	This function reads the parameters scale (buffer size) and number of buffers
	and defines a list of buffer sizes.
	'''
	
	# Assess the minimum buffer size
	con_esc=self.scale
	
	# For each element up to the number of buffers
	for i in range(self.nbuffers):	
	    self.list_buffer_scales.append(con_esc) # Appending a buffer value to the buffer scale list
	    con_esc=con_esc+self.scale # Defining the next buffer value
		
		
    def createInputMapIDList(self):
	'''
	Function createInputMapIDList
	
	This function creates a list of features (ID, names, ...) given the input map 
	and the identificator column.
	Each component of this list corresponds to a feature of the input map.
	'''
	
	# Looking at the elements of the inputCol, within the inputmap
	with arcpy.da.SearchCursor(self.inputmap, self.inputCol) as cursor:
	    for row in cursor:
		# Tries to transform the elements in interger numbers, in case numerical IDs are used
		try: 
		    temp=int(row[0])
		    self.ListIDcod.append(temp) # Appends the value to the list of ID codes
		    query="\""+self.inputCol+"\"="+`temp` # Creating SQL expression for retrieving this feature later on
		# If it is not possible, it considers the elements of the column as strings
		except:
		    self.ListIDcod.append(row[0]) # Appends the value to the list of ID codes
		    query =  self.inputCol+"='%s'" % row[0] # Creating SQL expression for retrieving this feature later on
		    
		self.referenceListquery.append(query) # Appending expression to query list
		    
		    	    
    # This function deletes pre-existing shape files in the output geodatabase
    def deleteFiles(self):
	'''
	Function deleteFiles
	
	This function deletes pre-existing shape files in the output geodatabase.
	'''
	
	# If the geodatabase exists in the output folder
	if os.path.exists(self.OutPutFolder+'/'+geoDB_name):
	    # Sets the ArcGIS workspace as the geodatabase
	    arcpy.env.workspace=self.OutPutFolder+'/'+geoDB_name
	    # Raises a list of shape features in the geodatabase
	    onelist=arcpy.ListFeatureClasses()
	    # For each element in the list, deletes the feature and the shapefile
	    for i in onelist:
		inp = i.replace(".shp", '')
		arcpy.Delete_management(i)
		arcpy.Delete_management(inp)
    

    def selectInList(self):
	'''
	Function selectInList
	
	This function looks into a list (self.onelist), search for elements that match the 
	string self.pattern, and returns the list of matched elements.
	'''
	
	# Initializing list
        onelist=[]
	# For each element in a list of shapefile names
        for i in self.onelist:
	    # If the string pattern is found inside the name
            if self.pattern in i:
                onelist.append(i) # Appends that to the list
        
        return onelist # Returns the list of matched elements
        
    
    def createDb(self):
	'''
	Function createDb
	
	In case the geodatabase for saving the maps does not exist, this function creates it.
	'''
	
	# If the geodatabase does not exist
        if not os.path.exists(self.OutPutFolder+'/'+geoDB_name):
            arcpy.CreateFileGDB_management(self.OutPutFolder, geoDB_name) # Create it
        
    
    def createBuffer(self):
	'''
	Function createBuffer
	
	This function generates buffer maps (which overlap the input map).
	It also defines a list of buffer map names called self.listbuffers.
	'''
	
	# Defining the geodatabase, inside the output folder, as the ArcGIS workspace
        arcpy.env.workspace=self.OutPutFolder+'/'+geoDB_name
	
	# Polygon ID info, for saving it in the buffer map name
	idcod = str(self.ListIDcod[self.counter])
	
	# For each buffer size in the list of buffer scales:
        for i in self.list_buffer_scales:
            # Format buffer size in the map name
            formatName="00000"+`i` 
            formatName=formatName[-5:] # MAXIMUM BUFFER SIZE = 99999
	    # Define the output buffer map name
            OutPutName=self.inputmap_name+"_ID_"+idcod+"_buffer_with_inputmap_"+formatName
	    # Create buffer shapefile, with the original polygon together
            arcpy.Buffer_analysis(self.inputmap, OutPutName, i, "FULL", "FLAT", "ALL")
	    
	# List features in the geodatabase, searches for the buffer ones just created, 
	# and saves these names in a list called self.listbuffers
	listbuffers = arcpy.ListFeatureClasses()
	self.onelist = listbuffers
	self.pattern = idcod+"_buffer_with_inputmap_" # Pattern to be found in the map names
	self.listbuffers=MSBuffer.selectInList(self) # Searching for the pattern in map names and defining the list of buffer map names
    
    
    def erase(self):
	'''
	Function erase
	
	This function erases the original input feature from the buffer map, 
	resulting in a donut-like buffer. 
	It also defines a list of donut buffer map names called self.Listerased, 
	and a list of donut buffer map areas called self.listDonutMapAreas.
	'''
	
	# Polygon ID info, for saving it in the buffer map name
	idcod = str(self.ListIDcod[self.counter])	
	
	# For each map in the list of buffer map names
	for i in self.listbuffers:
	    # Define the name of the donut map, replacing "buffer" by "donut"
	    out_name=i.replace("buffer_with_inputmap", "donut_buffer")
	    # Erases the input map from the buffer map and produces a donut map
	    arcpy.Erase_analysis(i, self.inputmap, out_name, '')
	    
	    # Add a field to the donut map attribute table, called "area_ha"
	    arcpy.AddField_management(out_name, "area_ha", "DOUBLE", 10, 10)
	    # Calculate the area of the donut, in hectares
	    arcpy.CalculateField_management(out_name, "area_ha", "!shape.area@hectares!","PYTHON_9.3","#")
	    
	    # Assess the donut buffer map areas and append it to the list self.listDonutMapAreas
	    rows = arcpy.da.SearchCursor(out_name, "area_ha")
	    for row in rows:
		self.listDonutMapAreas.append(row[0])
	    #self.lista_erases.append(out_name)
	    
	# List features in the geodatabase, searches for the donut buffer ones just created, 
	# and saves these names in a list called self.Listerased
	Listerased = arcpy.ListFeatureClasses()
	self.onelist = Listerased
	self.pattern = idcod+"_donut_buffer_" # Pattern to be found in the map names
	self.Listerased = MSBuffer.selectInList(self) # Searching for the pattern in map names and defining the list of donut buffer map names
	
    
    def typeFeature(self):
	'''
	Function typeFeature
	
	This function checks the geometry type of the variable of interest (Polygon, Point) (pode Polyline ou outros????).
	This is written in a global variable (self.isArea or self.isPoint).
	PORQUE ELE CALCULA A AREA EM HA DE CADA POLIGONO DO MAPA DA VARIAVEL DE INTERESSE TODO?
	EH para definir a area funcional depois?
	'''
	
	# Get description of the variable of interest map
	desc = arcpy.Describe(self.variable_interest)
	# Look at the geometry type of the map (polygons, lines, points)
	geometryType = desc.shapeType
	
	# If the geometryType is Polygon:
	if geometryType == 'Polygon':
	    self.isPoint = False # Variable type is not Point
	    self.isLine = False # Variable type is not Line
	    self.isArea = True # Defines the variable type as Area
	    
	    # If the Functional Area is to be calculated, calculate the area of the polygons of the variable of interest map
	    if self.func_area_length_on_off:
		try:
		    # Add field "area_ha" to the variable of interest map
		    arcpy.AddField_management(self.variable_interest, "area_ha", "DOUBLE", 10, 10)
		    # Calculate the area of the features within the map variable of interest, in hectares
		    arcpy.CalculateField_management(self.variable_interest, "area_ha", "!shape.area@hectares!","PYTHON_9.3","#")
		    
		    #arcpy.CalculateField_management(self.variable_interest, "area_ha", "!shape.area@squaremeters!","PYTHON_9.3","#")
		    #expression="!Area_ha!/10000" # Area_ha ou area_ha? 
		    #arcpy.CalculateField_management(self.variable_interest,"area_ha",expression,"PYTHON_9.3","#")		
		except Exception as e:
		    pass
	
	# If the geometryType is Polygon:
	elif geometryType == 'Point' or geometryType == 'Multipoint':
	    self.isArea = False # Variable type is not Area
	    self.isLine = False # Variable type is not Line
	    self.isPoint = True # Defines the variable as Point
	elif geometryType == 'Polyline':
	    self.isArea = False # Variable type is not Area
	    self.isPoint = False # Variable type is not Point 
	    self.isLine = True # Defines the variable as Line
	    
	    # If the Functional Lenth is to be calculated, calculate the length of the lines of the variable of interest map
	    if self.func_area_length_on_off:
		try:
		    # Add field "length_m" to the variable of interest map
		    arcpy.AddField_management(self.variable_interest, "length_m", "DOUBLE", 10, 10)
		    # Calculate the length of the features within the map variable of interest, in meters
		    arcpy.CalculateField_management(self.variable_interest, "length_m", "!shape.length@meters!","PYTHON_9.3","#")
		except Exception as e: 
		    pass
	
	
    def countFeatures(self):
	'''
	Function countFeatures
	
	This function counts the number of features that intersect with the donut buffer map, for each
	buffer size. It stores the value of the number of features in the list self.countList, a list of
	number of features for each buffer size.
	'''
	
	# For each map in the list of donut buffer maps:
	for donut in self.Listerased:
	    # Select the features in the variable of interest map that intersects with the donut buffer
	    arcpy.SelectLayerByLocation_management(self.variable_interest, "INTERSECT", donut)
	    # Looks at each feature selected
	    cursor = arcpy.da.SearchCursor(self.variable_interest, ['FID'])
	    
	    # Counts the number of features in the variable "count"
	    #count = 0
	    #for i in cursor:
		#count = count+1
	    list_cursor = list(cursor)
	    count = len(list_cursor)
	    
	    # Appends the number of features to the list self.countList
	    self.countList.append(count)	  	    
	    
	     
    def calcFunctionalArea_Length(self):
	'''
	Function calcFunctionalArea_Length
	
	This function calculates the functional area (for polygons) or length (for lines) of the variable of interest,
	for all buffer sizes. The values for each buffer size is saved in the list self.listFunctionalArea (for polygons)
	or self.listFunctionalLength (for lines).
	
	Details: the function checks the features of the variable of interest that overlaps the donut buffer map,
	and sum the complete area/length of these features (not only the area/length iside the buffer). 
	This summed area/length is here called functional area/length.
	'''
	
	# For each map in the donut buffer list:
	for donut in self.Listerased:
	    # Select the features in the variable of interest map that intersects with the donut buffer
	    arcpy.SelectLayerByLocation_management(self.variable_interest, "INTERSECT", donut) # para calcular functional area??????????????
	    
	    # If the map is an Area map, calculate functional area
	    if self.isArea == True:
		# Retrieving the area (in hectares) of each selected feature
		with arcpy.da.SearchCursor(self.variable_interest, "area_ha") as cursor:
		    # Initializing the total area
		    summed_total=0
		    # For each polygon area
		    for row in cursor:
			summed_total = summed_total + row[0] # Sum the polygon area to the total area
		    summed_total = round(summed_total, ndigits=2) # Round the total area to 2 digits
		    self.listFunctionalArea.append(summed_total) # Appends the total functional area to the list of functional areas for each buffer size
		    
	    # If the map is a Line map, calculate functional length
	    elif self.isLine == True:
		# Retrieving the length (in meters) of each selected feature
		with arcpy.da.SearchCursor(self.variable_interest, "length_m") as cursor:
		    # Initializing the total length
		    summed_total=0
		    # For each line length
		    for row in cursor:
			summed_total = summed_total + row[0] # Sum the line length to the total length
		    summed_total = round(summed_total, ndigits=2) # Round the total area to 2 digits
		    self.listFunctionalLength.append(summed_total) # Appends the total functional length to the list of functional lengths for each buffer size		
   
	
    def clip_variable_interest_by_donut_buffer(self):
	'''
	Function clip_variable_interest_by_donut_buffer
	
	This function clips the map of the variable of interest inside the donut buffer area.
	It also defines a list of names of variable of interest map inside the donut buffers, called self.listclip
	'''
	
	# Polygon ID info, for saving it in the buffer map name
	idcod = str(self.ListIDcod[self.counter])	
	
	# For each donut buffer map:
	for i in self.Listerased:
	    # Define the name of the clip map
	    out_name = i.replace("donut_buffer", self.variable_interest_name+"_inside_donut_buffer")
	    # Clips the variable of interest map features inside the donut buffer map
	    arcpy.Clip_analysis(self.variable_interest, i, out_name, "")
	
	# List features in the geodatabase, searches for the CLIP ones just created, 
	# and saves these names in a list called self.listclip	
	Listclip = arcpy.ListFeatureClasses()
	self.onelist = Listclip
	self.pattern = idcod+"_"+self.variable_interest_name+"_inside_donut_buffer_" # Pattern to be found in the map names
	self.listclip = MSBuffer.selectInList(self) # Searching for the pattern in map names and defining the list of CLIP map names
		    
    
    def checkField(self, shape_map):
	'''
	Function checkField
	
	This function returns a list of fields (columns) of an attribute table of a shapefile map.
	The list is also recorded as a class global variable, named self.FieldList.
	'''
	
	# List the fields in the shapefile map
	fields = arcpy.ListFields(shape_map)
	
	# For each field, append it to a list of map columns called self.FieldList
	for field in fields:
	    self.FieldList.append(field.name)
	# Returns the list
	return self.FieldList
    
    
    def deleteField(self):
	'''
	Function deleteField
	
	This function deletes the field "Area_ha" from the clip map (the areas of features inside the donut buffer)
	'''
	
	# For each CLIP map:
	for i in self.listclip:
	    # Lists the fields/columns in the attribute table of the map
	    fields = MSBuffer.checkField(self, i)
	    # If there is a column called "Area_ha":
	    if "Area_clip_ha" in fields:
		arcpy.DeleteField_management(i, ["Area_clip_ha"]) # Delete this column
    
    
    def addField(self):
	'''
	Function addField
	
	This function calculates the area (in hectares) of each feature of the clip map (i.e. the features 
	of the variable of interest inside the donut buffer map) and adds this value to 
	the attribute table field "Area_ha" inside the clip map
	
	# change to implement length calculation
	'''
	
	# For each CLIP map
	for i in self.listclip:
	    try:
		# Add a field to the attribute table, called "Area_ha"
		arcpy.AddField_management(i, "Area_clip_ha", "DOUBLE", 10, 10)
		# Calculates the area of each feature, in hectares
		arcpy.CalculateField_management(i,"Area_clip_ha","!shape.area@hectares!","PYTHON_9.3","#")
		
		#arcpy.CalculateField_management(i,"Area_ha","!shape.area@squaremeters!","PYTHON_9.3","#")
		#expression="!Area_ha!/10000"
		#arcpy.CalculateField_management(i,"Area_ha",expression,"PYTHON_9.3","#")
	    except:
		print "pass"
    
    
    def calculateArea_LengthInsideBuffer(self):
	'''
	Function calculateArea_LengthInsideBuffer
	
	This function retrieves the values of the feature areas (in case of polygons) or 
	lengths (in case of polylines) of the variable of interest inside the donut buffer, 
	sums it and writes it into the list self.listAreaInsideBuffer (polygons) or self.listLengthInsideBuffer (Lines).
	It works only for Polygon and Polyline shapefiles.
	'''
	
	# For each CLIP map:
	for i in self.listclip:
	    # Initializes the total area of the variable of interest inside the donut buffer
	    summed_total = 0 
	    
	    # If the map geometry is polygon:
	    if self.isArea:
		# For each polygon in the CLIP map:
		with arcpy.da.SearchCursor(i, "Shape_Area") as cursor: # Uses the "Shape_Area" column, created when the clip map is created
		#with arcpy.da.SearchCursor(i, "Area_clip_ha") as cursor: # This is in the case of calculating the area of each polygon
		    # Sum the polygon area of the variable of interest to the total area
		    for row in cursor:
			summed_total = summed_total + row[0]
		    summed_total = summed_total/10000 # This calculation is based on the "Shape_Area" column; if "Area_clip_ha" is used, this must be removed.
		    summed_total = round(summed_total, ndigits = 2) # Rounds the value to two digits
		    self.listAreaInsideBuffer.append(summed_total) # Appends it to the list of areas inside the donut buffer
		    
	    # If the map geometry is polyline:
	    elif self.isLine:
		# For each line in the CLIP map:
		with arcpy.da.SearchCursor(i, "Shape_Length") as cursor: # Uses the "Shape_Length" column, created when the clip map is created
		    # Sum the line length of the variable of interest to the total length
		    for row in cursor:
			summed_total = summed_total + row[0]
		    #summed_total = summed_total/1000 # For kilometers, not used
		    summed_total = round(summed_total, ndigits = 2) # Rounds the value to two digits
		    self.listLengthInsideBuffer.append(summed_total) # Appends it to the list of lengths inside the donut buffer	    
		
    
    def removeDuplicateList(self, onelist):
	'''
	Function removeDuplicateList
	
	Remove duplicated items inside a list, and returns a list without duplications.
	'''
	
	# Creating list without duplications
	onelistapoio=[]
	
	# For each element in the input list
	for i in onelist:
	    # If this element is not already in the list without duplication
	    if not i in onelistapoio:
		onelistapoio.append(i) # Append that to the list without duplication
	
	return onelistapoio # Returns list without duplication
	    
    
    def initializeOutputTxt(self):
	'''
	Function initializeOutputTxt
	
	This function initializes (creates) the text outputs and write the header on them.
	'''
	
	# Area
	if self.isArea and self.area_length_on_off:
	    self.txtArea = open(self.txtArea_name, 'w')
	    self.txtArea.write(self.inputCol+','+','.join(str(x) for x in self.list_buffer_scales)) # File header
	    self.txtArea.write('\n')
	    self.txtArea.close()
	
	# Functional area
	if self.isArea and self.func_area_length_on_off:
	    self.txtFuncArea = open(self.txtFuncArea_name, 'w')
	    self.txtFuncArea.write(self.inputCol+','+','.join(str(x) for x in self.list_buffer_scales)) # File header
	    self.txtFuncArea.write('\n')
	    self.txtFuncArea.close()
	    
	# Length
	if self.isLine and self.area_length_on_off:
	    self.txtLength = open(self.txtLength_name, 'w')
	    self.txtLength.write(self.inputCol+','+','.join(str(x) for x in self.list_buffer_scales)) # File header
	    self.txtLength.write('\n')
	    self.txtLength.close()
    
	# Functional area
	if self.isLine and self.func_area_length_on_off:
	    self.txtFuncLength = open(self.txtFuncLength_name, 'w')
	    self.txtFuncLength.write(self.inputCol+','+','.join(str(x) for x in self.list_buffer_scales)) # File header
	    self.txtFuncLength.write('\n')
	    self.txtFuncLength.close()	
    
	# Count feaures
	if self.count_on_off:
	    self.txtCountFeat = open(self.txtCountFeat_name, 'w')
	    self.txtCountFeat.write(self.inputCol+','+','.join(str(x) for x in self.list_buffer_scales)) # File header
	    self.txtCountFeat.write('\n')
	    self.txtCountFeat.close()
	    
	# Buffer area
	self.txtBufferArea = open(self.txtBufferArea_name, 'w')
	self.txtBufferArea.write(self.inputCol+','+','.join(str(x) for x in self.list_buffer_scales)) # File header
	self.txtBufferArea.write('\n')
	self.txtBufferArea.close()	
    
    
    def createOutputTxt(self):
	'''
	function createOutputTxt
	
	This function writes output information in the output text files. 
	The number and type of outputs depend on the users choice parameters.
	'''
	
	# Polygon ID info
	idcod = str(self.ListIDcod[self.counter])
    
	# AREA INSIDE BUFFER
	# Appends one line (one feature of the input map) with the Area inside the Buffer to the output text file
	#self.listAreaInsideBuffer=MSBuffer.removeDuplicateList(self, self.listAreaInsideBuffer)
	if self.isArea and self.area_length_on_off:
	    self.txtArea = open(self.txtArea_name, 'a')
	    self.txtArea.write(idcod+','+','.join(str(x) for x in self.listAreaInsideBuffer))
	    self.txtArea.write('\n')
	    self.txtArea.close()	
	    self.listAreaInsideBuffer = []
	
	# FUNCTIONAL AREA
	# Appends one line (one feature of the input map) with the Functional Area to the output text file
	if self.isArea and self.func_area_length_on_off:
	    self.listFunctionalArea = MSBuffer.removeDuplicateList(self, self.listFunctionalArea)
	    self.txtFuncArea = open(self.txtFuncArea_name, 'a')    
	    self.txtFuncArea.write(idcod+','+','.join(str(x) for x in self.listFunctionalArea))
	    self.txtFuncArea.write('\n')
	    self.txtFuncArea.close()	    
	    self.listFunctionalArea = []
	    
	# LENGTH INSIDE BUFFER
	# Appends one line (one feature of the input map) with the Length inside the Buffer to the output text file
	#self.listAreaInsideBuffer=MSBuffer.removeDuplicateList(self, self.listAreaInsideBuffer)
	if self.isLine and self.area_length_on_off:
	    self.txtLength = open(self.txtLength_name, 'a')
	    self.txtLength.write(idcod+','+','.join(str(x) for x in self.listLengthInsideBuffer))
	    self.txtLength.write('\n')
	    self.txtLength.close()	
	    self.listLengthInsideBuffer = []
	
	# FUNCTIONAL AREA
	# Appends one line (one feature of the input map) with the Functional Area to the output text file
	if self.isLine and self.func_area_length_on_off:
	    self.listFunctionalLength = MSBuffer.removeDuplicateList(self, self.listFunctionalLength)
	    self.txtFuncLength = open(self.txtFuncLength_name, 'a')    
	    self.txtFuncLength.write(idcod+','+','.join(str(x) for x in self.listFunctionalLength))
	    self.txtFuncLength.write('\n')
	    self.txtFuncLength.close()	    
	    self.listFunctionalLength = []	
		
	# COUNT FEATURES
	# Appends one line (one feature of the input map) with the count of features inside the donut buffer
	# to the output text file
	if self.count_on_off:
	    #self.countList = MSBuffer.removeDuplicateList(self, self.countList)
	    self.txtCountFeat = open(self.txtCountFeat_name, 'a')
	    self.txtCountFeat.write(idcod+','+','.join(str(x) for x in self.countList))
	    self.txtCountFeat.write('\n')
	    self.txtCountFeat.close()		    
	    self.countList = []
	    
	# BUFFER AREAS
	self.txtBufferArea = open(self.txtBufferArea_name, 'a')
	self.txtBufferArea.write(idcod+','+','.join(str(x) for x in self.listDonutMapAreas)) # File header
	self.txtBufferArea.write('\n')
	self.txtBufferArea.close()
	self.listDonutMapAreas = []
	
	
#----------------------------------------------------------------------------------
# The Run class calls MSBuffer functions in order to perform the Multi-Scale buffer analysis
# It inherits the MSBuffer class

class Run(MSBuffer):
    
    # Initializing parameters
    def __init__(self, inputmap, inputmap_name, inputCol, variable_interest, variable_interest_name, OutPutTxt, OutPutFolder, save_maps,
                 scale, nbuffers, count_on_off, area_length_on_off, func_area_length_on_off):
	
	if not (count_on_off or area_length_on_off or func_area_length_on_off):
	    string_error = "At least one of the options must be selected:\n" + \
		"Count Features\nCalculate Area/Length\nCalculate Functional Area/Length\n\n" + \
		"Please, select one of them and try again!"
	    
	    raise Exception(string_error)
	
	
	MSBuffer.__init__(self, inputmap, inputmap_name, inputCol, variable_interest, variable_interest_name, OutPutTxt, OutPutFolder, save_maps,
                 scale, nbuffers, count_on_off, area_length_on_off, func_area_length_on_off)
	
	# Clear selection of features
	arcpy.SelectLayerByAttribute_management(self.inputmap, "CLEAR_SELECTION")	
    	
    def run(self):
	'''
	Function run
	
	In this function the analysis is performed.
	'''
	
	#----------
	# Preparing
	
	# Define the geometry of the variable of interest
	MSBuffer.typeFeature(self)  
	# Create the list of polygon IDs, from the input map
	MSBuffer.createInputMapIDList(self)
	# Define the list of buffer sizes
	MSBuffer.defineScale(self)
	# If the Geodatabase does not exist, creates it
	MSBuffer.createDb(self)
	
	#---------
	# Analyses
	
	# Change to output folder
	os.chdir(OutPutFolder)
	
	# Initialize output text file for area analysis
	MSBuffer.initializeOutputTxt(self)
	
	# If the maps will be saved, the previous maps inside the geodatabase may be deleted
	# Delete previous files from the geodatabase, to perform new analysis
	if overwrite_maps == True:
	    MSBuffer.deleteFiles(self)	    
		
	# Initializing counter for getting polygon ID from the input map (around which buffers are drawn)
	self.counter = 0	
	
	# For each feature in the input map:
	for i in self.referenceListquery:
		
	    # Select the feature from the input map
	    arcpy.SelectLayerByAttribute_management(self.inputmap, "NEW_SELECTION", i)
	    # Create Buffer (with the feature embedded)
	    MSBuffer.createBuffer(self)
	    # Erase the input map feature from the buffer, generating a donut buffer
	    MSBuffer.erase(self)
	    
	    # Count features
	    if self.count_on_off:
		MSBuffer.countFeatures(self)
	    # Calculate Functional Area
	    if (self.isArea or self.isLine) and self.func_area_length_on_off:
		MSBuffer.calcFunctionalArea_Length(self)	    
	
	    # Calculate Area
	    if (self.isArea or self.isLine) and self.area_length_on_off:
		MSBuffer.clip_variable_interest_by_donut_buffer(self)
		# The functions deleteField and addField, which delete the area column and recalculates it, are not being used,
		# since the area of polygons of the variable of interest inside the donut buffer are calculated through the "Shape_Area" column,
		# created automatically when the clip map is created.
		# However, the implementation may change, if needed. We keep the functions declared in case it is necessary
		#MSBuffer.deleteField(self)
		#MSBuffer.addField(self)
		MSBuffer.calculateArea_LengthInsideBuffer(self)
	    
	    # Write outputs
	    MSBuffer.createOutputTxt(self)	    
	    
	    # Next input map feature
	    self.counter = self.counter + 1
	    
	
	# Clear selection
	arcpy.SelectLayerByAttribute_management(self.inputmap, "CLEAR_SELECTION")
	
	# If the maps will not be saved, delete them
	if not self.save_maps:
	    ## Delete files from the geodatabase
	    MSBuffer.deleteFiles(self)	
	
	    
#----------------------------------------------------------------------------------
# Running the analysis
	
# Run instance
run_instance = Run(inputmap, inputmap_name, inputCol, variable_interest, variable_interest_name, OutPutTxt, OutPutFolder, save_maps,
                   scale, nbuffers, count_on_off, area_length_on_off, func_area_length_on_off)
# Run
run_instance.run()
