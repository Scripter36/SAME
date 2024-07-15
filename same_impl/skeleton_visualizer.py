from panda3d.core import Vec3, LRotation, Material


class SkeletonVisualizer:
    def __init__(self, render, loader, hierarchy, joint_radius=0.4, connection_radius=0.2, color=(1, 0, 0, 1)):
        self.render = render
        self.loader = loader
        self.joint_radius = joint_radius
        self.connection_radius = connection_radius
        self.color = color
        self.hierarchy = hierarchy

        self.nodes = {}
        self.skeleton_np = self.create_joint(hierarchy, self.render)
        self.skeleton_np.reparent_to(self.render)
        self.skeleton_np.set_color_scale(self.color)

    def create_joint(self, joint, parent):
        name = joint['name']
        offset = joint['offset']

        joint_np = parent.attach_new_node(name)
        joint_np.set_pos(parent, offset['x'], offset['y'], offset['z'])
        self.nodes[name] = joint_np

        joint_sphere = self.loader.load_model('models/sphere.glb')
        joint_sphere.set_scale(self.joint_radius)
        joint_sphere.reparent_to(joint_np)

        if 'children' in joint:
            for child in joint['children']:
                child_np = self.create_joint(child, joint_np)

                # Draw connection
                offset = child_np.get_pos(joint_np)
                distance = offset.length()
                if distance < 1e-6:
                    continue
                joint_cylinder = self.loader.load_model('models/cylinder.glb')
                joint_cylinder.reparent_to(joint_np)
                joint_cylinder.set_scale(self.connection_radius, self.connection_radius, distance / 2)
                joint_cylinder.set_pos(offset / 2)
                joint_cylinder.look_at(offset)
                joint_cylinder.set_p(joint_cylinder.get_p() + 90)

        return joint_np

    def update_joint(self, motion_data):
        # traverse the hierarchy and update the joint position
        # motion data is sequencial float, use channels to consume the data
        self.update_joint_recursive(self.hierarchy, motion_data)

    def update_joint_recursive(self, joint, motion_data, index=0):
        if 'channels' not in joint:
            return index
        name = joint['name']
        offset = joint['offset']
        channels = joint['channels']
        joint_np = self.nodes[name]

        pos = Vec3(0, 0, 0)
        quat = LRotation()
        for channel in channels:
            if channel == 'Xposition':
                pos.x = motion_data[index]
                index += 1
            elif channel == 'Yposition':
                pos.y = motion_data[index]
                index += 1
            elif channel == 'Zposition':
                pos.z = motion_data[index]
                index += 1
            elif channel == 'Xrotation':
                quat = LRotation((1, 0, 0), motion_data[index]) * quat
                index += 1
            elif channel == 'Yrotation':
                quat = LRotation((0, 1, 0), motion_data[index]) * quat
                index += 1
            elif channel == 'Zrotation':
                quat = LRotation((0, 0, 1), motion_data[index]) * quat
                index += 1

        joint_np.set_quat(quat)
        joint_np.set_pos(pos + Vec3(offset['x'], offset['y'], offset['z']))

        if 'children' in joint:
            for child in joint['children']:
                index = self.update_joint_recursive(child, motion_data, index)

        return index
