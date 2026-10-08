(() => {
  const KEY = "sse_human_game_v1";
  const now = new Date(Date.now() + 8 * 60 * 60 * 1000);\n  const todayKey = now.toISOString().slice(0,10);\n  const beforeCutoff = now.getUTCHours() < 9;
  const state = JSON.parse(localStorage.getItem(KEY) || '{"p":3000,"streak":0,"votes":{},"wins":0,"games":0,"nickname":"游客"}');
  if (typeof state.p !== "number") state.p = 3000;
  const root = document.querySelector("[data-human-game]");
  if (!root) return;
  const save = () => localStorage.setItem(KEY, JSON.stringify(state));
  const balance = root.querySelector("[data-balance]");
  const streak = root.querySelector("[data-streak]");
  const result = root.querySelector("[data-result]");
  const buttons = [...root.querySelectorAll("[data-vote]")];
  function render() {\n    const locked = !beforeCutoff;
    balance.textContent = state.p.toLocaleString() + " P";
    streak.textContent = state.streak + " 天";
    const v = state.votes[todayKey];
    buttons.forEach(b => {
      b.disabled = !!v || locked;
      b.classList.toggle("selected", b.dataset.vote === v);
    });
    if (locked && !v) {\n      result.innerHTML = "<b>⏰ 今日投票已截止</b><span>每天 09:00（UTC+8）锁定，等待下一个交易日。</span>";\n    } else if (v) {
      result.innerHTML = '<b>今天已提交：' + (v === "bull" ? "🟢 看多" : "🔴 看空") +
        '</b><span>预测会在下一个交易日收盘后结算。</span>';
    } else {
      result.innerHTML = '<b>今天还没有选择</b><span>选一个方向，先挑战 AI。</span>';
    }
  }
  buttons.forEach(btn => btn.addEventListener("click", () => {
    if (state.votes[todayKey] || !beforeCutoff) return;
    const vote = btn.dataset.vote;
    state.votes[todayKey] = vote;
    state.games += 1;
    state.p = Math.max(0, state.p - 100);
    save();
    render();
    root.classList.add("celebrate");
    setTimeout(() => root.classList.remove("celebrate"), 700);
  }));
  const login = root.querySelector("[data-login]");
  if (login) login.addEventListener("click", () => {
    alert("先体验、后注册。正式版会接入 Google 登录，并把 P币、预测记录和排行榜保存到云端。");
  });
  render();
})();