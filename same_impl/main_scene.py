import time

import simplepbr
from direct.showbase.ShowBase import ShowBase

from same_impl.motion_database import MotionDatabase
from same_impl.orbit_control import OrbitControl
from same_impl.skeleton_visualizer import SkeletonVisualizer


class MainScene(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        simplepbr.init()

        self.floor = self.loader.load_model('models/grid_floor.glb')
        self.floor.look_at(0, 0, -1)
        self.floor.reparent_to(self.render)

        self.xyz_axis = self.loader.load_model('models/misc/xyzAxis')
        self.xyz_axis.reparent_to(self.render)
        self.xyz_axis.set_pos(0, 0.5, 0)

        self.render.set_shader_auto()

        # Lighting
        # self.sun_light = DirectionalLight('sun_light')
        # # self.sun_light.set_shadow_caster(True, 2048, 2048)
        # self.sun_lnp = self.render.attach_new_node(self.sun_light)
        # self.sun_lnp.set_hpr(0, -30, 0)
        # self.sun_lnp.node().show_frustum()
        # lens = self.sun_light.get_lens()
        # lens.set_film_size(512, 512)
        # lens.set_near_far(-200, 200)
        # self.render.set_light(self.sun_lnp)

        # self.ambient_light = AmbientLight('ambient_light')
        # self.ambient_light.setColor((0.4, 0.4, 0.4, 1))
        # self.ambient_lnp = self.render.attach_new_node(self.ambient_light)
        # # self.render.set_light(self.ambient_lnp)

        # Add Orbit Control
        self.disable_mouse()
        self.orbit_control = OrbitControl(self.mouseWatcherNode, self.camera, self.win)

        # load motions
        self.motion_database = MotionDatabase()
        self.motion_database.load_bvh('data/LocomotionFlat01_000.bvh', 'LocomotionFlat01_000')

        # show skeleton
        skeleton = self.motion_database.get_skeleton('LocomotionFlat01_000')
        motion = self.motion_database.get_motion('LocomotionFlat01_000')
        self.motion = motion
        self.skeleton_visualizer = SkeletonVisualizer(self.render, self.loader, skeleton)
        self.current_frame = 0
        self.skeleton_visualizer.update_joint(motion.data[0])

        for i in range(10):
            variation_name = self.motion_database.add_variation('LocomotionFlat01_000')
            new_skeleton = self.motion_database.get_skeleton(variation_name)
            new_skeleton_visualizer = SkeletonVisualizer(self.render, self.loader, new_skeleton)
            new_skeleton_visualizer.skeleton_np.set_pos(new_skeleton_visualizer.skeleton_np, 0, 0, -10 * i)

        self.start_time = time.time()
        self.taskMgr.add(self.update_frame, 'update_frame')

        self.accept('escape', self.userExit)

        # press q to toggle animation
        self.accept('q', self.toggle_animation)

    def userExit(self):
        self.destroy()

    show_anim = True

    def update_frame(self, task):
        current_time = time.time()
        if self.show_anim:
            self.current_frame = int((current_time - self.start_time) / self.motion.frame_time) % \
                                 self.motion.frames
            self.skeleton_visualizer.update_joint(self.motion.data[self.current_frame])
        else:
            self.skeleton_visualizer.clear_joint_transform()
        return task.cont

    def toggle_animation(self):
        self.show_anim = not self.show_anim
