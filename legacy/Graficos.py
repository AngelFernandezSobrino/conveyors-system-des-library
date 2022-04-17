import RedNeuronal
import matplotlib.pyplot as plt

# Graficos tendencias NN

NN = 0

colas = [[11, 12],
         [6, 7, 19, 20, 21, 22, 23, 32, 33],
         [8, 13, 14],
         [15, 25, 26, 27],
         [16, 17, 18],
         [29, 30]]

datos = []
resultados = []

# 0 -> Ocupacion de tipo 0
# 1 -> Ocupacion de tipo 1
############## 01 ## 02 ## 03 ## 04 ## 05 ## 06 ##
##############0  1  0  1  0  1  0  1  0  1  0  1######
dataset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

NN = RedNeuronal.NN01_02(colas)

NN.cargarModelo('01_03_final')

for cola in range(0, len(dataset)):
    dataset = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
    resultados.append([])
    datos.append([])
    for sample in range(0, 100):
        dataset[cola] = sample / 100
        NN.setEntrada([dataset])
        NN.calculaSalida()
        datos[cola].append(dataset[cola])
        resultados[cola].append(NN.salida)
for cola in range(0, len(dataset)):
    plt.figure(cola)
    plt.plot(datos[cola], resultados[cola])

plt.show()
