from ..predicate import AtomicPredicate, QuantifiedPredicate, BinaryPredicate

OTY = "objectType"
PR = "parentReceptacles"

    
def get_predicates_from(spec):
    preds = []
    res = []
    for key in spec: 
        if key == OTY:
            obj_pred = AtomicPredicate(lhs=OTY, op="==", rhs=spec[OTY])
            preds.append(obj_pred)
        elif key == PR:
            if len(spec[PR])==1:
                preds.append(AtomicPredicate(lhs=PR, op="in", rhs=spec[PR][0]))
        else:
            preds.append(AtomicPredicate(lhs=key, op="==", rhs=spec[key]))
    conjunction_pred = None
    for pred in preds:
        res.append(QuantifiedPredicate(quantifier="exist", predicate = pred))
        if conjunction_pred == None:
            conjunction_pred = pred
        else:
            conjunction_pred = BinaryPredicate(lhs=conjunction_pred, op="and", rhs=pred)
    conjunction_pred= QuantifiedPredicate(quantifier="exist", predicate=conjunction_pred)
    res.append(conjunction_pred)        
    return res
