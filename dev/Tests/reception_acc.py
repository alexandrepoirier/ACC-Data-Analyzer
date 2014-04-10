from math import degrees, pi, atan2
from pyo import *

s = Server().boot().start()

osc = OscListReceive(port=8000, address="/accxyz", num=3)

oscx = Scale(osc["/accxyz"][0], inmin=-1, inmax=1, outmin=-90, outmax=90)
oscy = Scale(osc["/accxyz"][1], inmin=-1, inmax=1, outmin=-90, outmax=90)
oscz = Scale(osc["/accxyz"][2], inmin=-1, inmax=1, outmin=-90, outmax=90)

def convert_data():
    x, y, z = [oscx.get(),oscy.get(),oscz.get()]
    degx = degrees(atan2(-y, -z) + pi);
    degy = degrees(atan2(-x, -z) + pi);
    degz = degrees(atan2(-y, -x) + pi);
    print [degx,degy,degz]
    
met = Metro(time=.25).play()
trigfunc = TrigFunc(met, convert_data)

s.gui()