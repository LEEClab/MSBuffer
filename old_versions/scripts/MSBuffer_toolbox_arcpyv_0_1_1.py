#---------------------------------------------------------------------------------------
"""
 MSbuffer - MultiScale Buffer Analysis

 Bruno P. Leles - brunopleles@gmail.com
 John W. Ribeiro - jw.ribeiro.rc@gmail.com
 Juliana Silviera dos Santos - 
 Camila Eboli - 
 Alice C. Hughes - 
 Bernardo B. S. Niebuhr - bernardo_brandaum@yahoo.com.br
 Milton C. Ribeiro - mcr@rc.unesp.br

 Universidade Estadual Paulista - UNESP
 Rio Claro - SP - Brasil

 This script runs inside ArcMap v???? using Python shell.
 Usage: ????

 Short description

 Copyright (C) 2017 by Bruno P. Leles, John W. Ribeiro, and Milton C. Ribeiro.

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


# Import modules 
import arcpy
from arcpy import env
import os, sys
import arcpy.mapping

# Name of the geo database where output buffer maps will be saved
geoDB_name = "output_buffer_maps.gdb"
# Do we want to overwrite output buffer maps in case the analysis is re-run?
arcpy.env.overwriteOutput = True


# Reading parameters from the GUI
# Input map
UCs=arcpy.GetParameterAsText(0) # inputmap ao inves de UCs
inputCol=arcpy.GetParameterAsText(1)
UCsApoio=UCs.split("\\")
UCsApoio=UCsApoio[-1] # mudar UCsApoio - inputmap_name

# Input variable of interest
Veg=arcpy.GetParameterAsText(2) # veg -> variable_interest

# Scale (buffer size in meters)
escale=arcpy.GetParameterAsText(3)
escale=int(escale)

########## MUDAR NOME
# Multiplier field (number of buffers) 
mult=arcpy.GetParameterAsText(4)
mult=int(mult)

# Should we count the number of features?
boll=arcpy.GetParameterAsText(5)
feature_count=arcpy.GetParameterAsText(6) # campo de texto - talvez nao vamos precisar disso
feature_count=Veg

######## mudar para ser prefixo
# Prefix for output files 
OutPutTxt=arcpy.GetParameterAsText(7)

# DEFINIR NOMES DOS OUTPUTS
# prefix_area.txt
# prefix_count, functionalarea
# DEFINIR NOMES DOS OUTPUT MAPS (GEODB)

# Folder for output files
OutPutFolder=arcpy.GetParameterAsText(8)

# PODEMOS TESTAR SE OS PARAMETROS ESTAO OK, SAO VALIDOS!


#----------------------------------------------------------------------------------
# MSBuffer is the main class, in which the toolbox is initialized and runs

class MSBuffer(object):
    
    # Initializing parameters
    def __init__(self,UCs,UCsApoio,Veg,OutPutFolder,escale,mult,OutPutTxt,feature_count,boll,inputCol):
	
	self.inpuCol=inputCol #alsdjaslkjdslakj
	self.lista_escala_buffers=[]
	self.scale=escale
	self.mult=mult
	self.OutPutTxt=OutPutTxt
	self.lista_erases=[]
	self.fielArea=''
	self.fielPoint=''
        self.UCs=UCs
	self.UCsApoio=UCsApoio
        self.Veg=Veg
        self.OutPutFolder=OutPutFolder
        self.listbuffers=''
	self.Listerase=''
	self.listclip=''
	self.FieldList=[]
	self.cout=0
	self.feature=feature_count
	self.boll=boll
	self.countList=[]
	self.listaAreaFeatures=[]
	self.referenceListquery=[]
	self.listAreaAnalise=[]
	self.txtAreaAnalise=''
	self.txtFuncarea=''
	self.ListIDcod=[]
	self.txtCountFeat=''

        self.lista='' # para usar na def selectINlist
        self.pattern='' # para usar na def selectINlist
	
    # 
    def DefineEscale(self):
	'''
	Function DefineScale
	
	This function reads the scale (buffer size) and mutiplier (number of buffers) parameters 
	and defines a list of buffer sizes
	'''
	
	con_esc=self.scale 
	for i in range(self.mult):	
		self.lista_escala_buffers.append(con_esc) #criando lista de escala
		con_esc=con_esc+self.scale # Defining new buffer value
		
    # Creates a list of features (ID, names, ...) given the input map and the identificator column
    # each component of this list corresponds to a feature of the input map
    def CreateListaFieldReference(self):
	with arcpy.da.SearchCursor(self.UCs, self.inpuCol) as cursor:
	    for row in cursor:
		try:
		    temp=int(row[0])
		    self.ListIDcod.append(temp)
		    query="\""+self.inpuCol+"\"="+`temp`
		    self.referenceListquery.append(query)
		except:
		    self.ListIDcod.append(row[0])
		    query =  self.inpuCol+"='%s'" % row[0]
		    self.referenceListquery.append(query)
		    
		
		    
    # This function deletes pre-existing shape files in the output geodatabase
    def deletefiles(self):
	if os.path.exists(self.OutPutFolder+'/'+geoDB_name):
	    arcpy.env.workspace=self.OutPutFolder+'/'+geoDB_name
	    lista=arcpy.ListFeatureClasses()
	    for i in lista:
		inp=i.replace(".shp",'')
		arcpy.Delete_management(i)
		arcpy.Delete_management(inp)
		
    def selecInList(self):
        lista=[]
        for i in self.lista:
            if self.pattern in i:
                lista.append(i)
        return lista
        
    #criando um geodata base    
    def createDb(self):
        if not os.path.exists(self.OutPutFolder+'/'+geoDB_name):
            arcpy.CreateFileGDB_management(self.OutPutFolder,"ArcGisDataBase")
        
    #criando os buffers    
    def GeraBuffers(self):
        arcpy.env.workspace=self.OutPutFolder+'/'+geoDB_name
        for i in self.lista_escala_buffers:
            formatName="00000"+`i`
            formatName=formatName[-5:]
	    self.UCsApoio=self.UCsApoio.replace(".shp",'')
            OutPutName=self.UCsApoio+"_Buffer_"+formatName
            arcpy.Buffer_analysis(self.UCs,OutPutName,i,"FULL","FLAT","ALL")
	listbuffers=arcpy.ListFeatureClasses()
	self.lista=listbuffers
	self.pattern="_Buffer_"
	self.listbuffers=MSBuffer.selecInList(self)	
    
    
    
    def erase(self):
	for i in self.listbuffers:
		out_name=i.replace("Buffer","Erase")
		arcpy.Erase_analysis(i,self.UCs,out_name,'')   
		self.lista_erases.append(out_name)
	Listerase=arcpy.ListFeatureClasses()
	self.lista=Listerase
	
	self.pattern="_Erase_"
	self.Listerase=MSBuffer.selecInList(self)
    def typeFeature(self): # erro aqui!!!!!
	desc = arcpy.Describe(self.feature) # error na arcpy.Describe = IOError: "" does not exist
	geometryType = desc.shapeType
	if geometryType == 'Polygon':
	    self.fielArea=True # vendo se eh um poligono ou nao se nao for sera ponto
	    try:
		arcpy.AddField_management(self.feature, "area_ha", "DOUBLE", 10, 10)
		arcpy.CalculateField_management(self.feature,"area_ha","!shape.area@squaremeters!","PYTHON_9.3","#")
		expression="!Area_ha!/10000"
		arcpy.CalculateField_management(self.feature,"area_ha",expression,"PYTHON_9.3","#")		
	    except Exception as e:
		pass
	else:
	    self.fielPoint=True # neste cado eh um ponto
	
    
	    
	
    def count_Features(self):
	if self.fielArea:
	    
	    for erase in self.lista_erases:
		arcpy.SelectLayerByLocation_management(self.feature,"INTERSECT",erase)
		cursor = arcpy.da.SearchCursor(self.feature, ['FID'])
		count=0
		for i in cursor:
		    count=count+1
		self.countList.append(count)
		
		with arcpy.da.SearchCursor(self.feature, "area_ha") as cursor:
		    summed_total=0
		    for row in cursor:
			    summed_total = summed_total + row[0]
		    summed_total=round(summed_total, ndigits=2)
		    self.listaAreaFeatures.append(summed_total)
			
	if self.fielPoint:
	    
	    for erase in self.lista_erases:
		arcpy.SelectLayerByLocation_management(self.feature,"INTERSECT",erase)
		cursor = arcpy.da.SearchCursor(self.feature, ['FID'])
		count=0
		for i in cursor:
		    count=count+1
		self.countList.append(count)	    
	    
		
		
	    
		
		
    def clipVegByErase(self):
	for i in self.Listerase:
	    out_name=i.replace("Erase","Erase_Clip_Veg")
	    arcpy.Clip_analysis(self.Veg,i,out_name,"")
	    
	    Listclip=arcpy.ListFeatureClasses()
	    self.lista=Listclip
	    self.pattern="_Erase_Clip_Veg_"
	    self.listclip=MSBuffer.selecInList(self)	    
	    
    
    def checkField(self,mapa):
	fields = arcpy.ListFields(mapa)
	for field in fields:
	    self.FieldList.append(field.name)	
	return self.FieldList
    
    
    def deletefield(self):
	for i in self.listclip:
	    fields=MSBuffer.checkField(self, i)
	    if "Area_ha" in fields:
		arcpy.DeleteField_management(i, ["Area_ha"])    
    
    def addfield(self):
	for i in self.listclip:
	    try:
		arcpy.AddField_management(i, "Area_ha", "DOUBLE", 10, 10)
		arcpy.CalculateField_management(i,"Area_ha","!shape.area@squaremeters!","PYTHON_9.3","#")
		expression="!Area_ha!/10000"
		arcpy.CalculateField_management(i,"Area_ha",expression,"PYTHON_9.3","#")
	    except:
		print "pass"
    
    
    def calculateAreaAnalises(self):
	for i in self.listclip:
	    summed_total =0 
	    with arcpy.da.SearchCursor(i, "Shape_Area") as cursor:
		for row in cursor:
		    summed_total = summed_total + row[0]
		summed_total=round(summed_total, ndigits=2)
		summed_total=summed_total/10000
		self.listAreaAnalise.append(summed_total)

    def removeDuplicateList(self,lista):
	listaapoio=[]
	for i in lista:
	    if not i in listaapoio:
		listaapoio.append(i)
	
	return listaapoio
	    
	
    def criatxtArea_Analise(self):
	idcod=str(self.ListIDcod[self.cout])
	
	
	
	##----------------TXTAREAAnalise------------------------------------------------------
	#self.listAreaAnalise=MSBuffer.removeDuplicateList(self, self.listAreaAnalise)
	self.txtAreaAnalise.write(idcod+','+','.join(str(x) for x in self.listAreaAnalise))
	self.txtAreaAnalise.write('\n')
	self.listAreaAnalise=[]
	#-------------------------------------------------------------------------------------
	
	if self.fielArea==True:
	    self.listaAreaFeatures=MSBuffer.removeDuplicateList(self, self.listaAreaFeatures)
	    ##----------------TXTFunarea------------------------------------------------------
	    self.txtFuncarea.write(idcod+','+','.join(str(x) for x in self.listaAreaFeatures))
	    self.txtFuncarea.write('\n')
	    self.listaAreaFeatures=[]
	    #-------------------------------------------------------------------------------------	
	
	
	if self.boll:
	    
	    self.countList=MSBuffer.removeDuplicateList(self, self.countList)
	    self.txtCountFeat.write(idcod+','+','.join(str(x) for x in self.countList))
	    self.txtCountFeat.write('\n')
	    self.countList=[]		
		
	    #-------------------------------------------------------------------------------------		
	
	
	
			    
		
			
	

	
	
	
	
	
	
class principal(MSBuffer):
    def __init__(self, UCs, UCsApoio, Veg, OutPutFolder, escale, mult, 
                OutPutTxt, feature_count, boll, inputCol):
	MSBuffer.__init__(self, UCs, UCsApoio, Veg, OutPutFolder, escale, mult, 
	                  OutPutTxt, feature_count, boll, 
	                  inputCol)
    
    
		
		
    def run(self):
	
	

	MSBuffer.typeFeature(self)	# parece ter ERRO AQUI!!!    
	
	MSBuffer.CreateListaFieldReference(self)
	MSBuffer.DefineEscale(self) #definindo a lista de escalas
	MSBuffer.createDb(self)
	
	#area analises
	os.chdir(OutPutFolder)
	
	self.txtAreaAnalise=open("__AreaAnalises_"+self.OutPutTxt+".txt",'w')
	self.txtAreaAnalise.write(self.inpuCol+','+','.join(str(x) for x in self.lista_escala_buffers)) #cabecalho
	self.txtAreaAnalise.write('\n')
	#--------
	
	#Fuctional area
	if self.fielArea:
	    self.txtFuncarea=open("__FunctionalArea"+self.OutPutTxt+".txt",'w')
	    self.txtFuncarea.write(self.inpuCol+','+','.join(str(x) for x in self.lista_escala_buffers)) #cabecalho
	    self.txtFuncarea.write('\n')	
	
	if self.boll:
	    #Fuctional area
	    self.txtCountFeat=open("__CountFeatures_"+self.OutPutTxt+".txt",'w')
	    self.txtCountFeat.write(self.inpuCol+','+','.join(str(x) for x in self.lista_escala_buffers)) #cabecalho
	    self.txtCountFeat.write('\n')	    
	
	self.cout=0
	
	for i in self.referenceListquery:
	    MSBuffer.deletefiles(self) ###### colocar if overwrite = True
	    arcpy.SelectLayerByAttribute_management(self.UCs,"NEW_SELECTION",i)
	    MSBuffer.GeraBuffers(self)
	    MSBuffer.erase(self)
	    MSBuffer.count_Features(self)
	    MSBuffer.clipVegByErase(self)
	    MSBuffer.deletefield(self)
	    MSBuffer.addfield(self)
	    MSBuffer.calculateAreaAnalises(self)
	    MSBuffer.criatxtArea_Analise(self)
	
	    
	    
	    self.cout=self.cout+1
	self.txtAreaAnalise.close()
	
	if self.fielArea:
	    self.txtFuncarea.close()
	if self.fielPoint:
	    self.txtCountFeat.close()
	    
		    
	
fun=principal(UCs, UCsApoio, Veg, OutPutFolder, escale, mult, OutPutTxt, 
             feature_count, boll, inputCol)
fun.run()
