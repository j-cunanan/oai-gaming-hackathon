from dataclasses import dataclass


@dataclass(frozen=True)
class GameAdapter:
    id: str
    upstream: str
    build: tuple[str, ...]
    launch: tuple[str, ...]
    tests: tuple[str, ...]
    status: str


MINDUSTRY = GameAdapter(
    "mindustry",
    "https://github.com/Anuken/Mindustry.git",
    ("bash", "./gradlew", "desktop:dist", "--no-daemon"),
    ("java", "-Duser.home=/workspace/runtime/profile", "-jar", "desktop/build/libs/Mindustry.jar"),
    ("bash", "./gradlew", "tests:test", "--offline", "--no-daemon"),
    "Desktop Java adapter; each historical commit must be built and checked.",
)
LUANTI = GameAdapter(
    "luanti",
    "https://github.com/luanti-org/luanti.git",
    (
        "bash",
        "-lc",
        "cmake -S . -B build -DRUN_IN_PLACE=TRUE -DENABLE_SOUND=OFF "
        "-DENABLE_GETTEXT=OFF -DENABLE_CURL=OFF && cmake --build build -j2",
    ),
    ("./bin/luanti", "--config", "/workspace/runtime/profile/luanti.conf", "--go"),
    ("./bin/luanti", "--run-unittests"),
    "Experimental adapter; content pack and Irrlicht dependencies may be required.",
)
ADAPTERS = {a.id: a for a in (MINDUSTRY, LUANTI)}
