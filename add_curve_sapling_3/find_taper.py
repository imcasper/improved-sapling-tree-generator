from .shape_ratio import shape_ratio
from .TreeSettings import TreeSettings


# calculate taper automatically
def find_taper(tree_settings: TreeSettings):
    taper_s = []
    for i, t in enumerate(tree_settings.length):
        if i == 0:
            shp = 1.0
        elif i == 1:
            shp = shape_ratio(tree_settings.shape, 0, custom=tree_settings.customShape)
        else:
            shp = shape_ratio(tree_settings.shapeS, 0)
        t = t * shp
        taper_s.append(t)

    taper_p = []
    for i, t in enumerate(taper_s):
        pm = 1
        for x in range(i+1):
            pm *= taper_s[x]
        taper_p.append(pm)

    taper_r = []
    for i, t in enumerate(taper_p):
        t = sum(taper_p[i:tree_settings.levels])
        taper_r.append(t)

    taper_t = []
    for i, t in enumerate(taper_r):
        try:
            t = taper_p[i] / taper_r[i]
        except ZeroDivisionError:
            t = 1.0
        taper_t.append(t)

    taper_t = [t * tree_settings.taper[i] for i, t in enumerate(taper_t)]

    return taper_t
