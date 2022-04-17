from legacy import Sim, Utilities as Ut
import RedNeuronal

# Modelo02_02 control de bifurcaciones - Genetico Colas
individuosPorGeneracion = 6
generaciones = 10
tiempoSimulacion = 2000
coeficienteProduccion = 0.8
coeficienteColas = 0.2

NN1 = []
NN2 = []
resultados = 0
fitness = [0, 0]
coste1 = 0
coste2 = 0

simulador = Sim.Simulador02(logs=True)

colas1 = [[11, 12], [6, 7, 19, 20, 21, 22, 23, 32, 33], [8, 13, 14], [15, 25, 26, 27], [16, 17, 18], [29, 30]]
colas2 = [[11, 12], [6, 7, 19, 20, 21, 22, 23, 32, 33], [8, 13, 14], [15, 25, 26, 27], [16, 17, 18], [29, 30]]

# 0 -> % Ocupacion de tipo 0
# 1 -> % Ocupacion de tipo 1
############### 01 ## 02 ## 03 ## 04 ## 05 ## 06 ##
###############0  1  0  1  0  1  0  1  0  1  0  1######
dataset01 = [
    [[0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0], 0],
    [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1],
    [[0, 0, 0, 0, 0, 0, 0.7, 0, 0, 0, 0, 0], 0],
    [[0, 0, 0, 0, 0, 0, 0.3, 0, 0, 0, 0, 0], 1]
]

dataset02 = [
    [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0], 0],
    [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 1],
    [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.7, 0], 0],
    [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0.3, 0], 1]
]

NN1 = RedNeuronal.NN02_03_01(colas1)
NN2 = RedNeuronal.NN02_03_02(colas2)

NN1.cargarModelo('02_03_01_v2')
NN2.cargarModelo('02_03_02_v2')

for epoch in range(0, 25000):
    if epoch % 5000 == 0:
        Ut.pNoEs('Epoch ')
        print(epoch)
    if epoch % 100 == 99:
        Ut.pNoEs('Error 1: ')
        try:
            Ut.pNoEs(coste1.item())
        except:
            pass
        Ut.pNoEs('Error 2: ')
        try:
            print(coste2.item())
        except:
            pass

    for sample in dataset01:
        NN1.setEntrada([sample[0]])
        NN1.calculaSalida()
        coste1 = NN1.entrenar(sample[1], 0.1)

    for sample in dataset02:
        NN2.setEntrada([sample[0]])
        NN2.calculaSalida()
        coste2 = NN2.entrenar(sample[1], 0.1)

simulador = Sim.Simulador02(logs=True)
resultados = simulador.simular(NN1, NN2, tiempoSimulacion)

fitness[0] = NN1.fitness(resultados, coeficienteProduccion, coeficienteColas)
fitness[1] = NN2.fitness(resultados, coeficienteProduccion, coeficienteColas)
print(resultados.produccion)
print(fitness)

NN1.guardarModelo('02_03_01_v3')
NN2.guardarModelo('02_03_02_v3')
