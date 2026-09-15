# 图片来源与权利 / Image provenance and rights

本插件的刀盾小狗形象参考了 [Bilibili 视频 BV1A8w7zCEwm](https://www.bilibili.com/video/BV1A8w7zCEwm/)。动作帧包含依据该参考制作的 AI 衍生图像，以及透明背景处理和逐帧整理；并非全部由本仓库作者原创。演示图片由这些帧合成。0.4.0保留此前 62 帧和图标的原始字节，并增加探头、收回及复用探头末帧的停靠状态。

This character references [Bilibili video BV1A8w7zCEwm](https://www.bilibili.com/video/BV1A8w7zCEwm/). The animation frames include AI-derived imagery based on that reference, with transparency processing and frame preparation. They are not claimed to be wholly original work by this repository's contributors. The preview images are assembled from those frames. Version 0.4.0 preserves the original bytes of the preceding 62 frames and icon, and adds peek, unpeek, and an edge-rest state reusing the final peek frame.

本说明适用于全部 11 个动作目录中的 PNG、`tray.png` 及 `docs/previews/` 下的全部图片。代码的 MIT 许可不适用于这些素材；本仓库不替原素材或角色的权利人授予许可，也不承诺素材可无限制商用。其他用途或再分发应自行确认相关权利。

This notice covers the PNG files in all 11 action directories, `tray.png`, and all images under `docs/previews/`. The code's MIT license does not cover these assets. This repository does not grant rights on behalf of the original material or character owners, or promise unrestricted commercial use. Verify the relevant rights for other uses or redistribution.

新增探头和收回是以已有刀盾形象为参考生成的动作，再经透明背景处理、对齐及体积优化；并非直接使用原视频截帧。上文所说保留的62帧，是此前插件已使用的动作素材，并不指最初从视频提取的帧。

The new peek and unpeek animations were generated from the existing character reference, followed by transparency processing, alignment, and size optimization. They do not directly reuse frames extracted from the video. The retained 62 frames refer to the preceding plugin animations, not the original video extracts.


## 0.5.0 B 版打招呼 / B greeting

B 版由 Seedance 2.0 参考已有刀盾狗形象与用户提供的动作参考生成，导出121帧、24fps。动作参考来自用户提供的动态表情，其原始作者未在本仓库核实；不公开原始参考文件或访问凭据，也不宣称获得其商业授权。本版为对齐身体与容纳挥刀，将其他既有动作统一留白、缩放及压缩，保留动作顺序和时序，图标原样保留。先前0.4.0的逐字节保留说明仅描述该历史版本。

The B greeting was generated with Seedance 2.0 using the existing character and a user-supplied motion reference, then exported as 121 frames at 24 fps. The motion reference was an animated sticker whose original author has not been verified in this repository. The original reference and access credentials are not published, and no commercial license is claimed. Other existing actions receive common padding, scaling and compression to align the body and accommodate the blade, retaining their ordering and timing. The icon is unchanged. The preceding byte-preservation statement describes historical version 0.4.0 only.


## Arrival voice / 入场配音（0.6.0）

普通站定后播放原声两遍，间隔 180 毫秒，再播放原 B 动作。拖动、召回立即停止，探头入场不播。发送端和接收端均需宿主 0.24.0；接收端无需安装刀盾插件。宿主仍通过受邀测试渠道提供。

Normal arrival plays the voice twice with a 180 ms gap, then the unchanged B greeting. Dragging and recalling cancel the voice; edge peek has no voice. Both peers require host 0.24.0. The receiver does not need this plugin installed. Host builds remain invitation-only.

Voice selected by the user: https://www.myinstants.com/en/instant/what-da-dog-doin-35890/ (yt1s_wU4BGgD.mp3), converted to mono PCM16 16 kHz WAV. Audio attribution is separate from the original visual asset license.
