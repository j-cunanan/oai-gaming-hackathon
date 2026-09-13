# Third-party inventory

Generated from the installed Python environment and frontend lockfile on 2026-09-14. This lists production and development dependencies together. Preserve each dependency’s actual license notices when distributing binaries; this inventory is not a substitute for those notices.

## External evaluation targets

- **Mindustry:** GPL-3.0, verified in the pinned source checkout’s LICENSE. [Upstream](https://github.com/Anuken/Mindustry). Source, assets and builds are downloaded locally and are not vendored or claimed as REPRO’s work. The runtime screenshots and small source diff in `docs/evidence/MD-001/` document that external game; they are attributed to Mindustry and its contributors.
- **Luanti:** adapter only, not yet validated. [Upstream licensing](https://github.com/luanti-org/luanti/blob/master/LICENSE.txt) contains distinct code and media terms; content packs require separate review. No Luanti content is bundled here.
- **Public player reports:** externally authored evidence; manifests provide source attribution. Attachments are not redistributed by default.

## Python packages

| Package | Version | Declared license |
| --- | --- | --- |
| annotated-doc | 0.0.5 | MIT |
| annotated-types | 0.8.0 | MIT |
| anyio | 4.15.1 | MIT |
| certifi | 2026.7.22 | MPL-2.0 |
| click | 8.5.0 | BSD-3-Clause |
| distro | 1.9.0 | Apache License, Version 2.0 |
| fastapi | 0.141.1 | MIT |
| h11 | 0.16.0 | MIT |
| httpcore | 1.0.9 | BSD-3-Clause |
| httptools | 0.8.0 | MIT |
| httpx | 0.28.1 | BSD-3-Clause |
| idna | 3.19 | BSD-3-Clause |
| iniconfig | 2.3.0 | MIT |
| jiter | 0.17.0 | MIT |
| markdown-it-py | 4.2.0 | See installed distribution metadata |
| mdurl | 0.1.2 | See installed distribution metadata |
| openai | 2.54.0 | Apache-2.0 |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pluggy | 1.6.0 | MIT |
| pydantic | 2.13.5 | MIT |
| pydantic-settings | 2.15.0 | MIT |
| pydantic_core | 2.46.5 | MIT |
| Pygments | 2.21.0 | BSD-2-Clause |
| pytest | 9.1.1 | MIT |
| pytest-asyncio | 1.4.0 | Apache-2.0 |
| python-dotenv | 1.2.3 | BSD-3-Clause |
| python-multipart | 0.0.32 | Apache-2.0 |
| PyYAML | 6.0.3 | MIT |
| rich | 15.0.0 | MIT |
| ruff | 0.16.7 | MIT |
| shellingham | 1.5.4 | ISC License |
| sniffio | 1.3.1 | MIT OR Apache-2.0 |
| starlette | 1.6.0 | BSD-3-Clause |
| tqdm | 4.70.1 | MPL-2.0 AND MIT |
| typer | 0.27.2 | MIT |
| typing-inspection | 0.4.4 | MIT |
| typing_extensions | 4.16.0 | PSF-2.0 |
| uvicorn | 0.52.4 | BSD-3-Clause |
| uvloop | 0.22.1 | MIT License |
| watchfiles | 1.2.0 | MIT |
| websockets | 17.1 | BSD-3-Clause |

## Frontend packages

| Package | Version | Lockfile license |
| --- | --- | --- |
| @babel/code-frame | 7.29.7 | MIT |
| @babel/compat-data | 7.29.7 | MIT |
| @babel/core | 7.29.7 | MIT |
| @babel/generator | 7.29.8 | MIT |
| @babel/helper-compilation-targets | 7.29.7 | MIT |
| @babel/helper-globals | 7.29.7 | MIT |
| @babel/helper-module-imports | 7.29.7 | MIT |
| @babel/helper-module-transforms | 7.29.7 | MIT |
| @babel/helper-plugin-utils | 7.29.7 | MIT |
| @babel/helper-string-parser | 7.29.7 | MIT |
| @babel/helper-validator-identifier | 7.29.7 | MIT |
| @babel/helper-validator-option | 7.29.7 | MIT |
| @babel/helpers | 7.29.7 | MIT |
| @babel/parser | 7.29.8 | MIT |
| @babel/plugin-transform-react-jsx-self | 7.29.7 | MIT |
| @babel/plugin-transform-react-jsx-source | 7.29.7 | MIT |
| @babel/template | 7.29.7 | MIT |
| @babel/traverse | 7.29.8 | MIT |
| @babel/types | 7.29.8 | MIT |
| @esbuild/aix-ppc64 | 0.28.2 | MIT |
| @esbuild/android-arm | 0.28.2 | MIT |
| @esbuild/android-arm64 | 0.28.2 | MIT |
| @esbuild/android-x64 | 0.28.2 | MIT |
| @esbuild/darwin-arm64 | 0.28.2 | MIT |
| @esbuild/darwin-x64 | 0.28.2 | MIT |
| @esbuild/freebsd-arm64 | 0.28.2 | MIT |
| @esbuild/freebsd-x64 | 0.28.2 | MIT |
| @esbuild/linux-arm | 0.28.2 | MIT |
| @esbuild/linux-arm64 | 0.28.2 | MIT |
| @esbuild/linux-ia32 | 0.28.2 | MIT |
| @esbuild/linux-loong64 | 0.28.2 | MIT |
| @esbuild/linux-mips64el | 0.28.2 | MIT |
| @esbuild/linux-ppc64 | 0.28.2 | MIT |
| @esbuild/linux-riscv64 | 0.28.2 | MIT |
| @esbuild/linux-s390x | 0.28.2 | MIT |
| @esbuild/linux-x64 | 0.28.2 | MIT |
| @esbuild/netbsd-arm64 | 0.28.2 | MIT |
| @esbuild/netbsd-x64 | 0.28.2 | MIT |
| @esbuild/openbsd-arm64 | 0.28.2 | MIT |
| @esbuild/openbsd-x64 | 0.28.2 | MIT |
| @esbuild/openharmony-arm64 | 0.28.2 | MIT |
| @esbuild/sunos-x64 | 0.28.2 | MIT |
| @esbuild/win32-arm64 | 0.28.2 | MIT |
| @esbuild/win32-ia32 | 0.28.2 | MIT |
| @esbuild/win32-x64 | 0.28.2 | MIT |
| @jridgewell/gen-mapping | 0.3.13 | MIT |
| @jridgewell/remapping | 2.3.5 | MIT |
| @jridgewell/resolve-uri | 3.1.2 | MIT |
| @jridgewell/sourcemap-codec | 1.6.0 | MIT |
| @jridgewell/trace-mapping | 0.3.31 | MIT |
| @napi-rs/lzma-linux-x64-gnu | 1.5.1 | MIT |
| @rolldown/pluginutils | 1.0.0-rc.3 | MIT |
| @rollup/rollup-android-arm-eabi | 4.63.2 | MIT |
| @rollup/rollup-android-arm64 | 4.63.2 | MIT |
| @rollup/rollup-darwin-arm64 | 4.63.2 | MIT |
| @rollup/rollup-darwin-x64 | 4.63.2 | MIT |
| @rollup/rollup-freebsd-arm64 | 4.63.2 | MIT |
| @rollup/rollup-freebsd-x64 | 4.63.2 | MIT |
| @rollup/rollup-linux-arm-gnueabihf | 4.63.2 | MIT |
| @rollup/rollup-linux-arm-musleabihf | 4.63.2 | MIT |
| @rollup/rollup-linux-arm64-gnu | 4.63.2 | MIT |
| @rollup/rollup-linux-arm64-musl | 4.63.2 | MIT |
| @rollup/rollup-linux-loong64-gnu | 4.63.2 | MIT |
| @rollup/rollup-linux-loong64-musl | 4.63.2 | MIT |
| @rollup/rollup-linux-ppc64-gnu | 4.63.2 | MIT |
| @rollup/rollup-linux-ppc64-musl | 4.63.2 | MIT |
| @rollup/rollup-linux-riscv64-gnu | 4.63.2 | MIT |
| @rollup/rollup-linux-riscv64-musl | 4.63.2 | MIT |
| @rollup/rollup-linux-s390x-gnu | 4.63.2 | MIT |
| @rollup/rollup-linux-x64-gnu | 4.63.2 | MIT |
| @rollup/rollup-linux-x64-musl | 4.63.2 | MIT |
| @rollup/rollup-openbsd-x64 | 4.63.2 | MIT |
| @rollup/rollup-openharmony-arm64 | 4.63.2 | MIT |
| @rollup/rollup-win32-arm64-msvc | 4.63.2 | MIT |
| @rollup/rollup-win32-ia32-msvc | 4.63.2 | MIT |
| @rollup/rollup-win32-x64-gnu | 4.63.2 | MIT |
| @rollup/rollup-win32-x64-msvc | 4.63.2 | MIT |
| @types/babel__core | 7.20.5 | MIT |
| @types/babel__generator | 7.27.0 | MIT |
| @types/babel__template | 7.4.4 | MIT |
| @types/babel__traverse | 7.28.0 | MIT |
| @types/estree | 1.0.9 | MIT |
| @types/react | 19.3.0 | MIT |
| @types/react-dom | 19.3.0 | MIT |
| @vitejs/plugin-react | 5.2.0 | MIT |
| baseline-browser-mapping | 2.11.23 | Apache-2.0 |
| browserslist | 4.28.9 | MIT |
| caniuse-lite | 1.0.30001810 | CC-BY-4.0 |
| convert-source-map | 2.0.0 | MIT |
| csstype | 3.2.3 | MIT |
| debug | 4.4.3 | MIT |
| electron-to-chromium | 1.5.427 | ISC |
| esbuild | 0.28.2 | MIT |
| escalade | 3.2.0 | MIT |
| fdir | 6.5.0 | MIT |
| fsevents | 2.3.3 | MIT |
| gensync | 1.0.0-beta.2 | MIT |
| js-tokens | 4.0.0 | MIT |
| jsesc | 3.1.0 | MIT |
| json5 | 2.2.3 | MIT |
| lru-cache | 5.1.1 | ISC |
| lucide-react | 0.468.0 | ISC |
| ms | 2.1.3 | MIT |
| nanoid | 3.3.19 | MIT |
| node-releases | 2.0.55 | MIT |
| picocolors | 1.1.1 | ISC |
| picomatch | 4.0.7 | MIT |
| postcss | 8.5.28 | MIT |
| prettier | 3.9.6 | MIT |
| react | 19.3.0 | MIT |
| react-dom | 19.3.0 | MIT |
| react-refresh | 0.18.0 | MIT |
| rollup | 4.63.2 | MIT |
| scheduler | 0.28.0 | MIT |
| semver | 6.3.1 | ISC |
| source-map-js | 1.2.1 | BSD-3-Clause |
| tinyglobby | 0.2.17 | MIT |
| typescript | 5.9.3 | Apache-2.0 |
| update-browserslist-db | 1.3.3 | MIT |
| vite | 7.3.6 | MIT |
| yallist | 3.1.1 | ISC |

## Worker image and fonts

The worker uses the official Eclipse Temurin JDK 17 image, Ubuntu packages, Xvfb/Openbox, Mesa, FFmpeg, Git, ripgrep and compiler tools. The image retains OS/package license notices. Python desktop packages are pinned in `infra/docker/Dockerfile`: PyAutoGUI 0.9.54, mss 10.1.0 and Pillow 11.3.0. Audit their distribution metadata and transitive dependencies before redistributing the worker image.

The dashboard requests DM Sans and Space Grotesk through Google Fonts, with system-font fallback. Font files are not vendored; see their upstream Google Fonts license files before self-hosting them.

The OpenAI **Python SDK** is used (Apache-2.0 according to its installed metadata). The OpenAI **Agents SDK** is not currently a dependency; do not list it as an implemented component in the submission.

A license for REPRO’s own original code is a team decision and has not been selected by this inventory.
