// Voting UI: live Supabase community system\n(() => {
  const SUPABASE_URL = "https://hfdrdxxcaqdknniiypnz.supabase.co";
  const SUPABASE_KEY = "sb_publishable_YLtCCkTOO9KwJKNTyeIMFA_cuEmNG3k";
  const root = document.querySelector("[data-human-game]");
  if (!root) return;

  // Supabase CDN 可能比页面脚本晚一点加载；不要因此让投票按钮失效。
  let db = null;
  let initialized = false;
  function init() {
    if (initialized) return true;
    if (!window.supabase) return false;
    db = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
    initialized = true;
    return true;
  }
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
    if (!init()) return;
    const { data: { user } } = await db.auth.getUser();
    if (!user) {
      balance.textContent = "准备中…";
      streak.textContent = "—";
      buttons.forEach(b => b.disabled = false);
      result.innerHTML = "<b>🎯 直接选择方向</b><span>无需 Google 登录，首次参与自动创建游客身份并领取 3,000 P。</span>";
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
    if (!init()) {
      result.innerHTML = "<b>正在连接投票系统…</b><span>请再点一次，或刷新页面。</span>";
      return;
    }
    const tradingDate = nextWeekday();
    if (!beforeCutoff(tradingDate)) return;
    result.innerHTML = "<b>⏳ 正在提交…</b><span>正在连接游客身份与云端账户。</span>";
    const { data: { user }, error: userError } = await db.auth.getUser();
    if (userError) {
      result.innerHTML = "<b>身份读取失败</b><span>" + (userError.message || "Supabase Auth 读取失败") + "</span>";
      return;
    }
    let activeUser = user;
    if (!activeUser) {
      result.innerHTML = "<b>⏳ 创建游客身份…</b><span>第一次参与需要创建云端玩家身份。</span>";
      const { data: authData, error: authError } = await db.auth.signInAnonymously();
      if (authError) {
        result.innerHTML = "<b>游客身份创建失败</b><span>" + (authError.message || "Anonymous Sign-In 失败") + "</span>";
        return;
      }
      activeUser = authData.user;
      if (!activeUser) {
        result.innerHTML = "<b>游客身份创建失败</b><span>请刷新页面后再试。</span>";
        return;
      }
    }
    buttons.forEach(b => b.disabled = true);
    result.innerHTML = "<b>⏳ 云端处理中…</b><span>正在写入 100 P 押注。</span>";
    let rpcResult;
    try {
      rpcResult = await Promise.race([
        db.rpc("place_prediction", {
          p_trading_date: tradingDate, p_direction: btn.dataset.vote, p_stake: 100
        }),
        new Promise(resolve => setTimeout(() => resolve({ data: null, error: { message: "请求超时（10秒）。请检查 Supabase Data API / RPC 是否可用。" } }), 10000))
      ]);
    } catch (e) {
      rpcResult = { data: null, error: { message: e?.message || String(e) } };
    }
    const error = rpcResult?.error;
    if (error) {
      const msg = error.message || "未知错误";
      result.innerHTML = "<b>提交失败</b><span>" + (msg.includes("ALREADY_VOTED") ? "你今天已经投过票了。" : msg.includes("VOTING_CLOSED") ? "投票已截止。" : msg.includes("INSUFFICIENT_BALANCE") ? "P币余额不足。" : msg) + "</span>";
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

  if (login) login.style.display = "none";

  // 初始时先保证按钮可点击；登录/截止状态由 render() 再决定。
  buttons.forEach(b => b.disabled = false);
  let tries = 0;
  const boot = setInterval(() => {
    tries += 1;
    if (init()) {
      clearInterval(boot);
      db.auth.onAuthStateChange(() => render());
      render();
    } else if (tries >= 100) {
      clearInterval(boot);
      result.innerHTML = "<b>投票系统加载失败</b><span>请按 Ctrl+F5 强制刷新页面。</span>";
    }
  }, 50);
})();