# 构建与发布 / Build and release

## 本地验证 / Local checks

Python 3.9+ 标准库即可独立构建。`npm` 仅作为具名命令入口，不安装依赖；插件运行本身不使用 Python 或 Node 权限。

Python 3.9+ and its standard library are sufficient. The npm scripts are optional named entry points and require no package installation. Plugin runtime does not require Python or Node access.

```sh
npm run test:delivery
npm run check:public
npm run build
```

测试包括全部 62 帧与图标的冻结 SHA-256、透明 PNG 格式及资源预算、八个动作和预览一致性、权限/版本边界、符号链接与损坏文件拒绝、允许列表打包、跨文件时间/权限的重复构建一致性。`tests/assets.sha256.json` 是已验收素材的逐文件基线，升级素材时须明确评审后更新。

Tests cover frozen SHA-256 hashes for all 62 frames and the icon, PNG format and resource budgets, eight animation/preview contracts, permissions and versions, symlink/corruption rejection, the archive allowlist, and reproducibility across changed file timestamps and modes. Asset updates require explicit review before changing `tests/assets.sha256.json`.

## 安装包内容 / Archive contents

安装包根目录直接放置 `manifest.json`，并仅包含：

- `manifest.json`, `character.json`
- `panel.html`, `panel.css`, `panel.js`, `preview.js`
- `tray.png` 和八个动作目录中的 62 张 PNG / the 62 PNG files in the eight action directories
- `LICENSE`, `ASSETS.md`

文档预览、测试、构建脚本、CI 配置不会打包。ZIP 固定排序、时间戳与文件权限，并使用 STORE 模式；PNG 已压缩，避免依赖不同压缩库版本。`plugin.zip.sha256` 是安装 ZIP 的摘要，与 CI artifact 自身的摘要不同。

Documentation previews, tests, build scripts, and CI configuration are excluded. ZIP entries have fixed ordering, timestamps, and file modes and use STORE compression. PNG data is already compressed; this avoids compression-library variance. `plugin.zip.sha256` hashes the installable ZIP, not the surrounding CI artifact.

## CI 与发布 / CI and release

推送到 `main`、提交 PR 或手动运行会执行验证并构建，上传有效期 7 天的插件构建产物。推送 `v` 加插件版本号的标签（如 `v0.3.1`）时，CI 核对标签与两个元数据版本一致，再由独立发布任务上传 `plugin.zip` 和摘要到 GitHub Release。失败会中止，不覆盖既有 Release 或偷偷移动标签。

Pushes to `main`, pull requests, and manual runs validate and build the plugin, retaining build artifacts for seven days. A pushed version tag such as `v0.3.1` must match both metadata versions. A separate publishing job then attaches `plugin.zip` and its checksum to a GitHub Release. Failure aborts the process; it does not replace existing releases or move tags.

构建任务只有 `contents: read`；仅标签发布任务使用 `contents: write` 和自动生成的 `GITHUB_TOKEN`。仅检出本仓库，所有 Action 固定到完整提交 SHA，不使用个人凭据，不需要其他代码仓库。发布说明只包含插件信息。

The build job has `contents: read`; only the tag publishing job receives `contents: write` and the automatic `GITHUB_TOKEN`. It checks out only this repository, pins Actions to full commit SHAs, requires no personal credentials or other code repository, and generates plugin-only release notes.

市场登记应使用实际 CI Release 附件复算的 SHA-256，并核对版本、最低宿主版本和权限。发布前仍须在兼容宿主进行实际安装与恢复验收；本仓库的独立构建不声称执行了该应用验收。

Market registration must use the hash recomputed from the actual CI Release attachment, with matching version, minimum host version, and permissions. Real install and restore acceptance in a compatible host is still required; this standalone build does not claim to perform it.

官方依据 / Official references: [workflow permissions](https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions), [artifact transfer](https://docs.github.com/en/actions/tutorials/store-and-share-data), [GitHub CLI release creation](https://cli.github.com/manual/gh_release_create).
