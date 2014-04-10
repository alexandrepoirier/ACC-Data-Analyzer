import numpy

def smoothListGaussian(list,degree=5):  

     window=degree*2-1  

     weight=numpy.array([1.0]*window)  

     weightGauss=[]  

     for i in range(window):  

         i=i-degree+1  

         frac=i/float(window)  

         gauss=1/(numpy.exp((4*(frac))**2))  

         weightGauss.append(gauss)  

     weight=numpy.array(weightGauss)*weight  

     smoothed=[0.0]*(len(list)-window)  

     for i in range(len(smoothed)):  

         smoothed[i]=sum(numpy.array(list[i:i+window])*weight)/sum(weight)  

     return smoothed

#ajouter 5 valeurs au debut et 4 a la fin
data = [175,175,175,175,175,175.556, 175.556, 176.221, 176.591, 176.798, 176.913, 
        176.977, 178.182, 178.854, 179.229, 179.438, 179.555, 179.735, 179.735, 
        179.837, 179.894, 179.926, 179.944, 179.954, 179.947, 179.943, 179.941, 
        179.940, 179.939, 181.778, 181.778, 182.792, 183.354, 183.667, 183.842, 
        183.940, 184.871, 185.398, 185.693, 185.859, 185.952, 189.002, 190.610, 
        190.610, 191.479, 191.969, 192.730, 193.167, 193.413, 193.551, 193.628, 
        193.671, 195.165, 195.990, 196.448, 196.448, 196.703, 196.845, 196.925, 
        196.969, 197.790, 198.256, 198.519, 198.667, 200.332, 201.259, 201.776, 
        201.776, 202.065,202,202,202,202]
        
a = smoothListGaussian(data)
print a
print len(a)