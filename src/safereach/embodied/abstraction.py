
import json
import math
import itertools
from deepdiff import DeepDiff
from ..abstraction import Abstraction, FINISH
from typing import Any, Set, List, Dict
import networkx as nx
import matplotlib.pyplot as plt
from ..predicate import *
from z3 import *

keys_map = {
    "isToggled": "toggleable",
    "isCooked":"cookable",
    "isBroken": "breakable",
    "isFilledWithLiquid": "canFillWithLiquid",
    "isDirty": "dirtyable",
    "isUsedUp" : "canBeUsedUp",
    "isSliced": "sliceable",
    "isOpen": "openable",
    "isPickedUp":"pickupable",
}

# type_profile = {}
# with open("safereach/embodied/meta_data1.json") as f:
#     meta_data = json.loads(f.read())
#     type_profile = meta_data["type_profiles"]
     
class EmbodiedAbstraction(Abstraction):

    # order matters
    def __init__(self, preds):
        self.predicates = preds # [pred for pred in preds if type(pred) == QuantifiedPredicate and pred.quantifier=="exist"]
        self.state_idx = None
        self.state_interpretation = None
     
    def to_json(self): 
        predicates =[pre.dict() for pre in self.predicates]
        return json.dumps(predicates)

    def get_state_idx(self, states) -> Dict[str, int]:
        if self.state_idx == None:
            self.state_idx = {s:i for i, s in enumerate(states)}
        return self.state_idx

    def get_state_interpretation(self, states) -> Dict[str, Any]:
        if self.state_interpretation == None:
            self.state_interpretation = {s: self.decode(s) for s in states}
        return self.state_interpretation

    # In embodied agent, the observation is list of object states
    def encode(self, observations: List[Any]) -> str:
        if observations == FINISH:
            return FINISH
        
        for obs in observations:
            obs["parentReceptacles"] = [pr[:pr.find("|")] for pr in obs["parentReceptacles"] ]\
                if type(obs["parentReceptacles"])==list else obs["parentReceptacles"] 
        bitstr = ""
        # print(observations)
        for pred in self.predicates:
            # assume all predicates are quantified.
            # print(type(pred))
            # print("??")
            # print(pred)
            bitstr = bitstr + ('1' if pred.state_eval(observations) else '0')
            # print(bitstr)
        return bitstr
    
    def decode(self, bitstr: str) -> Any: 
        # pass
        if bitstr == FINISH:
            return FINISH
        # object_states = []
        pairs = [
            (pred.dict(), bit)   # or pred.model_dump() for Pydantic v2
            for pred, bit in zip(self.predicates, bitstr)
        ]
        return pairs
        # for (pred, bit) in zip(self.predicates, bitstr):
        #     if bit == '1':
        #         pred = pred.predicate
        #         obj = construct_obj(pred)
        #         object_states.append(obj)
        #     else:
        #         if pred.state_eval(object_states) == True:
        #             raise Exception("This is not a ")
        # return object_states
   
    # this should return a mask for the 
    # proposition maps from predicate to its bool value (i.e., 1)
    def filter(self, propositions) -> Set[str]:
        pred_idxes = {str(pred):i for i, pred in enumerate(self.predicate)}
        masks = {}
        for (predicate, b_value) in propositions:
            if not str(predicate) in pred_idxes:
                raise Exception("Unknown predicate for the current abstraction")
            pred_i = pred_idxes[str(predicate)]
            masks[pred_i] = '1' if b_value else '0'
            
        states = [bitstr for bitstr in itertools.product('01', repeat=len(self.predicates)) \
            if all(bitstr[idx] == masks[idx] for idx in masks)]
        return set(states)
        
    def valid_trans(self, state1: str, state2: str) -> bool:
        if state1 == FINISH:
            return False

        return True
        # TODO- Engineering the correctness of transition
        observation1 = self.decode(state1)
        observation2 = self.decode(state2)
        # observations are list of object state
        
        diff = DeepDiff(observation1, observation2, ignore_order=True)
        
        # we assume transitions are atomic, (i.e., the )
        if len(diff.keys()) > 1:
            return False
        
        # same state
        if len(diff) == 0 :
            return True
        
        # only one item can be added removed at a time
        if "iterable_item_added" in diff:
            return len(diff["iterable_item_added"]) == 1
        if "iterable_item_removed" in diff:
            return len(diff["iterable_item_removed"]) == 1
        
        if "values_changed" in diff and "['parentReceptacles'][0]" in diff["values_changed"]:
            return False
            
        if len(diff["values_changed"]) >1:
            return False
        
        key_o = list(diff["values_changed"].keys())[0]
        key = key_o[key_o.find("]")+1:] 
        diff["values_changed"][key] =  diff["values_changed"][key_o]
        del diff["values_changed"][key_o]
        
        if "['parentReceptacles'][0]" in diff["values_changed"]: 
            return False
         
        # some property are not recoverable
        if any(f"['{x}']" in diff["values_changed"] and \
                diff["values_changed"][f"['{x}']"]["old_value"] and \
                not diff["values_changed"][f"['{x}']"]["new_value"]   
                for x in ["isBroken", "isSliced", "isCooked"]
                ): 
            return False
        return True
        
    def show_reachability_graph(self):
        state_space = list(self.enumerate_possible_states())
        G = nx.DiGraph()
        
        # Add all states as nodes
        for state in state_space:
            G.add_node(state)

        # Add edges based on reachability
        for i in range(len(state_space)):
            for j in range(len(state_space)): 
                s1, s2 = state_space[i], state_space[j]

                if self.valid_trans(s1, s2):
                    G.add_edge(s1, s2)
    
        print(f"Absorbing states: {find_absorbing_states(G)}")
        # Optional: Print summary
        print(f"Total states: {len(G.nodes)}")
        print(f"Reachable transitions: {len(G.edges)}")

        # Optional: Draw the graph (only for small graphs!)
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=False, node_size=100, arrows=True)
        plt.title("State Transition Graph")
        plt.show()

def process_type_profile():

    with open("safereach/embodied/meta_data.json") as f:
        
        meta_data = json.loads(f.read())
        obj_types = meta_data["obj_types"]
        keyables = [keys_map[k] for k in keys_map]

        type_profiles = {}
        for type in obj_types:
            type_profile = {}
            for k in keyables:
                type_profile[k] = obj_types[type][k]
            type_profiles[type] = type_profile
        
        with open("safereach/embodied/meta_data1.json", 'w') as j:
            del meta_data["obj_types"]
            meta_data["type_profiles"] = type_profiles
            j.write(json.dumps(meta_data))
        
# process_type_profile()

def find_absorbing_states(G):
    absorbing_states = [node for node in G.nodes if G.out_degree(node) == 0]
    return absorbing_states