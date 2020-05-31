from ..Script import Script
import re
class XGantryWipe(Script):
    version = "1.0"
    def __init__(self):
        super().__init__()

    def getSettingDataString(self):
        return """{
            "name":"X Gantry Wipe """ + self.version + """",
            "key":"XGantryWipe",
            "metadata": {},
            "version": 2,
            "settings":
            {
                "wipe_layer":
                {
                    "label": "Wipe Frequency",
                    "description": "Wipe every N layers",
                    "unit": "Layers",
                    "type": "int",
                    "default_value": 1
                },
                "wipeCount":
                {
                    "label": "Wipe Count",
                    "description": "How many times to perform wipe motion",
                    "unit": "Wipes",
                    "type": "int",
                    "default_value": 1
                },
                "Xlow":
                {
                    "label": "Brush X Start",
                    "description": "The X gantry value where brush contacts",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 235
                },
                "Xhigh":
                {
                    "label": "Brush X Finish",
                    "description": "The X gantry value where brush has completed stroke",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 255
                },
                "Zhop":
                {
                    "label": "Z hop",
                    "description": "How far to hop to avoid printed parts when going to wipe",
                    "unit": "mm",
                    "type": "float",
                    "default_value": 2
                }
            }
        }"""
#getMyValue is like the script default getValue, but can find <1 values. 
    def getMyValue(self, line, key, default = None):
        if not key in line or (';' in line and line.find(key)> line.find(';')):
            return default
        sub_part = line[line.find(key)+len(key):]
        m = re.search('^[-+]?[0-9]*\.?[0-9]*',sub_part)
        if m is None:
            return default
        try:
            return float(m.group(0))
        except:
            return default
            
    def getMyCommentVal(self, line, key, default = None): #less safe version that doesn't ignore comments.
        if not key in line:
            return default
        sub_part = line[line.find(key)+len(key):]
        m = re.search('^[-+]?[0-9]*\.?[0-9]*',sub_part)
        if m is None:
            return default
        try:
            return float(m.group(0))
        except:
            return default

    def buildGCode(self,Xlow_local,Xhigh_local,wipeCount_local,Zhop_local,X_resume,Z_resume):
        wipeGcode = "; BEGIN WIPE: " + str(wipe_count) + "\n"
        wipeGcode += "M211S0\n" # Allows travel past bed size
        # wipeGcode += "G0F" + str(travelSpeed_local) + "\n" # Sets Speed
        wipeGcode += "G0Z" + str(Z_resume + Zhop_local) + "\n" # Move Z up by hop distance
        for thisWipe in range(0, wipeCount_local):
            wipeGcode += "G0X" + str(Xlow_local) + "\n" # Move on X to start wipe
            wipeGcode += "G0X" + str(Xhigh_local) + "\n" # Move on X to end wipe
        wipeGcode += "G0X" + str(X_resume) + "\n" # Move X back to start
        wipeGcode += "G0Z" + str(Z_resume) + "\n" # Move Z back to start
        wipeGcode += "M211S1\n" # Cancel travel past bed size
        return wipeGcode

    def execute(self,data):
        wipeEveryN = self.getSettingValueByKey("wipe_layer")
        xLow = self.getSettingValueByKey("Xlow")
        xHigh = self.getSettingValueByKey("Xhigh")
        wipeCountPerLayer = self.getSettingValueByKey("wipeCount")
        zHop = self.getSettingValueByKey("Zhop")
        wipeEveryLayerCounter = 0
        layers_started = False
        last_layer = False
        last_speed = 3030303030 #wipe script is added at the start of indicated layers. So throughout the previous layer, I should look for Fcommands, and keep the most recent one.
        resume_speed = 3030303030
        global wipe_count
        wipe_count = 0
        total_layers = -555555555555#wary as last_layer counting system relies on wipe_count and I don't want cura to break the script by devising "negative layers" or something like that
        for layer in data: #data is already split by layers as given by cura (see tweakZ for same format)
            lines = layer.splitlines() #'Ive used both layer.split("\n") and this, but find same behavior. I believe all gcode from cura should split on \n, but a stackexchange answer said it can be platform dependant as a general convention so I chose to use splitlines to circumvent that. 
            first_Z = None
            first_X = None
            wipe_gcode = None #reset the wipe gcode per layer
            for line in lines:
                if ";LAYER_COUNT:" in line:
                    total_layers = self.getMyCommentVal(line,';LAYER_COUNT:')
                    total_layers = int(round(total_layers,0))
                if ";LAYER:1" in line: #should run once when passing LAYER:N
                    layers_started = True
                    #wipe_gcode = "Total Layer No. = " + str(total_layers) + "\n" #TODO REMOVE THIS DEBUG
                if not layers_started: #should run once after passed LAYER:N
                    continue
                if (";LAYER:"+str(total_layers-1)) in line:
                    last_layer = True
                #Next, searching for the first Z, first X, first Y, and last F. 
                if self.getMyValue(line,'G') == 1 or self.getMyValue(line,'G') == 0:
                    if first_Z == None: #only act if we haven't found Z yet in this layer
                        first_Z = self.getMyValue(line,'Z') #should return None if doesn't find anything in this line
                    if first_X == None: #TODO consider case of X1 command then a Y1 command later (I.e, first X command isn't in same line as first Y command)
                        first_X = self.getMyValue(line,'X') #should return None if doesn't find anything
                    if self.getMyValue(line,'F') != None:
                        if (self.getMyValue(line,'X') != None) or (self.getMyValue(line,'Y')!=None): #only count F commands that include some XY motion to ignore slow extruder or Z speeds. TODO: Consider that this 'safety' should not be required, because even if you set the speed to that slower speed, if it truly was the last F command in a layer, the next layer should fix itself (or else it would fail without the wipe code)
                            last_speed = self.getMyValue(line,'F')
                            
            if not layers_started: #should run once after passed LAYER:N
                continue
            
            wipeEveryLayerCounter+=1 #this counter should reset each time you build and store a wipe code
            wipe_count += 1 #this is a more general count of what potential wipe layer you're on, but mostly defunct code (cleanup?)
            if wipeEveryLayerCounter<wipeEveryN: #e.g, wipe every 2 layers. counter =1, N=2. Second layer should wipe and reset counter to 0.  
                if last_speed != None:  #See this same line later, after buildGcode. Even if you skip buildGcode you still want to track your previous layer speed, for the next buildGcode to have a speed ready.  
                    resume_speed = last_speed  
                if last_layer == True:  #There are two last layer checks, they could probably be consolidated to (1) in front of both of them, that checks for N-1 of the current check [checking within this loop was chosen as an extension of the original test before wiping every N layers was implemented [original test was after the last gcode one adds rather than before building]]
                    return data 
                continue #skips the wipe gcode generation and inclusion (below)
            else:
                wipeEveryLayerCounter=0 #resets the wipe skipping counter. Assume default wipeEveryN = 1, should turn 0 here, then turn to 1 again by the +=1 val. 

            wipe_gcode = self.buildGCode(xLow,xHigh,wipeCountPerLayer,zHop,first_X,first_Z)

            #add the wipe code adding -format pulled from BQ Pause@height code
            index = data.index(layer) #find our current layer
            layer = wipe_gcode + layer #add wipe code then (is there order of operations to string addition? Presumably)
            data[index] = layer
            if last_layer == True:
                return data
        return data