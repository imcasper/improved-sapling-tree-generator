from math import sin, pi


# This function calculates the shape ratio
def shape_ratio(shape, ratio, custom=None):
    if custom is None:
        custom = [.5, 1.0, .3, .5]
    if shape == 0:
        return 0.05 + 0.95 * ratio  # 0.2 + 0.8 * ratio

    elif shape == 1:
        return 0.2 + 0.8 * sin(pi * ratio)

    elif shape == 2:
        return 0.2 + 0.8 * sin(0.5 * pi * ratio)

    elif shape == 3:
        return 1.0

    elif shape == 4:
        return 0.5 + 0.5 * ratio

    elif shape == 5:
        if ratio <= 0.7:
            return 0.05 + 0.95 * ratio / 0.7
        else:
            return 0.05 + 0.95 * (1.0 - ratio) / 0.3

    elif shape == 6:
        return 1.0 - 0.8 * ratio

    elif shape == 7:
        if ratio <= 0.7:
            return 0.5 + 0.5 * ratio / 0.7
        else:
            return 0.5 + 0.5 * (1.0 - ratio) / 0.3

    elif shape == 9:  # old custom shape
        r = 1 - ratio
        if r == 1:
            v = custom[3]
        elif r >= custom[2]:
            pos = (r - custom[2]) / (1 - custom[2])
            pos = pos * pos
            v = (pos * (custom[3] - custom[1])) + custom[1]
        else:
            pos = r / custom[2]
            pos = 1 - (1 - pos) * (1 - pos)
            v = (pos * (custom[1] - custom[0])) + custom[0]
        return v

    elif shape == 8:
        r = 1 - ratio
        if r == 1:
            v = custom[3]
        else:
            custom[2] = min(custom[2], .99)
            if r >= custom[2]:
                t = (r - custom[2]) / (1 - custom[2])
                p1 = custom[1]
                p2 = custom[3]
            else:
                t = r / custom[2]
                p1 = custom[0]
                p2 = custom[1]

            slope1 = (custom[3] - custom[1]) / (1-custom[2])
            slope2 = (custom[1] - custom[0]) / custom[2]
            slope = (slope1 + slope2) / 2
            flat = False

            if (slope1 > 0 > slope2) or (slope1 < 0 < slope2):
                slope = 0.0
                flat = True

            h1 = slope * ((1 - custom[2]) / 2) + custom[1]
            h2 = -slope * (custom[2] / 2) + custom[1]

            if not flat:
                if (h1 < custom[3]) and (custom[0] > custom[3]):
                    h1 = custom[3]
                    slope = slope1 * 2
                    h2 = -slope * (custom[2] / 2) + custom[1]
                if (h2 < custom[0]) and (custom[3] > custom[0]):
                    h2 = custom[0]
                    slope = slope2 * 2
                    h1 = slope * ((1 - custom[2]) / 2) + custom[1]
                if (h1 > custom[3]) and (custom[0] < custom[3]):
                    h1 = custom[3]
                    slope = slope1 * 2
                    h2 = -slope * (custom[2] / 2) + custom[1]
                if (h2 > custom[0]) and (custom[3] < custom[0]):
                    h2 = custom[0]
                    slope = slope2 * 2
                    h1 = slope * ((1 - custom[2]) / 2) + custom[1]

            if r >= custom[2]:
                h = h1
            else:
                h = h2
            v = ((1 - t) ** 2) * p1 + (2 * t * (1 - t)) * h + (t ** 2) * p2
        return v

    elif shape == 10:
        return 0.5 + 0.5 * (1 - ratio)
