import numpy

x = [157.979, 157.979, 160.909, 162.602, 163.566, 164.110, 164.416, 170.604, 
     174.086, 176.029, 177.111, 177.715, 178.725, 178.725, 179.240, 179.515, 
     179.665, 179.747, 179.793, 179.767, 179.752, 179.744, 179.740, 179.737, 
     187.569, 187.569, 191.708, 193.932, 195.145, 195.814, 196.185, 201.127, 
     204.112, 205.850, 206.842, 207.403, 220.037, 225.849, 225.849, 228.733, 
     230.239, 231.862, 232.724, 233.193, 233.451, 233.594, 233.674, 235.859, 
     236.936, 237.499, 237.499, 237.803, 237.969, 238.061, 238.112, 240.048, 
     241.104, 241.686, 242.009, 246.167, 248.316, 249.465, 249.465, 250.092]

y = [259.122, 259.122, 259.196, 259.236, 259.259, 259.272, 259.279, 259.144, 
     259.070, 259.028, 259.005, 258.992, 258.274, 258.274, 257.871, 257.645, 
     257.519, 257.448, 257.408, 257.232, 257.132, 257.075, 257.044, 257.026, 
     256.854, 256.854, 256.760, 256.707, 256.678, 256.661, 256.652, 257.562, 
     258.080, 258.372, 258.536, 258.628, 259.322, 259.693, 259.693, 259.896, 
     259.997, 259.941, 259.904, 259.882, 259.870, 259.864, 259.860, 259.586, 
     259.433, 259.348, 259.348, 259.301, 259.274, 259.259, 259.251, 259.524, 
     259.681, 259.770, 259.820, 260.704, 261.206, 261.490, 261.490, 261.649]

z = [175.556, 175.556, 176.221, 176.591, 176.798, 176.913, 176.977, 178.182, 
     178.854, 179.229, 179.438, 179.555, 179.735, 179.735, 179.837, 179.894, 
     179.926, 179.944, 179.954, 179.947, 179.943, 179.941, 179.940, 179.939, 
     181.778, 181.778, 182.792, 183.354, 183.667, 183.842, 183.940, 184.871, 
     185.398, 185.693, 185.859, 185.952, 189.002, 190.610, 190.610, 191.479, 
     191.969, 192.730, 193.167, 193.413, 193.551, 193.628, 193.671, 195.165, 
     195.990, 196.448, 196.448, 196.703, 196.845, 196.925, 196.969, 197.790, 
     198.256, 198.519, 198.667, 200.332, 201.259, 201.776, 201.776, 202.065]
     
def calculateRoughness(coord):
    a = (coord[-1] - coord[0]) / 63
    line = [a*i+coord[0] for i in range(64)]
    rough_count = 0
        
    for i in range(64):
        if abs(coord[i]-line[i]) > 8:
            rough_count += 1
    
    return rough_count

ax = numpy.array(x)
ay = numpy.array(y)
az = numpy.array(z)

dir_x = ax[0] - ax[-1]
dir_y = ay[0] - ay[-1]
dir_z = az[0] - az[-1]

magnitude = (abs(dir_x)/30*.1 +
             abs(dir_y)/30*.45 +
             abs(dir_z)/30*.45)
print "Magnitude : ", magnitude

activity = numpy.std(ax)*.1 + numpy.std(ay)*.45 + numpy.std(az)*.45
print "Activity : ", activity

rx = calculateRoughness(ax)*.1
ry = calculateRoughness(ay)*.45
rz = calculateRoughness(az)*.45
roughness = rx+ry+rz
print "Roughness : ", roughness

#Fonctions interessante
#Ecart tpye : numpy.std
#Moyenne : numpy.average
#Mediane : numpy.median
#Peak to peak : numpy.ptp