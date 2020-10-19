from .shape_ratio import shape_ratio


# calculate taper automatically
def find_taper(length, taper, shape, shapeS, levels, customShape):
    taperS = []
    for i, t in enumerate(length):
        if i == 0:
            shp = 1.0
        elif i == 1:
            shp = shape_ratio(shape, 0, custom=customShape)
        else:
            shp = shape_ratio(shapeS, 0)
        t = t * shp
        taperS.append(t)

    taperP = []
    for i, t in enumerate(taperS):
        pm = 1
        for x in range(i+1):
            pm *= taperS[x]
        taperP.append(pm)

    taperR = []
    for i, t in enumerate(taperP):
        t = sum(taperP[i:levels])
        taperR.append(t)

    taperT = []
    for i, t in enumerate(taperR):
        try:
            t = taperP[i] / taperR[i]
        except ZeroDivisionError:
            t = 1.0
        taperT.append(t)

    taperT = [t * taper[i] for i, t in enumerate(taperT)]

    return taperT