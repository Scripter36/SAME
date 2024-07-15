import math

import panda3d
from direct.showbase.DirectObject import DirectObject
from direct.task.Task import Task
from panda3d.core import MouseButton, LRotation


class OrbitControl(DirectObject):
    yaw = 0
    pitch = math.pi / 2
    last_x = -1
    last_y = -1
    speed = 0.1
    distance = 10

    def __init__(self, mouse_watcher_node: panda3d.core.MouseWatcher, camera: panda3d.core.Camera, win: panda3d.core.WindowHandle):
        DirectObject.__init__(self)

        self.mouse_watcher_node = mouse_watcher_node
        self.camera = camera
        self.win = win

        self.camera_center = camera.parent.attach_new_node('camera_center')
        self.camera.reparent_to(self.camera_center)
        self.camera.set_pos(0, 0, self.distance)
        self.camera.look_at(self.camera_center)

        self.add_task(self.spin_camera_task)
        self.accept('wheel_up', self.wheel_up)
        self.accept('wheel_down', self.wheel_down)

    def spin_camera_task(self, task):
        if self.mouse_watcher_node.has_mouse():
            x = self.mouse_watcher_node.get_mouse_x()
            y = self.mouse_watcher_node.get_mouse_y()
            dx = x - self.last_x
            dy = y - self.last_y
            dx = dx * self.win.get_x_size()
            dy = dy * self.win.get_y_size()
            if self.last_x != -1:
                if self.mouse_watcher_node.is_button_down(MouseButton.two()):
                    self.yaw -= dx * self.speed
                    self.pitch += dy * self.speed
                    quat = LRotation((1, 0, 0), self.pitch) * LRotation((0, 1, 0), self.yaw)
                    self.camera_center.set_quat(quat)
                elif self.mouse_watcher_node.is_button_down(MouseButton.one()):
                    self.camera_center.set_pos(self.camera_center, -dx * self.distance / 2, 0, -dy * self.distance / 2)

            self.last_x = x
            self.last_y = y
        return Task.cont

    def wheel_up(self):
        self.distance *= 0.9
        self.camera.set_pos(0, 0, self.distance)

    def wheel_down(self):
        self.distance /= 0.9
        self.camera.set_pos(0, 0, self.distance)
