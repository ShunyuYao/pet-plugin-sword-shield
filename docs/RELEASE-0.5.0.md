# 0.5.0 delivery / 交付记录

## Behavior / 行为
Normal visit arrival plays the B greeting once after docking; edge-peek arrival retains its existing animation and does not play B. All 11 states remain present. Manual greet uses the same B clip. This asset update requires no SDK changes.

正常串门站定后播放B一次，探头入场保持原行为、不播放B；全部11个状态保留，手动打招呼也使用B。不修改SDK。

The previous eight-action local experiment was not the public 0.4.0 baseline. This release starts from public 0.4.0 and retains peek, unpeek, edgehide, their timing, and their identical join frames. The source icon is unchanged. All animation frames receive shared padding and color compression; historical hashes remain in the tree for provenance rather than being claimed as current bytes.

此前八动作本地试验不是公开0.4.0基线。本次从公开0.4.0出发，保留探头、收回、停靠及其时序和相同接缝帧，图标不变。动作帧统一留白和压缩颜色；历史哈希继续保留用于溯源，不再宣称当前字节未变。

## Acceptance / 验证
Standalone delivery: 19 tests cover packaging, fixed resource limits, historical baseline retention, current asset hashes, B timing, edge timing/seams, invalid inputs and public-source boundaries. No limits were raised: 202 frames, 7,496,584 PNG bytes, 20,684,800 decoded pixels; the transport deduplicates the three identical join frames.

独立交付19项测试覆盖打包、固定资源预算、历史记录、当前图片哈希、B时序、贴边时序/接缝、非法输入及公开边界。未提高预算：202帧，PNG共7,496,584字节，解码20,684,800像素；传输对三张相同接缝图去重。

Real host validation passed all 46 checks. It uses the built ZIP with isolated, hidden-before-paint Electron sender and receiver profiles, actual UDP discovery and LAN TCP transfer. The receiver has no plugin installed. Checks cover complete transferred image hashes for all states, post-docking greeting, fixed position, natural idle return, receiver restart, recall during greeting and edge peek without greeting. This is a same-machine two-process test; physical two-machine, public relay and native desktop compositing are not claimed.

真实宿主验证46项全部通过，使用构建ZIP、首绘前隐藏的独立收发配置、真实UDP发现和LAN TCP传输，接收端未安装插件。检查全部动作图片哈希、站定后打招呼、位置保持、回待机、接收端重启、打招呼中召回及探头不打招呼。本轮为同机双进程验证，不声称物理双机、公网中继或原生桌面合成验证。

## Remaining visual limits / 视觉限制
The padded canvas needs manual size compensation (default 100% to 125%) and repositioning. The final upward roar still cuts to idle; some light matte fringe and color compression remain. No automatic size migration is included. Earlier release tags remain available for rollback.

加宽画布需手动补偿尺寸（默认100%改125%）和重新定位。仰头吼叫收尾仍硬切回待机，少量浅边及颜色压缩仍存在。未包含自动尺寸迁移，旧标签保留供回退。
