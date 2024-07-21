import numpy as np
from lark import Lark, Transformer
from panda3d.core import Vec3

from same_impl.motion_struct import Joint, Motion

grammar = '''
%import common.LETTER
%import common.DIGIT
%import common.SIGNED_NUMBER -> NUMBER
%import common.INT
%import common.WS
%ignore WS

CHANNEL: "Xposition" | "Yposition" | "Zposition" | "Xrotation" | "Yrotation" | "Zrotation"
NAME: ("_"|LETTER) ("_"|LETTER|DIGIT|":")*

channels: "CHANNELS" INT (CHANNEL)+
offset: "OFFSET" NUMBER NUMBER NUMBER

start: "HIERARCHY" root "MOTION" motion
root: "ROOT" NAME "{" offset channels (joint | end_joint)+ "}"
joint: "JOINT" NAME "{" offset channels (joint | end_joint)+ "}"
end_joint: "End" "Site" "{" offset "}"
motion: "Frames:" INT "Frame Time:" NUMBER data
data: (NUMBER)+
'''


class BVHParser(Transformer):
    def start(self, children):
        return children[0], children[1]

    def root(self, children):
        return Joint(
            name=children[0],
            offset=children[1],
            channels=children[2],
            children=children[3:],
            type='root'
        )

    def joint(self, children):
        return Joint(
            name=children[0],
            offset=children[1],
            channels=children[2],
            children=children[3:],
            type='joint'
        )

    def end_joint(self, children):
        return Joint(
            name='end',
            offset=children[0],
            channels=[],
            children=[],
            type='end'
        )

    def offset(self, children):
        return Vec3(children[0], children[1], children[2])

    def channels(self, children):
        return children[1:]

    def motion(self, children):
        return Motion(frames=children[0], frame_time=children[1], data=children[2])

    def data(self, children):
        return children

    def NUMBER(self, token):
        return float(token)

    def INT(self, token):
        return int(token)

    def NAME(self, token):
        return token.value

    def CHANNEL(self, token):
        return token.value


def parse_bvh(file_path) -> (Joint, Motion):
    # read and parse the bvh file
    with open(file_path) as file:
        bvh = file.read()
    parser = Lark(grammar, parser='lalr', transformer=BVHParser())

    skeleton: Joint
    motion: Motion
    skeleton, motion = parser.parse(bvh)
    skeleton.cache_channel_index()

    # reshape motion data
    total_channels = 0
    for node in skeleton.traverse_pre_order():
        total_channels += len(node.channels)
    assert total_channels * motion.frames == len(motion.data), \
        f"Total channels {total_channels} and frame {motion.frames} does not match motion data {len(motion.data)}"

    motion.data = np.array(motion.data).reshape(motion.frames, total_channels)

    return skeleton, motion
