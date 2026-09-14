'use strict';
const $ = id => document.getElementById(id);
const data = window.appearancePreview;
const sdk = window.pet?.appearance;
let snapshot, busy = false, ready = false, sequence = 0, stopped = false;
let clipName = 'idle', paused = false, frame = 0, elapsed = 0, previousTime = 0;
const clips = data?.clips || {};
const actionNames = { idle: '待机', walk: '走路', greet: '打招呼', speak: '说话', sleep: '睡觉', wake: '醒来', drag: '被抓起', send: '送东西', unread: '未读提醒', edgehide: '藏在屏边', peek: '探头', unpeek: '收回探头', dropempty: '等待文件', dropfull: '拿着文件' };
let animationKey = '';
const errors = {
  permission_denied: '外观权限未获授权，请在插件管理中检查授权。',
  appearance_unavailable: '这个插件的形象素材不可用，请重新安装。',
  plugin_inactive: '插件已停用，请重新启用。',
  persistence_failed: '保存失败，外观没有更改。请检查磁盘空间后重试。'
};
function errorText(error) {
  const message = String(error?.message || error);
  return Object.entries(errors).find(([code]) => message.includes(code))?.[1] || '操作失败，请刷新状态后重试。';
}
function controls() {
  $('apply').disabled = busy || !ready || !snapshot || snapshot.current.key === snapshot.own.key;
  $('apply').textContent = snapshot?.current.key === snapshot?.own.key && snapshot ? '正在使用' : '使用这个形象';
  $('reset').disabled = busy || !snapshot?.canRestore;
  $('refresh').disabled = busy;
}
function render(state) {
  snapshot = state;
  $('companion').textContent = state.companion.name;
  $('status').textContent = state.current.isDefault ? '正在使用伙伴原外观' : `当前外观：${state.current.name}`;
  controls();
}
async function refresh() {
  if (busy || stopped || !sdk) return;
  const request = ++sequence;
  try {
    const state = await sdk.getState();
    const animations = window.pet.pet.getAnimations ? await window.pet.pet.getAnimations() : null;
    if (request === sequence && !stopped) { render(state); renderAnimations(animations); }
  }
  catch (error) { if (request === sequence && !stopped) { snapshot = null; $('status').textContent = errorText(error); controls(); } }
}
async function mutate(method) {
  if (busy || !sdk || stopped) return;
  busy = true; ++sequence; controls();
  $('notice').textContent = '正在保存…'; $('notice').dataset.error = 'false';
  try {
    const state = await sdk[method]();
    if (stopped) return;
    render(state);
    $('notice').textContent = method === 'apply' ? '已使用这个形象，重启后仍会保留。' : state.canRestore ? '外观状态已刷新。' : state.current.isDefault ? '已恢复伙伴原外观。' : '当前已是其他外观，未作更改。';
  } catch (error) { if (!stopped) { $('notice').textContent = errorText(error); $('notice').dataset.error = 'true'; } }
  finally { busy = false; if (!stopped) { controls(); await refresh(); } }
}
function showFrame() {
  const clip = clips[clipName]; if (!ready || !clip) return;
  $('actor').src = clip.frames[frame]; $('actor').dataset.frame = String(frame); $('actor').dataset.clip = clipName;
}
function choose(name) {
  if (!clips[name]) return;
  clipName = name; frame = 0; elapsed = 0;
  for (const n of ['idle','walk']) $(n).setAttribute('aria-pressed', String(n === name));
  $('timing').textContent = `${clips[name].frames.length} 帧 · ${Math.round(1000 / clips[name].fps)} 毫秒/帧 · 仅在面板预览`;
  showFrame();
  $('preview-action').value = name;
}
function renderAnimations(animations) {
  if (!animations) { $('animation-status').textContent = '这个宿主尚不支持动作查询。'; return; }
  const key = JSON.stringify(animations);
  if (key !== animationKey) {
    const previous = $('animation').value;
    $('animation').value = animations.some(c => c.state === previous) ? previous : animations[0]?.state;
    $('animation').replaceChildren(...animations.map(c => {
      const button = document.createElement('button');
      button.textContent = actionNames[c.state] || c.state; button.dataset.state = c.state;
      button.setAttribute('aria-pressed', String(c.state === $('animation').value));
      button.onclick = () => { $('animation').value = c.state; for (const b of $('animation').children) b.setAttribute('aria-pressed', String(b === button)); };
      return button;
    }));
    animationKey = key;
    $('animation-status').textContent = `当前形象有 ${animations.length} 个动作。单次动作结束后回到待机，循环动作可用右侧按钮停止。`;
  }
  $('play').disabled = animations.length === 0;
  $('stop-animation').disabled = animations.length === 0;
}
async function playAnimation(state) {
  try {
    const sent = await window.pet.pet.playAnim(state);
    $('animation-status').textContent = sent ? `已请求${actionNames[state] || state}，请看桌面上的伙伴。` : '伙伴暂时不可用，请稍后再试。';
  } catch { $('animation-status').textContent = '动作操作失败，请检查插件权限后重试。'; }
}
function tick(now) {
  if (stopped) return;
  const dt = previousTime ? Math.min(now - previousTime, 200) : 0; previousTime = now;
  if (ready && !paused) {
    const clip = clips[clipName]; elapsed += dt;
    const duration = 1000 / clip.fps;
    if (elapsed >= duration) { frame = (frame + Math.floor(elapsed / duration)) % clip.frames.length; elapsed %= duration; showFrame(); }
  }
  requestAnimationFrame(tick);
}
$('apply').onclick = () => mutate('apply'); $('reset').onclick = () => mutate('reset'); $('refresh').onclick = refresh;
$('close').onclick = () => window.pet.ui.closePanel();
$('idle').onclick = () => choose('idle'); $('walk').onclick = () => choose('walk');
$('preview-action').replaceChildren(...Object.keys(clips).map(state => new Option(actionNames[state] || state, state)));
$('preview-action').onchange = () => choose($('preview-action').value);
$('play').onclick = () => playAnimation($('animation').value);
$('stop-animation').onclick = () => playAnimation('idle');
$('pause').onclick = () => { paused = !paused; $('pause').textContent = paused ? '继续' : '暂停'; $('pause').setAttribute('aria-pressed', String(paused)); };
$('name').textContent = data?.name || '形象试用';
$('walk').disabled = !clips.walk;
if (!sdk) $('status').textContent = '当前宿主尚不支持外观插件，请使用支持此功能的测试版本。';
Promise.all(Object.values(clips).flatMap(clip => clip.frames).map(src => { const img = new Image(); img.src = src; return img.decode(); }))
  .then(() => { if (!clips.idle?.frames.length) throw Error('missing idle'); ready = true; choose('idle'); controls(); })
  .catch(() => { $('preview-error').textContent = '素材无法加载，请重新安装形象包。'; ready = false; controls(); });
void refresh(); requestAnimationFrame(tick);
// Only one polling request at a time; unload tears down both polling and animation.
let poll;
async function pollState() { await refresh(); if (!stopped) poll = setTimeout(pollState, 1000); }
poll = setTimeout(pollState, 1000);
window.addEventListener('pagehide', () => { stopped = true; ++sequence; clearTimeout(poll); });
