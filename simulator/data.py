class Output:
    def __init__(self, tiposDiferentes, cantidadRetenedores):
        self.produccion = []
        self.tiempoReposo = []
        self.tiempoPeticion = []
        self.tiempoAvance = []
        self.tiempoProceso = []

        for i in range(0, tiposDiferentes):
            self.produccion += [0]

        for i in range(0, cantidadRetenedores):
            self.tiempoReposo += [0]
            self.tiempoPeticion += [0]
            self.tiempoAvance += [0]
            self.tiempoProceso += [0]

    def producir(self, tipo):
        self.produccion[tipo] += 1

    def incrementarTiempo(self, retenedor, elemento):
        if elemento == 'reposo':
            self.tiempoReposo[retenedor] += 1
        if elemento == 'peticion':
            self.tiempoPeticion[retenedor] += 1
        if elemento == 'avance':
            self.tiempoAvance[retenedor] += 1
        if elemento == 'proceso':
            self.tiempoProceso[retenedor] += 1

    def print(self):
        print('')
        Ut.pNoEs('Produccion: ')
        print(self.produccion)
        Ut.pNoEs('Reposo: ')
        print(self.tiempoReposo)
        Ut.pNoEs('Peticion: ')
        print(self.tiempoPeticion)
        Ut.pNoEs('Avance: ')
        print(self.tiempoAvance)
        Ut.pNoEs('Proceso: ')
        print(self.tiempoProceso)

    def exportar(self):
        return [self.produccion, self.tiempoReposo, self.tiempoProceso, self.tiempoPeticion, self.tiempoAvance]
