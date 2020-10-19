from math import sin, pi


# This function calculates the shape ratio as defined in the paper
def shape_ratio(shape, ratio, pruneWidthPeak=0.0, prunePowerHigh=0.0, prunePowerLow=0.0, custom=None):
    if shape == 0:
        return 0.05 + 0.95*ratio #0.2 + 0.8*ratio
    elif shape == 1:
        return 0.2 + 0.8*sin(pi*ratio)
    elif shape == 2:
        return 0.2 + 0.8*sin(0.5*pi*ratio)
    elif shape == 3:
        return 1.0
    elif shape == 4:
        return 0.5 + 0.5*ratio
    elif shape == 5:
        if ratio <= 0.7:
            return 0.05 + 0.95 * ratio/0.7
        else:
            return 0.05 + 0.95 * (1.0 - ratio)/0.3
    elif shape == 6:
        return 1.0 - 0.8*ratio
    elif shape == 7:
        if ratio <= 0.7:
            return 0.5 + 0.5*ratio/0.7
        else:
            return 0.5 + 0.5*(1.0 - ratio)/0.3
    elif shape == 8:
        r = 1 - ratio
        if r == 1:
            v = custom[3]
        elif r >= custom[2]:
            pos = (r - custom[2]) / (1 - custom[2])
            #if (custom[0] >= custom[1] <= custom[3]) or (custom[0] <= custom[1] >= custom[3]):
            pos = pos * pos
            v = (pos * (custom[3] - custom[1])) + custom[1]
        else:
            pos = r / custom[2]
            #if (custom[0] >= custom[1] <= custom[3]) or (custom[0] <= custom[1] >= custom[3]):
            pos = 1 - (1 - pos) * (1 - pos)
            v = (pos * (custom[1] - custom[0])) + custom[0]

        return v

    elif shape == 9:
        if (ratio < (1 - pruneWidthPeak)) and (ratio > 0.0):
            return ((ratio/(1 - pruneWidthPeak))**prunePowerHigh)
        elif (ratio >= (1 - pruneWidthPeak)) and (ratio < 1.0):
            return (((1 - ratio)/pruneWidthPeak)**prunePowerLow)
        else:
            return 0.0

    elif shape == 10:
        return 0.5 + 0.5 * (1 - ratio)