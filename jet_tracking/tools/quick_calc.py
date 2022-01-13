def skimmer(key, oldlist, checklist):
    skimlist = []
    for i in range(len(checklist[key])):
        if checklist[key][i] == 0:
            skimlist.append(oldlist[i])
    return skimlist


def div_with_try(v1, v2):
    try:
        a = v1 / v2
    except (TypeError, ZeroDivisionError):
        a = 0
    return a
