from wx.tools import img2py
import os

def listImgFiles(path):
    list = [os.path.join(path,f) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    if list[0].find('DS_Store') != -1: del list[0]
    return list
    
def convertImagesToPy(list, target):
    for i in range(len(list)):
        img2py.img2py(list[i], target, True)
    print "\n#############################################################"
    print "Done converting %d files to %s." % (len(list), target)
    print "#############################################################\n"
    
convertImagesToPy(listImgFiles("Ressources/img/mac"), "Ressources/img/mac_icons.py")
convertImagesToPy(listImgFiles("Ressources/img/default"), "Ressources/img/default_icons.py")