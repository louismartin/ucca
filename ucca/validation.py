from ucca import layer0, layer1


LINKAGE = (layer1.EdgeTags.LinkArgument, layer1.EdgeTags.LinkRelation)


def validate(passage):
    for node in passage.layer(layer0.LAYER_ID).all:
        if not node.incoming:
            yield "Orphan terminal (%s) '%s'" % (node.ID, node)
        elif len(node.incoming) > 1:
            yield "Reentrant terminal (%s) '%s'" % (join(node.incoming), node)
    stack = [list(passage.layer(layer1.LAYER_ID).heads)]
    for node in stack[-1]:
        if node.ID != "1.1" and node.tag != layer1.NodeTags.Linkage:
            yield "Extra root (%s)" % node.ID
    visited = set()
    path = []
    path_set = set(path)
    while stack:
        for node in stack[-1]:
            if node in path_set:
                yield "Detected cycle (%s)" % "->".join(n.ID for n in path)
            elif node not in visited:
                visited.add(node)
                path.append(node)
                path_set.add(node)
                stack.append(node.children)
                incoming = [e for e in node.incoming if not e.attrib.get("remote") and e.tag not in LINKAGE]
                if len(incoming) > 1:
                    yield "Multiple incoming non-remote (%s)" % join(incoming)
                for edge in node:
                    if (edge.tag == layer1.EdgeTags.Punctuation) != (edge.child.tag == layer1.NodeTags.Punctuation):
                        yield "%s edge (%s) with %s child" % (edge.tag, edge, edge.child.tag)
                    if (node.tag == layer1.NodeTags.Punctuation) != (edge.child.tag == layer0.NodeTags.Punct):
                        yield "%s node (%s) with %s child (%s)" % (node.tag, node.ID, edge.child.tag, edge.child.ID)
                break
        else:
            if path:
                path_set.remove(path.pop())
            stack.pop()


def join(incoming):
    return ", ".join(map(str, incoming))