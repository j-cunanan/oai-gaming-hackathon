"""A tiny first-person Panda3D room with an intentionally seeded save/load defect.

Movement is stepped at 60 Hz and pauses between actions. The model receives only
rendered images, never these world coordinates or the evaluator's private state.
"""

import math
from dataclasses import asdict, dataclass
from pathlib import Path

from repro.models import Action


@dataclass
class World:
    x: float = 0
    y: float = 1.5
    heading: float = 0
    pitch: float = 0
    collected: bool = False
    inventory: int = 0
    saved: dict | None = None
    collected_before_save: bool = False
    reloaded_after_collection: bool = False
    feedback: str = "Find the blue crystal beyond the partition."
    collisions: int = 0

    def snapshot(self):
        return asdict(self)

    def can_collect(self):
        angle = math.atan2(-(0 - self.x), 9 - self.y)
        relative = (math.degrees(angle) - self.heading + 180) % 360 - 180
        return math.hypot(self.x, self.y - 9) < 2.3 and abs(relative) < 45

    def apply(self, action: Action, *, fixed: bool):
        if action.action == "wait":
            return
        if action.action != "keypress":
            raise ValueError("This synthetic adapter supports keypress and wait only.")
        keys = set(action.keys)
        if keys - {"w", "a", "s", "d", "left", "right", "up", "down", "e", "f5", "f9"}:
            raise ValueError("Use the keys documented in the scene controls.")
        if action.hold_seconds > 2:
            raise ValueError("Each held input is limited to two seconds.")
        if keys & {"e", "f5", "f9"} and len(keys) != 1:
            raise ValueError("Interaction, save and reload must be separate actions.")
        if "e" in keys:
            if self.can_collect() and not self.collected:
                self.collected = True
                self.inventory += 1
                self.feedback = "Crystal collected."
            else:
                self.feedback = "No collectible in reach. Move closer and face it."
        elif "f5" in keys:
            self.saved = {"inventory": self.inventory}
            if fixed:
                self.saved["collected"] = self.collected
            self.collected_before_save = self.collected and self.inventory > 0
            self.feedback = "Room saved."
        elif "f9" in keys:
            if self.saved is None:
                self.feedback = "No save exists."
            else:
                self.inventory = self.saved["inventory"]
                self.collected = self.saved.get("collected", False)
                self.reloaded_after_collection = self.collected_before_save
                self.feedback = "Room reloaded."
        else:
            steps = max(1, round((action.hold_seconds or 0.1) * 60))
            collided = False
            for _ in range(steps):
                self.heading += (int("left" in keys) - int("right" in keys)) * 75 / 60
                self.pitch = max(
                    -45, min(45, self.pitch + (int("up" in keys) - int("down" in keys)) * 35 / 60)
                )
                h = math.radians(self.heading)
                f = int("w" in keys) - int("s" in keys)
                r = int("d" in keys) - int("a" in keys)
                norm = max(1, math.hypot(f, r))
                dx = (-math.sin(h) * f + math.cos(h) * r) * 2.4 / 60 / norm
                dy = (math.cos(h) * f + math.sin(h) * r) * 2.4 / 60 / norm
                nx, ny = self.x + dx, self.y + dy
                blocked = not (-5.65 < nx < 5.65 and 0.35 < ny < 13.65)
                blocked |= -2.35 < nx < 2.35 and 5.15 < ny < 6.45
                if blocked:
                    collided = True
                else:
                    self.x, self.y = nx, ny
            if collided:
                self.collisions += 1
            self.feedback = "Movement blocked by a wall." if collided else ""

    @property
    def reproduced(self):
        return self.reloaded_after_collection and self.inventory == 1 and not self.collected

    @property
    def correct_after_reload(self):
        return self.reloaded_after_collection and self.inventory == 1 and self.collected


class Scene:
    def __init__(self):
        from panda3d.core import loadPrcFileData

        loadPrcFileData(
            "",
            "window-type offscreen\nwin-size 1280 720\naudio-library-name null\nsync-video false\nnotify-level error\n",
        )
        from direct.gui.OnscreenText import OnscreenText
        from direct.showbase.ShowBase import ShowBase
        from panda3d.core import TextNode

        self.base = ShowBase(windowType="offscreen")
        self.base.disableMouse()
        self.base.setBackgroundColor(0.075, 0.08, 0.12)
        self.base.camLens.setFov(76)
        self.base.camLens.setNearFar(0.05, 80)
        for x in range(-6, 6):
            for y in range(14):
                color = (0.22, 0.25, 0.30) if (x + y) % 2 else (0.27, 0.30, 0.35)
                self.box((x + 0.5, y + 0.5, -0.06), (0.98, 0.98, 0.1), color)
        for center, size in [
            ((-6.1, 7, 1.8), (0.2, 14, 3.6)),
            ((6.1, 7, 1.8), (0.2, 14, 3.6)),
            ((0, 14.1, 1.8), (12, 0.2, 3.6)),
            ((0, -0.1, 1.8), (12, 0.2, 3.6)),
        ]:
            self.box(center, size, (0.30, 0.34, 0.43))
        self.box((0, 5.8, 1.35), (4, 0.6, 2.7), (0.37, 0.27, 0.48))
        self.box((0, 9, 0.18), (1.4, 1.4, 0.35), (0.15, 0.18, 0.24))
        self.crystal = self.box((0, 9, 1.15), (0.75, 0.75, 0.95), (0.10, 0.68, 1))
        self.crystal.setH(35)
        self.label("STORAGE", (0, 5.48, 2.1), 0.28)
        self.label("BLUE CRYSTAL", (0, 13.96, 2.7), 0.4)
        # World-space markings provide visual landmarks, without giving the model coordinates.
        self.box((-4.5, 10, 0.6), (1.1, 1.1, 1.2), (0.75, 0.43, 0.2))
        self.box((4.5, 11, 0.85), (1.1, 1.1, 1.7), (0.28, 0.55, 0.38))
        common = {
            "align": TextNode.ALeft,
            "mayChange": True,
            "fg": (0.90, 0.90, 0.98, 1),
            "shadow": (0, 0, 0, 0.9),
            "shadowOffset": (0.035, 0.035),
        }
        self.title = OnscreenText(
            text="REPRO / SYNTHETIC 3D LAB", pos=(-1.70, 0.90), scale=0.06, **common
        )
        self.inventory = OnscreenText(text="", pos=(-1.70, 0.80), scale=0.045, **common)
        self.feedback = OnscreenText(text="", pos=(-1.70, -0.77), scale=0.048, **common)
        self.controls = OnscreenText(
            text="WASD move | Arrows look | E collect | F5 save | F9 reload",
            pos=(-1.70, -0.91),
            scale=0.045,
            **common,
        )
        self.hint = OnscreenText(text="", pos=(-0.25, -0.18), scale=0.045, **common)
        OnscreenText(text="+", pos=(0, -0.015), scale=0.055, fg=(1, 1, 1, 0.8))

    def label(self, text, pos, scale):
        from panda3d.core import TextNode

        node = TextNode(text)
        node.setText(text)
        node.setAlign(TextNode.ACenter)
        node.setTextColor(0.9, 0.84, 1, 1)
        label = self.base.render.attachNewNode(node)
        label.setPos(*pos)
        label.setScale(scale)

    def box(self, center, size, color):
        from panda3d.core import (
            Geom,
            GeomNode,
            GeomTriangles,
            GeomVertexData,
            GeomVertexFormat,
            GeomVertexWriter,
        )

        data = GeomVertexData("box", GeomVertexFormat.getV3c4(), Geom.UHStatic)
        vertex, paint = GeomVertexWriter(data, "vertex"), GeomVertexWriter(data, "color")
        faces = [
            ([(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], 0.83),
            ([(1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)], 0.75),
            ([(-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)], 0.70),
            ([(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], 0.95),
            ([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], 1.0),
            ([(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)], 0.60),
        ]
        triangles = GeomTriangles(Geom.UHStatic)
        for face, (points, shade) in enumerate(faces):
            for point in points:
                vertex.addData3(*[point[i] * size[i] / 2 for i in range(3)])
                paint.addData4(*[v * shade for v in color], 1)
            offset = face * 4
            triangles.addVertices(offset, offset + 1, offset + 2)
            triangles.addVertices(offset, offset + 2, offset + 3)
        geom = Geom(data)
        geom.addPrimitive(triangles)
        node = GeomNode("box")
        node.addGeom(geom)
        path = self.base.render.attachNewNode(node)
        path.setPos(*center)
        path.setTwoSided(True)
        return path

    def capture(self, world: World, destination: Path):
        from panda3d.core import Filename, PNMImage

        self.base.camera.setPos(world.x, world.y, 1.6)
        self.base.camera.setHpr(world.heading, world.pitch, 0)
        self.crystal.hide() if world.collected else self.crystal.show()
        self.inventory.setText(f"Inventory: {world.inventory} crystal(s)")
        self.feedback.setText(world.feedback)
        self.hint.setText("E: collect" if world.can_collect() and not world.collected else "")
        self.base.graphicsEngine.renderFrame()
        self.base.graphicsEngine.renderFrame()
        image = PNMImage()
        if not self.base.win.getScreenshot(image):
            raise RuntimeError("3D screenshot failed")
        if not image.write(Filename.fromOsSpecific(str(destination))):
            raise RuntimeError("3D screenshot write failed")

    def close(self):
        self.base.destroy()
