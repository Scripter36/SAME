import numpy as np
from lark import Lark, Transformer

grammar = '''
%import common.CNAME -> NAME
%import common.SIGNED_FLOAT -> FLOAT
%import common.INT
%import common.WS
%ignore WS
CHANNEL: "Xposition" | "Yposition" | "Zposition" | "Xrotation" | "Yrotation" | "Zrotation"

channels: "CHANNELS" INT (CHANNEL)+
offset: "OFFSET" FLOAT FLOAT FLOAT

start: "HIERARCHY" root "MOTION" motion
root: "ROOT" NAME "{" offset channels (joint | end_joint)+ "}"
joint: "JOINT" NAME "{" offset channels (joint | end_joint)+ "}"
end_joint: "End" "Site" "{" offset "}"
motion: "Frames:" INT "Frame Time:" FLOAT data
data: (FLOAT)+
'''


class BVHParser(Transformer):
    def start(self, children):
        return {
            'hierarchy': children[0],
            'motion': children[1]
        }

    def root(self, children):
        return {
            'name': children[0],
            'offset': children[1],
            'channels': children[2],
            'children': children[3:]
        }

    def joint(self, children):
        return {
            'name': children[0],
            'offset': children[1],
            'channels': children[2],
            'children': children[3:]
        }

    def end_joint(self, children):
        return {
            'name': 'end',
            'offset': children[0]
        }

    def offset(self, children):
        return {
            'x': children[0],
            'y': children[1],
            'z': children[2]
        }

    def channels(self, children):
        return children[1:]

    def motion(self, children):
        return {
            'frames': children[0],
            'frame_time': children[1],
            'data': children[2]
        }

    def data(self, children):
        return children

    def FLOAT(self, token):
        return float(token)

    def INT(self, token):
        return int(token)

    def NAME(self, token):
        return token.value

    def CHANNEL(self, token):
        return token.value


def calc_total_channels(hierarchy):
    total_channels = len(hierarchy['channels']) if 'channels' in hierarchy else 0
    if 'children' in hierarchy:
        for child in hierarchy['children']:
            total_channels += calc_total_channels(child)
    return total_channels


def parse_bvh(file_path):
    with open(file_path) as file:
        bvh = file.read()
    parser = Lark(grammar, parser='lalr', transformer=BVHParser())
    result = parser.parse(bvh)

    total_channels = calc_total_channels(result['hierarchy'])
    assert total_channels * result['motion']['frames'] == len(result['motion']['data']), \
        f"Total channels {total_channels} does not match motion data {len(result['motion']['data'])} and frames {result['motion']['frames']}"

    result['motion']['data'] = np.array(result['motion']['data']).reshape(result['motion']['frames'], total_channels)

    return result
