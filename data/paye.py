

TI = 59000

if 10000 < TI < 25000:
    paye = TI * 0.07
elif 25000 < TI < 50000:
    paye = ((TI - 25000) * 0.11) + 1750
elif 50000 < TI < 91666.66:
    paye = ((TI - 50000) * 0.15) + 4500
elif 91666.66 < TI < 133333.32:
    paye = ((TI - 91666.66) * 0.19) + 10749.99
elif 133333.32 < TI < 266666.66:
    paye = ((TI - 133333.32) * 0.21) + 18665
elif TI > 266666.66:
    paye = ((TI - 266666.66) * 0.24) + 46664.99
elif TI < 10000:
    paye = 0
    print(paye)
