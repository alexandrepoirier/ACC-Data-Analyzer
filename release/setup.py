#!/usr/bin/env python

from distutils.core import setup
import os, sys, subprocess

###INFOS logiciel
name = 'ACC Data Analyzer'
version = '0.1.0'
full_description = "This small utility program is built to receive accelerometer \
data from a phone or a tablet via the Open Sound Control protocol and then uses this \
information and converts it to three meta-variables which are : activity, roughness, \
and magnitude. You can then send that data back with OSC and use them along with the \
raw accelerometer data to control synthesizers or effects."
pyversion = str(sys.version_info[0])+'.'+str(sys.version_info[1])
site_pack_path = os.path.join(sys.prefix, 'lib', 'python'+pyversion, 'site-packages')
inspath = os.path.join(site_pack_path, 'accdata')

def listImgFiles(path):
    list = [os.path.join(path,f) for f in os.listdir(path) if os.path.isfile(os.path.join(path,f))]
    if list[0].find('DS_Store') != -1: del list[0]
    return list

setup(name=name,
      version=version,
      description='Uses accelerometer data, converts it to meta-variables, and sends it using OSC.',
      long_description=full_description,
      license='BSD',
      platforms=['OSX','Linux','Windows'],
      author='Alexandre Poirier',
      author_email='alexpoirier05@gmail.com',
      url="http://www.google.ca",
      packages=['accdata', 'accdata.Ressources','accdata.Ressources.config','accdata.Ressources.data'],
      data_files=[(inspath+'/Ressources/img/default', listImgFiles('accdata/Ressources/img/default')),
                  (inspath+'/Ressources/img/mac', listImgFiles('accdata/Ressources/img/mac'))],
      requires=['pyo(>=0.6.8)','wxPython(==2.8.12)','python(>=2.7.6)']
     )
     
def writeLaunchSh(path):
    try:
        f = open("accdatacmd", "w")
        f.write("#!/bin/sh\ncd ")
        f.write(path)
        f.write("\npython __main__.py")
    except IOError, e:
        print "Can't write shell script. Please provide me with the traceback via email."
        print str(e)
    else:
        f.close()
        
def writeUninstallSh(path):
    info_file = name.replace(" ", "_")+"-"+version+"-py"+pyversion+".egg-info"
    try:
        f = open("uninstall.sh", 'w')
        f.write("#!/bin/sh\n")
        f.write("echo Deleting application files...\n")
        f.write("sleep 1\n")
        f.write("sudo rm -R "+inspath+"\n")
        f.write("echo Removing remaining files...\n")
        f.write("sleep 1\n")
        f.write("sudo rm "+os.path.join(site_pack_path, info_file)+"\n")
        f.write("sudo rm /usr/local/bin/accdata\n")
        f.write("echo Finished uninstalling ACC Data Analyzer.")
    except IOError, e:
        print "Couldn't write the uninstall script. Don't worry, just write me an email!"
        print str(e)
    else:
        f.close()
        
writeLaunchSh(inspath)
writeUninstallSh(inspath)

shell_script = subprocess.call(['sudo', 'sh', 'setup.sh'],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE)