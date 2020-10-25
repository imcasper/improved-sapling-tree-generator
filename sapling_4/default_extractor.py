# from .GeometryProperties import GeometryProperties


def default_extractor(prop):
    prop_annot = prop.__getattribute__('__annotations__')

    print("propp_annot: ", prop_annot)
    for entry in prop_annot:
        if not prop.is_property_set(entry):
            print("setting: ", entry)
            prop.__setattr__(entry, prop.__getattribute__(entry))
