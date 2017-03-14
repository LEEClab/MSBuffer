# MSBuffer

This is a repository for sharing code of the ArcGIS toolbox Multi-Scale Buffer (MSBuffer). It is a free and open source package built as an ArcToolbox in a python script to perform multi-scale spatial analyses for Conservation Unit buffer zones delimitation and management.

LSCorridors was developed and is maintained by the [Spatial Ecology and Conservation Lab](http://leec.eco.br) (LEEC), at Universidade Estadual Paulista, Rio Claro, SP, Brazil.

The repository has 3 folders:

- [MSBuffer_v1_00_code](https://github.com/LEEClab/MSBuffer/tree/master/MSBuffer_v1_00_code): here you can find the main MSBuffer stable script, as well as the ArcGIS toolbox itself.
- [old_versions](https://github.com/LEEClab/MSBuffer/tree/master/old_version): old versions of the code (before package release).
- [Data_test](https://github.com/LEEClab/MSBuffer/tree/master/Data_test): maps and data for testing and tutorials.

## How to use

MSBuffer runs as a ArcToolbox, therefore you should first install ArcGIS in your computer. You download and find installation procedures [here](http://www.esri.com/en/arcgis/products/arcgis-pro/DesktopFreeTrial) and [here](http://desktop.arcgis.com/en/arcmap/10.3/get-started/installation-guide/installing-on-your-computer.htm)

###Adding  MSBuffer as ArcToolbox inside ArcMap.
- Open ArcMap with an empty map document file and open the ArcToolbox window.
- Right-click on ArcToolbox> Add toolbox and navigate to the folder where you have saved to MSBuffer.
- Open the toolbox by selecting MSBuffer.tbx and clicking on the Open button. The MSBuffer should now be displayed in ArcToolbox.

### Three basic steps to run MSbuffer: 
#### 1. What do you need to use this tool? 
-  ArcMap installed and MSBuffer added as toolbox
- A map (a  Conservation Unit, forest fragment, a city map, an area of interest, etc.).
- A variable of interest ( point, line or polygon maps with information about, for example, species occurrence, caves occurrence, forest cover, land use type, roads, etc.).
#### 2. Running MSBuffer
1. Input the map of the area of interest in the "Input Map" and select the identification column (eg. name of the area) in the attribute table of the map. In the case of the input map contains more than one polygon (eg. multiple conservation units or areas of interest) the program will run a similar buffer analysis for each area and the identification column and print the requested metrics according to the identification column specified.
2. Input the variable of interest (the response variable of the buffer analysis, eg. forest cover area).
3. Set the size of the buffer steps (the unit here is the same of your projection units, therefore, we strongly recommend that projections should be set to meters).
4. Set how many buffer you want to run.
5. Choose the metrics you want to calculate (area, count, functional area).
6. Set the path for the output folder.
7. Name your output .txt file.
8. Click "ok" to run.



