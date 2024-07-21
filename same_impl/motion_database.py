import copy
import random
from math import floor
from typing import Dict

from panda3d.core import Vec3

from same_impl.bvh_parser import parse_bvh
from same_impl.motion_struct import Joint, Motion


class MotionDatabase:
    def __init__(self):
        self.skeletons: Dict[str, Joint] = {}
        self.motions: Dict[Joint, Motion] = {}

        self.spine_add_prob = 0.2
        self.spine_remove_prob = 0.2
        self.neck_add_prob = 0.2
        self.neck_remove_prob = 0.2
        self.hip_add_prob = 0.2
        self.shoulder_add_prob = 0.2
        self.end_zero_prob = 0.3
        self.scale_sigma = 0.3

    def load_bvh(self, path, name):
        skeleton, motion = parse_bvh(path)
        self.skeletons[name] = skeleton
        self.motions[skeleton] = motion
        self.correct_skeleton_height(name)

    def get_skeleton(self, name):
        return self.skeletons[name]

    def get_motion(self, name):
        return self.motions[self.skeletons[name]]

    def correct_skeleton_height(self, name):
        skeleton = self.skeletons[name]

        # Adjust height of the skeleton to the ground
        min_y = float('inf')
        for node in skeleton.traverse_pre_order():
            min_y = min(min_y, node.get_rest_global_position()[1])
        skeleton.offset = Vec3(skeleton.offset[0], skeleton.offset[1] - min_y, skeleton.offset[2])

        if skeleton in self.motions:
            motion = self.motions[skeleton]
            # Adjust height of the motion to the ground
            min_y_motion = float('inf')
            for i in range(motion.frames):
                for node in skeleton.traverse_pre_order():
                    min_y_motion = min(min_y_motion, node.get_global_transform(motion.data[i]).get_cell(3, 1))

            channel_index = 0
            for channel in skeleton.channels:
                if channel == 'Yposition':
                    break
                channel_index += 1

            for i in range(motion.frames):
                motion.data[i][channel_index] -= min_y_motion

    def find_variation_name(self, name, recursion=0):
        if name not in self.skeletons:
            return name
        return self.find_variation_name(f'{name}_variation_{recursion}', recursion + 1)

    def traverse_skeleton_with_depth(self, skeleton, depth=0):
        if 'augmented' not in skeleton.name.lower():
            yield skeleton, depth
        for child in skeleton.children:
            if 'augmented' in child.name.lower():
                yield from self.traverse_skeleton_with_depth(child, depth)
            else:
                yield from self.traverse_skeleton_with_depth(child, depth + 1)

    def add_variation(self, name, new_name=None):
        if new_name is None:
            new_name = self.find_variation_name(name)

        new_skeleton = copy.deepcopy(self.skeletons[name])
        random_seed = random.randint(0, 1000000)
        for joint, depth in self.traverse_skeleton_with_depth(new_skeleton):
            # to make the result symmetric
            random.seed(random_seed + depth)
            rand = random.random()
            name = joint.name.lower()
            # if joint is spine or neck, randomly add or remove joints
            if 'spine' in name or 'neck' in name:
                add_prob = self.spine_add_prob if 'spine' in name else self.neck_add_prob
                remove_prob = self.spine_remove_prob if 'spine' in name else self.neck_remove_prob
                if rand < add_prob:
                    # add joint to center of children
                    offset = sum([child.offset for child in joint.children], Vec3(0, 0, 0)) / len(joint.children)
                    new_joint = Joint(name + '_augmented', joint.type, joint.parent, copy.copy(joint.children), [], offset)
                    new_joint.channel_index = joint.channel_index
                    joint.clear_children()
                    joint.add_child(new_joint)
                elif rand < add_prob + remove_prob:
                    parent = joint.parent
                    parent.remove_child(joint)
                    children = copy.copy(joint.children)
                    for child in children:
                        parent.add_child(child)
            # if joint is hip or shoulder, randomly add dummy joints (end-joints)
            elif 'hip' in name or 'shoulder' in name:
                add_prob = self.hip_add_prob if 'hip' in name else self.shoulder_add_prob
                if rand < add_prob:
                    new_joint = Joint(name + '_augmented', 'end', joint, [], [])
                    # set offset as random value
                    new_joint.offset = Vec3(random.gauss(0, 1), random.gauss(0, 1), random.gauss(0, 1))
                    joint.add_child(new_joint)
            # if joint is end type, randomly set offset to zero
            elif joint.type == 'end':
                if rand < self.end_zero_prob:
                    joint.offset = Vec3(0, 0, 0)
            # randomly scale offset
            joint.offset = joint.offset * random.gauss(1, self.scale_sigma)

        self.skeletons[new_name] = new_skeleton
        self.correct_skeleton_height(new_name)
        return new_name
