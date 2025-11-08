from varasto import Varasto


def main():
    olutta = Varasto(100.0, 20.2)

    print(f"Olutvarasto: {olutta}")

    print("Olut getterit:")
    print(f"saldo = {olutta.saldo}")
    print(f"tilavuus = {olutta.tilavuus}")
    print(f"paljonko_mahtuu = {olutta.paljonko_mahtuu()}")

    print("Varasto(-100.0);")
    huono = Varasto(-100.0)
    print(huono)

if __name__ == "__main__":
    main()
