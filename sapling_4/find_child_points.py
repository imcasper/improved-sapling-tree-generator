
# Determine the range of t values along a splines length where child stems are formed
def find_child_points(stem_list, num_child):
    num_segs = sum([len(n.spline.bezier_points) - 1 for n in stem_list])
    num_per_seg = num_child / num_segs
    num_main = round(num_per_seg * stem_list[0].segMax, 0)
    return [(a+1)/(num_main) for a in range(int(num_main))]


def find_child_points2(num_child):
    return [(a+1) / (num_child) for a in range(int(num_child))]


def find_child_points3(stem_list, num_child, rp=0.5):
    max_segs = stem_list[0].segMax
    seg_num = [0] * max_segs
    for stem in stem_list:
        segs = len(stem.spline.bezier_points)-2
        for n in range(0, segs+1):
            seg_num[n] += 1
    seg_num = seg_num[::-1]

    child_points = []
    for i, s in enumerate(seg_num):
        start = i / max_segs
        end = (i+1) / max_segs
        num_points = int(round((num_child / max_segs) / s ** rp))
        cp = [((a / num_points) * (end - start) + start) for a in range(num_points)]
        child_points.extend(cp)
    return child_points


def find_child_points4(stem_list, num_child):
    max_offset = max([s.offsetLen + (len(s.spline.bezier_points) - 1) * s.segL for s in stem_list])
    stem_lengths = []
    for stem in stem_list:
        stem_len = stem.offsetLen + stem.segL*(len(stem.spline.bezier_points) - 1)
        stem_lengths.append(stem_len / max_offset)

    print(stem_lengths)

    return [(a+1) / (num_child) for a in range(int(num_child))]
