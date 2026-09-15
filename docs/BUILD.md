# 构建与发布 / Build and release

当前版本为 0.5.0。以下本地命令只验证并构建安装包；GitHub Release 由下述标签发布流程生成，市场条目另行同步。旧版本标签和附件保留供回退。

The current version is 0.5.0. The local commands below only validate and build the archive. The tag workflow publishes GitHub Releases, and market entries are synchronized separately. Earlier tags and assets remain available for rollback.

## 本地验证 / Local checks

Python 3.9+ 标准库即可独立构建。`npm` 仅作为具名命令入口，不安装依赖；插件运行本身不使用 Python 或 Node 权限。

Python 3.9+ and its standard library are sufficient. The npm scripts are optional named entry points and require no package installation. Plugin runtime does not require Python or Node access.

```sh
npm run test:delivery
npm run check:public
npm run build
```

测试覆盖 11 个状态、202 帧与图标的 SHA-256、RGBA8 PNG 格式、原有 8 MiB 字节与 32 Mi 解码像素上限、动作和预览一致性、权限/版本边界、符号链接与损坏文件拒绝、允许列表打包、跨文件时间/权限的重复构建一致性。预算负向测试使用可解码的真实 PNG，分别超过字节或像素限制，不能靠提高预算让新素材通过。

Tests cover 11 states, SHA-256 hashes for all 202 frames and the icon, RGBA8 PNG format, the existing 8 MiB byte and 32 Mi decoded-pixel limits, animation/preview contracts, permissions and versions, symlink/corruption rejection, the archive allowlist, and reproducibility across changed file timestamps and modes. Negative budget checks use real decodable PNGs that exceed the byte or pixel limit separately. New assets must fit the existing budgets.

`tests/accepted-v0.3.1.sha256.json` 保留历史哈希用于溯源。0.5.0明确重新导出公共画布并替换greet，因此旧字节不再作为当前帧验收值；新的 `tests/accepted-v0.5.0.sha256.json` 锁定前八动作的177帧及原图标。`tests/assets.sha256.json` 覆盖当前全部202帧和图标。原预算、接缝、时序、损坏和归档拒绝测试继续保留。

The v0.3.1 hash file is retained as historical provenance. Version 0.5.0 deliberately re-exports the shared canvas and replaces greet, so old bytes are no longer the current-frame acceptance values. `tests/accepted-v0.5.0.sha256.json` freezes 177 frames in the first eight actions plus the original icon; `tests/assets.sha256.json` covers all 202 frames and the icon. Resource, seam, timing, corruption and archive rejection tests remain in place.

探头为 12 帧、12 fps、单次；收回为 12 帧、15 fps、单次；停靠为 1 帧、1 fps、循环。三者使用相同画布，`peek/peek11.png`、`edgehide/edgehide00.png`、`unpeek/unpeek00.png` 必须逐字节一致。接缝负向测试也更新候选哈希，证明其拒绝来自接缝合同而非哈希偶然不符。收回末帧允许透明或只保留细轮廓，不以强制不透明像素覆盖率作为验收条件。

Peek is 12 frames at 12 fps, played once; unpeek is 12 frames at 15 fps, played once; edge rest is one frame at 1 fps, looping. The three states share a canvas size. `peek/peek11.png`, `edgehide/edgehide00.png`, and `unpeek/unpeek00.png` must be byte-identical. Negative seam checks also update the candidate hashes so rejection tests the seam contract itself. The final unpeek frame may be transparent or retain a thin outline; acceptance does not impose a minimum opaque-pixel ratio.

## 安装包内容 / Archive contents

安装包根目录直接放置 `manifest.json`，并仅包含：

- `manifest.json`, `character.json`
- `panel.html`, `panel.css`, `panel.js`, `preview.js`
- `tray.png` 和 11 个动作目录中的 202 张 PNG / the 202 PNG files in the 11 action directories
- `LICENSE`, `ASSETS.md`

文档预览、测试、构建脚本、CI 配置不会打包。ZIP 固定排序、时间戳与文件权限，并使用 STORE 模式；PNG 已压缩，避免依赖不同压缩库版本。`plugin.zip.sha256` 是安装 ZIP 的摘要，与 CI artifact 自身的摘要不同。

Documentation previews, tests, build scripts, and CI configuration are excluded. ZIP entries have fixed ordering, timestamps, and file modes and use STORE compression. PNG data is already compressed; this avoids compression-library variance. `plugin.zip.sha256` hashes the installable ZIP, not the surrounding CI artifact.

## CI 与发布 / CI and release

推送到 `main`、提交 PR 或手动运行会执行验证并构建，上传有效期 7 天的插件构建产物。推送 `v` 加插件版本号的标签（如 `v0.5.0`）时，CI 核对标签与两个元数据版本一致，再由独立发布任务上传 `plugin.zip` 和摘要到 GitHub Release。失败会中止，不覆盖既有 Release 或偷偷移动标签。

Pushes to `main`, pull requests, and manual runs validate and build the plugin, retaining build artifacts for seven days. A pushed version tag such as `v0.5.0` must match both metadata versions. A separate publishing job then attaches `plugin.zip` and its checksum to a GitHub Release. Failure aborts the process; it does not replace existing releases or move tags.

构建任务只有 `contents: read`；仅标签发布任务使用 `contents: write` 和自动生成的 `GITHUB_TOKEN`。仅检出本仓库，所有 Action 固定到完整提交 SHA，不使用个人凭据，不需要其他代码仓库。发布说明只包含插件信息。

The build job has `contents: read`; only the tag publishing job receives `contents: write` and the automatic `GITHUB_TOKEN`. It checks out only this repository, pins Actions to full commit SHAs, requires no personal credentials or other code repository, and generates plugin-only release notes.

市场登记应使用实际 CI Release 附件复算的 SHA-256，并核对版本、最低宿主版本和权限。发布前仍须在兼容宿主进行实际安装与恢复验收；本仓库的独立构建不声称执行了该应用验收。

Market registration must use the hash recomputed from the actual CI Release attachment, with matching version, minimum host version, and permissions. Real install and restore acceptance in a compatible host is still required; this standalone build does not claim to perform it.

官方依据 / Official references: [workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions), [artifact transfer](https://docs.github.com/en/actions/tutorials/store-and-share-data), [GitHub CLI release creation](https://cli.github.com/manual/gh_release_create).
