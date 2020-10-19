# Determine the range of t values along a splines length where child stems are formed
def find_child_points(stemList, numChild):
    numSegs = sum([len(n.spline.bezier_points) - 1 for n in stemList])
    numPerSeg = numChild/numSegs
    numMain = round(numPerSeg*stemList[0].segMax, 0)
    return [(a+1)/(numMain) for a in range(int(numMain))]


def find_child_points2(numChild):
    return [(a+1)/(numChild) for a in range(int(numChild))]


def find_child_points3(stemList, numChild):
    maxSegs = stemList[0].segMax
    segNum = [0] * maxSegs
    for stem in stemList:
        segs = len(stem.spline.bezier_points)-2
        for n in range(0, segs+1):
            segNum[n] += 1
    segNum = segNum[::-1]

    childPoints = []
    for i, s in enumerate(segNum):
        start = i / maxSegs
        end = (i+1) / maxSegs
        numPoints = int(round((numChild / maxSegs) / s ** .5))
        cp = [((a / numPoints) * (end - start) + start) for a in range(numPoints)]
        childPoints.extend(cp)
    return childPoints