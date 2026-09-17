"""Check that the synthetic probe's evaluator distinguishes a defect from setup failure."""

import pytest

from repro.models import Action
from scripts.three_d_probe.scene import World


def press(world, key, *, fixed=False, hold=0):
    world.apply(Action(action="keypress", keys=[key], hold_seconds=hold), fixed=fixed)


def test_frozen_collection_save_reload_distinguishes_seeded_bug_and_reference():
    for fixed in (False, True):
        world = World(y=7.5)
        for key in ("e", "f5", "f9"):
            press(world, key, fixed=fixed)
        assert world.inventory == 1
        assert world.reproduced is (not fixed)
        assert world.correct_after_reload is fixed


def test_save_without_successful_collection_is_not_a_reproduction():
    world = World()
    for key in ("e", "f5", "f9"):
        press(world, key)
    assert not world.reproduced
    assert not world.correct_after_reload


def test_movement_cannot_tunnel_through_partition_and_is_camera_relative():
    world = World()
    press(world, "w", hold=2)
    assert world.y < 5.15
    assert world.collisions == 1
    press(world, "right", hold=1.2)
    x, y = world.x, world.y
    press(world, "w", hold=0.5)
    assert world.x > x + 1
    assert world.y == pytest.approx(y)


def test_unsupported_or_unbounded_controls_do_not_change_world():
    world = World()
    before = world.snapshot()
    for action in (
        Action(action="keypress", keys=["w"], hold_seconds=3),
        Action(action="keypress", keys=["e", "f9"]),
        Action(action="keypress", keys=["escape"]),
    ):
        with pytest.raises(ValueError):
            world.apply(action, fixed=False)
        assert world.snapshot() == before
