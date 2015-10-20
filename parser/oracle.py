from action import Action
from ucca import layer1

SHIFT = Action("SHIFT")
REDUCE = Action("REDUCE")
WRAP = Action("WRAP")
FINISH = Action("FINISH")

ROOT_ID = "1.1"  # ID of root node in UCCA passages


class Oracle:
    """
    Oracle to produce gold transition parses given UCCA passages
    To be used for creating training data for a transition-based UCCA parser
    :param passage gold passage to get the correct edges from
    :param compound_swap whether to allow swap actions that move i steps rather than 1
    """
    def __init__(self, passage, compound_swap=False):
        self.nodes_left = {node.ID for node in passage.layer(layer1.LAYER_ID).all} - {ROOT_ID}
        self.edges_left = {edge for node in passage.nodes.values() for edge in node}
        self.swapped = set()
        self.passage = passage
        self.compound_swap = compound_swap

    def get_action(self, state):
        """
        Determine best action according to current state
        :param state: current State of the parser
        :return: best Action to perform
        """
        if not self.edges_left:
            return FINISH
        if state.stack:
            s = self.passage.by_id(state.stack[-1].node_id)
            edges = self.edges_left.intersection(s.incoming + s.outgoing)
            if not edges:
                return REDUCE
            if len(edges) == 1:
                edge = edges.pop()
                if edge.parent.ID == ROOT_ID:
                    self.edges_left.remove(edge)
                    return Action("ROOT", edge.tag, ROOT_ID)
        if not state.buffer:
            self.swapped = set()
            return WRAP
        b = self.passage.by_id(state.buffer[0].node_id)
        for edge in self.edges_left.intersection(b.incoming):
            if edge.parent.ID in self.nodes_left and not edge.attrib.get("remote"):
                self.edges_left.remove(edge)
                self.nodes_left.remove(edge.parent.ID)
                return Action("NODE", edge.tag, edge.parent.ID)
        if state.stack:
            for edge in self.edges_left.intersection(s.outgoing):
                if edge.child.ID == b.ID:
                    self.edges_left.remove(edge)
                    return Action("RIGHT-REMOTE" if edge.attrib.get("remote") else "RIGHT-EDGE",
                                  edge.tag)
                if edge.child.attrib.get("implicit"):
                    self.edges_left.remove(edge)
                    self.nodes_left.remove(edge.child.ID)
                    return Action("IMPLICIT", edge.tag, edge.child.ID)
            for edge in self.edges_left.intersection(b.outgoing):
                if edge.child.ID == s.ID:
                    self.edges_left.remove(edge)
                    return Action("LEFT-REMOTE" if edge.attrib.get("remote") else "LEFT-EDGE",
                                  edge.tag)
            swap_distance = self.check_swap_distance(s, state)
            if swap_distance:
                return Action("SWAP", swap_distance if self.compound_swap else None)
        return SHIFT

    def check_swap_distance(self, s, state):
        """
        Check if a swap is required, and to what distance (how many items to move to buffer)
        :param s: node corresponding to the stack top
        :param state: current State of the parser
        :return: 0 if no swap required, 1 if compound_swap is False, swap distance otherwise
        """
        distance = 0
        while len(state.stack) > distance + 1 and (self.compound_swap or distance < 1):
            s2 = self.passage.by_id(state.stack[-distance-2].node_id)
            pair = frozenset((s, s2))
            if pair in self.swapped:
                break
            children = [edge.child.ID for edge in self.edges_left.intersection(s2.outgoing)]
            parents = [edge.parent.ID for edge in self.edges_left.intersection(s2.incoming)]
            if any(c.node_id in children for c in state.buffer) and not \
                    any(c.node_id in children for c in state.stack) or \
                    any(p.node_id in parents for p in state.stack) and not \
                    any(p.node_id in parents for p in state.buffer) or \
                    any(p.node_id in parents for p in state.buffer) and not \
                    any(p.node_id in parents for p in state.stack):
                self.swapped.add(pair)
                distance += 1
            else:
                break
        return distance

    def str(self, sep):
        return "nodes left: [%s]%sedges left: [%s]" % (" ".join(self.nodes_left), sep,
                                                       " ".join(map(str, self.edges_left)))

    def __str__(self):
        return str(" ")
