from math import degrees, pi, atan2
from pyo import *

s = Server().boot().start()

osc = OscReceive(port=8000, address=["/mrmr/accelerometerX/1/iPhone-Alex",
                                     "/mrmr/accelerometerY/1/iPhone-Alex",
                                     "/mrmr/accelerometerZ/1/iPhone-Alex"])

oscx = Scale(osc["/mrmr/accelerometerX/1/iPhone-Alex"], inmin=0, inmax=1, outmin=-90, outmax=90)
oscy = Scale(osc["/mrmr/accelerometerY/1/iPhone-Alex"], inmin=0, inmax=1, outmin=-90, outmax=90)
oscz = Scale(osc["/mrmr/accelerometerZ/1/iPhone-Alex"], inmin=0, inmax=1, outmin=-90, outmax=90)

def convert_data():
    x, y, z = oscx.get(), oscy.get(), oscz.get()
    degx = degrees(atan2(-y, -z) + pi);
    degy = degrees(atan2(-x, -z) + pi);
    degz = degrees(atan2(-y, -x) + pi);
    print [degx,degy,degz]
    
met = Metro(time=.25).play()
trigfunc = TrigFunc(met, convert_data)

s.gui()