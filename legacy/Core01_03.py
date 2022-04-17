from legacy import Sim, Utilities as Ut
import RedNeuronal

# Modelo01_03 control de producto a fabricar - Genetico Backprop
individuosPorEpoca = 10
generaciones = 40
tiempoSimulacion = 2000
individuosSeleccion = 2
coeficienteProduccion = 0.6
coeficienteColas = 10
coeficienteMutacion = 0.15
seleccion = [0, 0]

NN = 0
resultados = 0
fitness = 0
coste = 0
costeAv = 0

simulador = Sim.Simulador01(logs=True)

colas = [[11, 12],
         [6, 7, 19, 20, 21, 22, 23, 32, 33],
         [8, 13, 14],
         [15, 25, 26, 27],
         [16, 17, 18],
         [29, 30]]

# 0 -> Ocupacion de tipo 0
# 1 -> Ocupacion de tipo 1
############## 01 ## 02 ## 03 ## 04 ## 05 ## 06 ##
##############0  1  0  1  0  1  0  1  0  1  0  1######
dataset = [[[0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], 1],
           [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1], 0],
           [[0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1],
           [[0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0], 0],
           [[0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0], 1],
           [[0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0], 0],
           [[0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0], 1],
           [[0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0], 0],
           [[1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1],
           [[0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0],
           [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 0]
           ]

NN = RedNeuronal.NN01_03(colas)

# NN.cargarModelo('01_03_prueba')

datafile = open('resultados/dataTrainingModelo01_03-sgd2.txt', 'w')

for epoch in range(0, 5000):
    if epoch % 500 == 0:
        Ut.pNoEs('Epoch ')
        print(epoch)
    if epoch % 100 == 99:
        Ut.pNoEs('Error ')
        print(costeAv / len(dataset))
    try:
        datafile.writelines(str(costeAv / len(dataset)) + '\n')
    except:
        pass
    costeAv = 0
    for sample in dataset:
        NN.setEntrada([sample[0]])
        NN.calculaSalida()
        coste = NN.entrenar(sample[1], 3e-3)

        try:
            costeAv += coste.item()
        except:
            pass

simulador = Sim.Simulador01(logs=True)
resultados = simulador.simular(NN, tiempoSimulacion)

fitness = NN.fitness(resultados, coeficienteProduccion, coeficienteColas)
print(resultados.produccion)
print(fitness)

# NN.guardarModelo('01_03_sgd')
