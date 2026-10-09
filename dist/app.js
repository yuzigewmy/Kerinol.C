'use strict';
(() => {
  const form = document.getElementById('command-form');
  const input = document.getElementById('command-input');
  const output = document.getElementById('terminal-output');
  const terminal = document.getElementById('terminal');
  const artworks = document.querySelectorAll('[data-animated]');
  const motionButton = document.getElementById('motion-toggle');
  const effectsButton = document.getElementById('effects-toggle');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const commands = {
    help: '可用命令：\n  about / whoami   关于 Kerinol.C\n  projects         查看公开项目\n  github           GitHub 地址\n  neofetch         回到头像终端\n  clear            清空输出',
    about: 'Kerinol.C / @yuzigewmy\n把想法写成代码。Build. Learn. Repeat.\nwhile (true) { keep_building(); }',
    whoami: 'Kerinol.C\nGitHub: @yuzigewmy',
    projects: 'Kerinol.C     · 个人终端与 Profile\ncyber_agent   · 网络安全 Agent\ntinycoder     · 终端 AI 编程 Agent\nall-in-rag    · RAG 技术指南（Fork）\n↓ 项目详情已列在页面下方。',
    github: 'https://github.com/yuzigewmy\n可通过顶部 GitHub 链接访问。'
  };
  function append(text, className) {
    const line = document.createElement('p');
    line.textContent = text;
    if (className) line.className = className;
    output.appendChild(line);
    while (output.children.length > 14) output.firstElementChild.remove();
    output.scrollTop = output.scrollHeight;
  }
  function run(raw) {
    const command = raw.trim();
    if (!command) return;
    const key = command.toLowerCase();
    if (key === 'clear' || key === 'neofetch') {
      output.replaceChildren();
    } else {
      append('guest@kerinol:~$ ' + command, 'output-command');
      append(Object.prototype.hasOwnProperty.call(commands, key) ? commands[key] : '未找到命令：' + command + '\n输入 help 查看可用命令。');
    }
    input.value = '';
  }
  form.addEventListener('submit', event => {
    event.preventDefault();
    run(input.value);
  });
  document.querySelectorAll('[data-command]').forEach(button => {
    button.addEventListener('click', () => {
      run(button.dataset.command);
      input.focus({preventScroll: true});
    });
  });
  effectsButton.addEventListener('click', () => {
    const effectsOn = terminal.classList.toggle('effects-off') === false;
    effectsButton.setAttribute('aria-pressed', String(effectsOn));
    effectsButton.textContent = '光效：' + (effectsOn ? '开' : '关');
  });
  function setMotion(enabled) {
    artworks.forEach(art => { art.src = enabled ? art.dataset.animated : art.dataset.static; });
    motionButton.setAttribute('aria-pressed', String(enabled));
    motionButton.textContent = '动画：' + (enabled ? '开' : '关');
  }
  setMotion(!reducedMotion.matches);
  motionButton.addEventListener('click', () => setMotion(motionButton.getAttribute('aria-pressed') !== 'true'));
  reducedMotion.addEventListener('change', event => setMotion(!event.matches));
  document.getElementById('current-year').textContent = new Date().getFullYear();
})();
