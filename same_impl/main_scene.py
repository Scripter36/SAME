import time

import simplepbr
from direct.showbase.ShowBase import ShowBase
from panda3d.core import DirectionalLight, AmbientLight, BoundingVolume

from same_impl.bvh_parser import parse_bvh
from same_impl.orbit_control import OrbitControl
from same_impl.skeleton_visualizer import SkeletonVisualizer


class MainScene(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)

        simplepbr.init()

        # Load the environment model.
        # self.scene = self.loader.load_model("models/environment")
        # # Reparent the model to render.
        # self.scene.reparent_to(self.render)
        # # Apply scale and position transforms on the model.
        # self.scene.set_scale(0.25, 0.25, 0.25)
        # self.scene.set_pos(-8, 42, 0)

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

        # show skeleton
        self.bvh_data = parse_bvh('data/LocomotionFlat01_000.bvh')
        self.skeleton_visualizer = SkeletonVisualizer(self.render, self.loader, self.bvh_data['hierarchy'])
        self.current_frame = 0
        self.skeleton_visualizer.update_joint(self.bvh_data['motion']['data'][0])

        self.start_time = time.time()
        self.taskMgr.add(self.update_frame, 'update_frame')

        self.accept('escape', self.userExit)

    def userExit(self):
        self.destroy()

    def update_frame(self, task):
        current_time = time.time()
        self.current_frame = int((current_time - self.start_time) / self.bvh_data['motion']['frame_time']) % self.bvh_data['motion']['frames']
        self.skeleton_visualizer.update_joint(self.bvh_data['motion']['data'][self.current_frame])
        return task.cont
