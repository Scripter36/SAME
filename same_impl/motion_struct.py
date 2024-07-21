from panda3d.core import LMatrix4f, Vec3


class Joint:
    __slots__ = ['name', 'type', 'parent', 'children', 'channels', 'offset', 'channel_index']

    def __init__(self, name, type, parent=None, children=None, channels=None, offset=Vec3(0, 0, 0)):
        if channels is None:
            channels = []
        if children is None:
            children = []

        self.name = name
        self.type = type
        self.parent = parent
        self.children = []
        self.channels = channels
        self.offset = offset
        self.channel_index = None

        for child in children:
            self.add_child(child)

    def add_child(self, child):
        if child.parent is not None and child in child.parent.children:
            child.parent.children.remove(child)
        child.parent = self
        if child not in self.children:
            self.children.append(child)

    def remove_child(self, child):
        if child in self.children:
            self.children.remove(child)
        child.parent = None

    def clear_children(self):
        for child in self.children:
            child.parent = None
        self.children.clear()

    def traverse_pre_order(self):
        yield self
        for child in self.children:
            yield from child.traverse_pre_order()

    def get_rest_global_position(self):
        if self.parent is None:
            return self.offset
        return self.parent.get_rest_global_position() + self.offset

    def cache_channel_index(self, start_index=0):
        self.channel_index = start_index
        next_index = start_index + len(self.channels)
        for child in self.children:
            next_index = child.cache_channel_index(next_index)

        return next_index

    def get_global_transform(self, motion):
        if self.parent is None:
            return self.get_local_transform(motion)
        return self.get_local_transform(motion) * self.parent.get_global_transform(motion)

    def get_local_transform(self, motion):
        transform = LMatrix4f.ident_mat()

        transform = LMatrix4f.translate_mat(self.offset) * transform
        channel_index = self.channel_index
        for channel in self.channels:
            if channel == 'Xposition':
                transform = LMatrix4f.translate_mat(motion[channel_index], 0, 0) * transform
            elif channel == 'Yposition':
                transform = LMatrix4f.translate_mat(0, motion[channel_index], 0) * transform
            elif channel == 'Zposition':
                transform = LMatrix4f.translate_mat(0, 0, motion[channel_index]) * transform
            elif channel == 'Xrotation':
                transform = LMatrix4f.rotate_mat(motion[channel_index], (1, 0, 0)) * transform
            elif channel == 'Yrotation':
                transform = LMatrix4f.rotate_mat(motion[channel_index], (0, 1, 0)) * transform
            elif channel == 'Zrotation':
                transform = LMatrix4f.rotate_mat(motion[channel_index], (0, 0, 1)) * transform
            channel_index += 1

        return transform


class Motion:
    __slots__ = ['frames', 'frame_time', 'data']

    def __init__(self, frames, frame_time, data):
        self.frames = frames
        self.frame_time = frame_time
        self.data = data
