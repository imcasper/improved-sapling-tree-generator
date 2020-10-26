shapeList = [('0', 'Conical (0)', 'Shape = 0'),
             ('1', 'Spherical (1)', 'Shape = 1'),
             ('2', 'Hemispherical (2)', 'Shape = 2'),
             ('3', 'Cylindrical (3)', 'Shape = 3'),
             ('4', 'Tapered Cylindrical (4)', 'Shape = 4'),
             ('5', 'Flame (5)', 'Shape = 5'),
             ('6', 'Inverse Conical (6)', 'Shape = 6'),
             ('7', 'Tend Flame (7)', 'Shape = 7')]

shapeList3 = [('0', 'Conical', ''),
              ('6', 'Inverse Conical', ''),
              ('1', 'Spherical', ''),#
              ('2', 'Hemispherical', ''),#
              ('3', 'Cylindrical', ''),
              ('4', 'Tapered Cylindrical', ''),
              ('10', 'Inverse Tapered Cylindrical', ''),
              ('5', 'Flame', ''),#
              ('7', 'Tend Flame', ''),
              ('8', 'Custom Shape', '')]

shapeList4 = [('0', 'Conical', ''),
              ('6', 'Inverse Conical', ''),
              ('1', 'Spherical', ''),
              ('2', 'Hemispherical', ''),
              ('3', 'Cylindrical', ''),
              ('4', 'Tapered Cylindrical', ''),
              ('10', 'Inverse Tapered Cylindrical', ''),
              ('5', 'Flame', ''),
              ('7', 'Tend Flame', '')]

leaftypes = [('0', 'Rotated Alternate', 'leaves rotate around the stem and face upwards'),
             ('1', 'Rotated Opposite', 'pairs of leaves rotate around the stem and face upwards'),
             ('2', 'Alternate', 'leaves sprout alternately from each side of the stem, uses rotate angle'),
             ('3', 'Opposite', 'pairs of leaves sprout from opposite sides of stem, uses rotate angle'),
             ('4', 'Palmately Compound', 'multiple leaves radiating from stem tip, uses rotate angle for spread angle'),
             ('5', 'Radial', 'leaves rotate around the stem (for needles)')]

leafShapes = [('hex', 'Hexagonal', '0'),
              ('rect', 'Rectangular', '1'),
              ('dFace', 'DupliFaces', '2'),
              ('dVert', 'DupliVerts', '3')]

# leafShapes = [('6', 'Hexagonal', '0'),
#               ('4', 'Rectangular', '1'),
#               ('4', 'DupliFaces', '2'),
#               ('1', 'DupliVerts', '3')]

axes = [("+0", "X", ""),
        ("+1", "Y", ""),
        ("+2", "Z", ""),
        ("-0", "-X", ""),
        ("-1", "-Y", ""),
        ("-2", "-Z", "")]

handleList = [('0', 'Auto', 'Auto'),
              ('1', 'Vector', 'Vector')]

settings = [('0', 'Geometry', 'Geometry'),
            ('1', 'Branch Radius', 'Branch Radius'),
            ('2', 'Branch Splitting', 'Branch Splitting'),
            ('3', 'Branch Growth', 'Branch Growth'),
            ('5', 'Leaves', 'Leaves'),
            ('6', 'Armature', 'Armature')]

branchmodes = [("original", "Original", "rotate around each branch"),
               ("rotate", "Rotate", "evenly distribute  branches to point outward from center of tree"),
               ("distance", "Distance", "remove overlapping branches")]

attachmenttypes = [('0', 'Alternate', ''),
                   ('1', 'Opposite', '')]
