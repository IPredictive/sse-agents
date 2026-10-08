(() => {
  const SUPABASE_URL = "https://hfdrdxxcaqdknniiypnz.supabase.co";
  const SUPABASE_KEY = "sb_publishable_YLtCCkTOO9KwJKNTyeIMFA_cuEmNG3k";
  const root = document.querySelector("[data-human-game]");
  if (!root || !window.supabase) return;
  const db = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
  const balance = root.querySelector("[data-balance]");
  const streak = root.querySelector("[data-streak]");
  const result = root.querySelector("[data-result]");
  const buttons = [...root.querySelectorAll("[data-vote]")];
  const login = root.querySelector("[data-login]");
  const leaderboard = root.querySelector(".leaderboard");

  function sgNow() { return new Date(Date.now() + 8 * 60 * 60 * 1000); }
  function dateKey(d) { return d.toISOString().slice(0,10); }
  function nextWeekday() {
    const d = sgNow();
    d.setUTCDate(d.getUTCDate() + 1);
    while (d.getUTCDay() === 0 || d.getUTCDay() === 6) d.setUTCDate(d.getUTCDate() + 1);
    return dateKey(d);
  }
  function beforeCutoff(tradingDate) {
    const now = sgNow();
    const today = dateKey(now);
    if (today < tradingDate) return true;
    if (today > tradingDate) return false;
    return now.getUTCHours() < 9;
  }

  async function render() {
    const { data: { user } } = await db.auth.getUser();
    if (!user) {
      balance.textContent = "登录后领取";
      streak.textContent = "—";
      const tradingDate = nextWeekday();
      buttons.forEach(b => b.disabled = !beforeCutoff(tradingDate));
      result.innerHTML = "<b>先免费体验，再保存成绩</b><span>登录 Google 后，自动获得 3,000 P币并加入真实排行榜。</span>";
      return;
    }
    const { data: profile } = await db.from("profiles").select("p_balance,nickname").eq("id", user.id).single();
    const tradingDate = nextWeekday();
    const { data: prediction } = await db.from("predictions").select("direction,status").eq("user_id", user.id).eq("trading_date", tradingDate).maybeSingle();
    balance.textContent = Number(profile?.p_balance || 0).toLocaleString() + " P";
    buttons.forEach(b => { b.disabled = !!prediction || !beforeCutoff(tradingDate); b.classList.toggle("selected", b.dataset.vote === prediction?.direction); });
    if (!beforeCutoff(tradingDate) && !prediction) result.innerHTML = "<b>⏰ 今日投票已截止</b><span>每天 09:00（UTC+8）锁定。</span>";
    else if (prediction) result.innerHTML = "<b>今天已提交：" + (prediction.direction === "bull" ? "🟢 看多" : "🔴 看空") + "</b><span>等待下一交易日收盘结算。</span>";
    else result.innerHTML = "<b>🎯 今天还没有押</b><span>选一个方向，100 P 入场，明天收盘揭晓胜负。</span>";
    await loadLeaderboard(user.id);
  }

  async function loadLeaderboard(me) {
    const { data, error } = await db.rpc("get_leaderboard");
    if (error || !leaderboard) return;
    const rows = (data || []).slice(0, 10).map((x, i) =>
      '<div class="leader-row ' + (x.user_id === me ? 'top' : '') + '"><span>' + ["🥇","🥈","🥉"][i] + '</span><b>' +
      (x.user_id === me ? "你" : (x.nickname || "玩家")) + '</b><small>👤 玩家 · ' + Number(x.accuracy || 0).toFixed(1) +
      '%</small><strong>' + Number(x.p_balance || 0).toLocaleString() + ' P</strong></div>'
    ).join("");
    const old = leaderboard.querySelector(".leader-row");
    if (old) leaderboard.querySelectorAll(".leader-row").forEach(x => x.remove());
    leaderboard.insertAdjacentHTML("beforeend", rows);
  }

  buttons.forEach(btn => btn.addEventListener("click", async () => {
    const tradingDate = nextWeekday();
    if (!beforeCutoff(tradingDate)) return;
    const { data: { user } } = await db.auth.getUser();
    if (!user) {
      await db.auth.signInWithOAuth({ provider: "google", options: { redirectTo: window.location.href } });
      return;
    }
    buttons.forEach(b => b.disabled = true);
    const { error } = await db.rpc("place_prediction", {
      p_trading_date: tradingDate, p_direction: btn.dataset.vote, p_stake: 100
    });
    if (error) {
      result.innerHTML = "<b>提交失败</b><span>" + (error.message.includes("ALREADY_VOTED") ? "你今天已经投过票了。" : error.message.includes("VOTING_CLOSED") ? "投票已截止。" : "请稍后再试。") + "</span>";
      await render();
      return;
    }
    root.classList.add("celebrate", "vote-success");
    result.innerHTML = "<b>🔥 押注成功！</b><span>" + (btn.dataset.vote === "bull" ? "你押了看多" : "你押了看空") + " · 100 P 已锁定，等明天收盘见分晓！</span>";
    setTimeout(() => root.classList.remove("celebrate", "vote-success"), 900);
    await render();
    result.classList.add("vote-success");
    setTimeout(() => result.classList.remove("vote-success"), 900);
  }));

  if (login) login.addEventListener("click", async () => {
    const { data: { user } } = await db.auth.getUser();
    if (user) { await db.auth.signOut(); await render(); }
    else await db.auth.signInWithOAuth({ provider: "google", options: { redirectTo: window.location.href } });
  });

  db.auth.onAuthStateChange(() => render());
  render();
})();