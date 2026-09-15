# 刀盾小狗

[English](README.en.md)

为吐梨邦伙伴换上刀盾小狗形象，提供动作预览和桌面动作播放。换装保留伙伴原有的名字、人设和记忆。

**0.5.0** 将打招呼替换为约 5 秒的 B 版动作。正常串门走到对方旁边、站定后自动播放一次；贴边探头不播放。保留全部 11 个动作状态。

需要 **吐梨邦 0.23.0 或更新的兼容测试版本**，SDK `apiVersion: 1`。宿主目前通过受邀测试渠道提供，本仓库仅分发插件。

## 使用

1. 在宿主的插件市场选择“刀盾小狗”安装。手动安装时，使用本仓库 Release 的 `plugin.zip`。
2. 打开插件面板，选择动作进行预览。安装与预览不会自动改变桌面伙伴。
3. 点击“使用这个形象”换装。关闭面板及重启后会保留已选外观；“恢复原外观”可撤销本插件当前的外观。
4. 选择伙伴动作，点击“让伙伴做动作”；循环动作可用“回到待机”停止。动作请求成功不代表播放已经完成，也不会控制远程访客。

停用或卸载当前使用的素材插件会恢复原伙伴外观。若已切换到另一个外观，本插件不会替你撤销后来选择的外观。插件标识保留为 `sword-shield-pilot`，可与此前同标识的试装版本保持升级连续性。

## 11 个动作状态

共 202 帧 RGBA8 透明 PNG，统一为 320 × 320。除打招呼替换为 B 版外，其余动作保留原顺序、帧数与时序，重新留白并压缩颜色；图片字节不再与 0.4.0 相同。图标保持不变。总图片字节不超过 8 MiB、解码像素不超过 32 Mi。

为给挥刀留出空间，透明画布有所扩大。原来使用默认 100% 尺寸时，改为 **125%（275）** 可保持身体接近原来的大小，再拖动到想要的位置。插件不会自动改变尺寸和位置；其他尺寸按原值 ×1.25 补偿，超过宿主330上限时不能完全补偿。

| 动作 | 帧数 | 帧率 | 桌面播放 |
| --- | ---: | ---: | --- |
| 待机 `idle` | 12 | 8 | 循环 |
| 走路 `walk` | 12 | 12.5 | 循环 |
| 打招呼 `greet` | 121 | 24 | 单次 |
| 说话 `speak` | 6 | 6 | 循环 |
| 睡觉 `sleep` | 6 | 3 | 循环 |
| 醒来 `wake` | 6 | 5.25 | 单次 |
| 被抓起 `drag` | 6 | 5.25 | 循环 |
| 送东西 `send` | 8 | 9 | 循环 |
| 探头 `peek` | 12 | 12 | 单次 |
| 收回 `unpeek` | 12 | 15 | 单次 |
| 贴边停靠 `edgehide` | 1 | 1 | 保持 |

下面的演示及面板预览循环播放，便于查看；桌面中的打招呼、醒来、探头和收回按单次动作处理。探头末帧、停靠画面与收回首帧完全相同，使停靠接缝连续。送东西是抱着物品原地迈步的动作，实际移动、贴边和串门行为由宿主负责。B 版结束仰头吼叫切回待机仍有姿势硬切，深色背景可见少量浅色边缘；其他六帧动作的流畅度仍有限。

在 0.23.1 宿主中，本机贴边会播放探头并停靠，访客离开屏边会播放收回；本机拖离屏边使用现有拖拽动作，不会自动播放收回。两段动作也可从插件面板手动播放。

| 待机 | 走路 |
| --- | --- |
| ![待机](docs/previews/idle.gif) | ![走路](docs/previews/walk.gif) |
| 打招呼 | 说话 |
| ![打招呼](docs/previews/greet.gif) | ![说话](docs/previews/speak.gif) |
| 睡觉 | 醒来 |
| ![睡觉](docs/previews/sleep.gif) | ![醒来](docs/previews/wake.gif) |
| 被抓起 | 送东西 |
| ![被抓起](docs/previews/drag.gif) | ![送东西](docs/previews/send.gif) |
| 探头 | 收回 |
| ![探头](docs/previews/peek.gif) | ![收回](docs/previews/unpeek.gif) |

## 权限与数据

| 权限 | 用途 |
| --- | --- |
| `ui` | 打开、关闭外观预览面板。 |
| `appearance` | 查询当前外观，应用本插件自己的形象，恢复本插件当前占用的外观。 |
| `pet` | 查询当前伙伴实际可用的动作，并请求本机伙伴播放。 |

插件不使用 Node 权限、不包含后台工具入口、不调用外部网络，也不收集账号、聊天、文件或剪贴板内容。构建脚本只在开发和 CI 阶段运行，不会打入插件安装包。

串门期间的素材传输由兼容宿主负责，仅传送经过校验的 PNG 和动画描述；接收方不会执行本插件的面板代码。跨机展示需要双方宿主支持相关协议，素材准备失败时由宿主中止出发并提示失败。

## 构建与验证

仅需 Python 3.9+ 标准库，不安装第三方依赖：

```sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
python3 scripts/build.py
```

也提供 `npm run test:delivery`、`npm run check:public` 和 `npm run build`。输出为 `dist/plugin.zip` 及 `dist/plugin.zip.sha256`；详细范围和发布流程见 [构建说明](docs/BUILD.md)。CI 构建验证不替代兼容宿主上的真实安装、换装与恢复验收。

## 来源与许可

形象参考 [Bilibili 视频 BV1A8w7zCEwm](https://www.bilibili.com/video/BV1A8w7zCEwm/)，动作素材包含 AI 衍生图像；新增探头和收回参考已有刀盾形象生成，并非直接剪辑原视频动作帧。代码采用 MIT 许可；图片不在该许可范围内，也不宣称完全原创或可无限制商用。详见 [图片来源与权利](ASSETS.md) 和 [代码许可](LICENSE)。


## Arrival voice candidate / 入场配音候选（未发布）

Normal arrival plays the selected voice twice (180 ms gap), then the unchanged B greeting. Dragging or recalling cancels the voice. Requires the unreleased host appearance-audio v3 implementation; 0.23.2 and earlier do not support it. No published compatible host version is claimed.

普通站定后原声两遍，间隔 180 毫秒，再播放原 B 动作。拖动、召回立即停止。依赖尚未发布的宿主音频 v3 能力，0.23.2 及以前不支持。当前为本地测试候选，不登记市场。

Voice source selected by the user: https://www.myinstants.com/en/instant/what-da-dog-doin-35890/ (yt1s_wU4BGgD.mp3), converted to mono PCM16 16 kHz WAV. The source page does not establish a redistribution license; public audio distribution requires rights confirmation.
