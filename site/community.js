// Community + account system for SSE dashboard
(() => {
  const SUPABASE_URL = "https://hfdrdxxcaqdknniiypnz.supabase.co";
  const SUPABASE_KEY = "sb_publishable_YLtCCkTOO9KwJKNTyeIMFA_cuEmNG3k";
  const root = document.querySelector("[data-human-game]");
  if (!root) return;

  let db = null, initialized = false;
  const balance = root.querySelector("[data-balance]");
  const streak = root.querySelector("[data-streak]");
  const result = root.querySelector("[data-result]");
  const buttons = [...root.querySelectorAll("[data-vote]")];
  const login = root.querySelector("[data-login]");
  const leaderboard = root.querySelector(".leaderboard");

  const modal = document.querySelector("[data-auth-modal]");
  const accountButtons = [...document.querySelectorAll("[data-account],[data-login]")];
  const closeBtn = modal?.querySelector("[data-auth-close]");
  const tabs = [...(modal?.querySelectorAll("[data-auth-mode]") || [])];
  const form = modal?.querySelector("[data-auth-form]");
  const tabsWrap = modal?.querySelector("[data-auth-tabs]");
  const accountView = modal?.querySelector("[data-account-view]");
  const nicknameField = modal?.querySelector("[data-nickname-field]");
  const password2Field = modal?.querySelector("[data-password2-field]");
  const submit = modal?.querySelector("[data-auth-submit]");
  const message = modal?.querySelector("[data-auth-message]");
  const accountMessage = modal?.querySelector("[data-account-message]");
  const accountEmail = modal?.querySelector("[data-account-email]");
  const accountBalance = modal?.querySelector("[data-account-balance]");
  const accountNickname = modal?.querySelector("[data-account-nickname]");
  const subtitle = modal?.querySelector("[data-auth-subtitle]");
  let authMode = "login";

  function init() {
    if (initialized) return true;
    if (!window.supabase) return false;
    db = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);
    initialized = true;
    return true;
  }
  function sgNow() { return new Date(Date.now() + 8 * 60 * 60 * 1000); }
  function dateKey(d) { return d.toISOString().slice(0,10); }
  function nextWeekday() {
    const d = sgNow(); d.setUTCDate(d.getUTCDate() + 1);
    while (d.getUTCDay() === 0 || d.getUTCDay() === 6) d.setUTCDate(d.getUTCDate() + 1);
    return dateKey(d);
  }
  function beforeCutoff(tradingDate) {
    const now = sgNow(), today = dateKey(now);
    if (today < tradingDate) return true;
    if (today > tradingDate) return false;
    return now.getUTCHours() < 9;
  }
  function escapeHtml(v) {
    return String(v ?? "").replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  }
  async function currentUser() {
    if (!init()) return null;
    const { data, error } = await db.auth.getUser();
    return error ? null : data?.user || null;
  }
  function showModal(mode = "login") {
    if (!modal) return;
    modal.classList.add("open"); modal.setAttribute("aria-hidden","false");
    setMode(mode);
  }
  function hideModal() { modal?.classList.remove("open"); modal?.setAttribute("aria-hidden","true"); }
  function setMode(mode) {
    authMode = mode;
    const account = mode === "account";
    tabsWrap.style.display = account ? "none" : "grid";
    form.style.display = account ? "none" : "grid";
    accountView.style.display = account ? "grid" : "none";
    tabs.forEach(t => t.classList.toggle("active", t.dataset.authMode === mode));
    if (account) {
      subtitle.textContent = "管理你的登录资料、P币和排行榜身份。";
      return;
    }
    subtitle.textContent = mode === "login" ? "登录后保存你的 P币、预测和排行榜成绩。" : "创建正式账户，跨设备保存你的成绩。";
    nicknameField.style.display = mode === "register" ? "block" : "none";
    password2Field.style.display = mode === "register" ? "block" : "none";
    submit.textContent = mode === "login" ? "登录" : "注册";
    form.elements.password.autocomplete = mode === "login" ? "current-password" : "new-password";
    message.textContent = "";
    message.className = "auth-message";
  }
  function authMsg(text, ok=false) {
    message.textContent = text; message.className = "auth-message " + (ok ? "ok" : "err");
  }
  async function refreshAccountButton() {
    const user = await currentUser();
    accountButtons.forEach(b => {
      if (user && !user.is_anonymous) b.textContent = "👤 我的账户";
      else if (user?.is_anonymous) b.textContent = "👤 游客账户";
      else b.textContent = "登录 / 注册";
    });
    return user;
  }
  async function openAccount() {
    const user = await refreshAccountButton();
    if (!user) showModal("login");
    else showModal("account");
    if (user) await loadAccount(user);
  }
  async function loadAccount(user) {
    const { data: profile } = await db.from("profiles").select("nickname,p_balance").eq("id", user.id).single();
    accountEmail.textContent = user.email || (user.is_anonymous ? "游客身份（未绑定邮箱）" : "—");
    accountBalance.textContent = Number(profile?.p_balance || 0).toLocaleString() + " P";
    accountNickname.value = profile?.nickname || user.user_metadata?.nickname || "新玩家";
    accountMessage.textContent = user.is_anonymous
      ? "当前是游客账户。正式注册/登录后可跨设备保留账户。"
      : "";
    accountMessage.className = "auth-message " + (user.is_anonymous ? "" : "ok");
  }
  async function render() {
    if (!init()) return;
    const user = await currentUser();
    await refreshAccountButton();
    if (!user) {
      balance.textContent = "登录后";
      streak.textContent = "—";
      buttons.forEach(b => b.disabled = false);
      result.innerHTML = "<b>🎯 登录后参与</b><span>注册或登录后，P币和每日预测会保存到你的账户。</span>";
      return;
    }
    const { data: profile } = await db.from("profiles").select("p_balance,nickname").eq("id", user.id).single();
    const tradingDate = nextWeekday();
    const { data: prediction } = await db.from("predictions").select("direction,status").eq("user_id", user.id).eq("trading_date", tradingDate).maybeSingle();
    balance.textContent = Number(profile?.p_balance || 0).toLocaleString() + " P";
    buttons.forEach(b => {
      b.disabled = !!prediction || !beforeCutoff(tradingDate);
      b.classList.toggle("selected", b.dataset.vote === prediction?.direction);
    });
    if (!beforeCutoff(tradingDate) && !prediction) result.innerHTML = "<b>⏰ 今日投票已截止</b><span>每天 09:00（UTC+8）锁定。</span>";
    else if (prediction) result.innerHTML = "<b>今天已提交：" + (prediction.direction === "bull" ? "🟢 看多" : "🔴 看空") + "</b><span>等待下一交易日收盘结算。</span>";
    else result.innerHTML = "<b>🎯 今天还没有押</b><span>选一个方向，100 P 入场，明天收盘揭晓胜负。</span>";
    await loadLeaderboard(user.id);
  }
  async function loadLeaderboard(me) {
    const { data, error } = await db.rpc("get_leaderboard");
    if (error || !leaderboard) return;
    const rows = (data || []).slice(0,10).map((x,i) => {
      const medal = ["🥇","🥈","🥉"][i] || (i+1);
      return '<div class="leader-row ' + (x.user_id === me ? "top" : "") + '"><span>' + medal + '</span><b>' +
        escapeHtml(x.user_id === me ? "你" : (x.nickname || "玩家")) + '</b><small>👤 玩家 · ' +
        Number(x.accuracy || 0).toFixed(1) + '%</small><strong>' + Number(x.p_balance || 0).toLocaleString() + ' P</strong></div>';
    }).join("");
    leaderboard.querySelectorAll(".leader-row").forEach(x => x.remove());
    leaderboard.insertAdjacentHTML("beforeend", rows);
  }

  buttons.forEach(btn => btn.addEventListener("click", async () => {
    if (!init()) { result.innerHTML = "<b>投票系统加载失败</b><span>请按 Ctrl+F5 后再试。</span>"; return; }
    const tradingDate = nextWeekday();
    if (!beforeCutoff(tradingDate)) return;
    const user = await currentUser();
    if (!user) { showModal("login"); authMsg("请先登录或注册，登录后才能下注。"); return; }
    result.innerHTML = "<b>⏳ 云端处理中…</b><span>正在写入 100 P 押注。</span>";
    buttons.forEach(b => b.disabled = true);
    let rpcResult;
    try {
      rpcResult = await Promise.race([
        db.rpc("place_prediction",{p_trading_date:tradingDate,p_direction:btn.dataset.vote,p_stake:100}),
        new Promise(resolve => setTimeout(() => resolve({error:{message:"请求超时（10秒），请检查 Supabase RPC。"}}),10000))
      ]);
    } catch(e) { rpcResult = {error:{message:e?.message || String(e)}}; }
    const error = rpcResult?.error;
    if (error) {
      const msg = error.message || "未知错误";
      result.innerHTML = "<b>提交失败</b><span>" +
        (msg.includes("ALREADY_VOTED") ? "你已经投过票了。" : msg.includes("VOTING_CLOSED") ? "投票已截止。" :
         msg.includes("INSUFFICIENT_BALANCE") ? "P币余额不足。" : escapeHtml(msg)) + "</span>";
      await render(); return;
    }
    root.classList.add("celebrate","vote-success");
    result.innerHTML = "<b>🔥 押注成功！</b><span>" + (btn.dataset.vote === "bull" ? "你押了看多" : "你押了看空") + " · 100 P 已锁定，等明天收盘见分晓！</span>";
    setTimeout(() => root.classList.remove("celebrate","vote-success"),900);
    await render();
  }));

  accountButtons.forEach(b => b.addEventListener("click", openAccount));
  closeBtn?.addEventListener("click", hideModal);
  modal?.addEventListener("click", e => { if (e.target === modal) hideModal(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") hideModal(); });
  tabs.forEach(t => t.addEventListener("click", () => setMode(t.dataset.authMode)));

  form?.addEventListener("submit", async e => {
    e.preventDefault();
    if (!init()) return;
    const email = form.elements.email.value.trim();
    const password = form.elements.password.value;
    const nickname = form.elements.nickname?.value.trim() || "新玩家";
    if (password.length < 8) { authMsg("密码至少 8 位。"); return; }
    if (authMode === "register" && password !== form.elements.password2.value) { authMsg("两次密码不一致。"); return; }
    submit.disabled = true; submit.textContent = authMode === "login" ? "登录中…" : "注册中…";
    try {
      if (authMode === "login") {
        const { error } = await db.auth.signInWithPassword({email,password});
        if (error) throw error;
        authMsg("登录成功。",true);
        await render();
        setTimeout(hideModal,500);
      } else {
        const redirect = location.href.split("#")[0];
        const { data, error } = await db.auth.signUp({
          email,password,
          options:{emailRedirectTo:redirect,data:{nickname}}
        });
        if (error) throw error;
        if (data.session) {
          await db.from("profiles").update({nickname}).eq("id",data.user.id);
          authMsg("注册成功，账户已经登录。",true);
          await render();
          setTimeout(() => { setMode("account"); loadAccount(data.user); },500);
        } else {
          authMsg("注册成功！请打开邮箱里的确认链接，完成邮箱验证后再登录。",true);
        }
      }
    } catch(e) {
      authMsg(e?.message || "操作失败，请稍后再试。");
    } finally {
      submit.disabled = false;
      submit.textContent = authMode === "login" ? "登录" : "注册";
    }
  });

  modal?.querySelector("[data-save-profile]")?.addEventListener("click", async () => {
    const user = await currentUser(); if (!user) return;
    const nickname = accountNickname.value.trim().slice(0,20) || "新玩家";
    const { error } = await db.from("profiles").update({nickname}).eq("id",user.id);
    accountMessage.textContent = error ? ("保存失败：" + error.message) : "账户资料已保存。";
    accountMessage.className = "auth-message " + (error ? "err" : "ok");
    await render();
  });
  modal?.querySelector("[data-change-password]")?.addEventListener("click", async () => {
    const user = await currentUser(); if (!user || user.is_anonymous) {
      accountMessage.textContent = "游客账户还没有密码。请注册正式账户后再设置密码。";
      accountMessage.className = "auth-message err"; return;
    }
    const password = prompt("请输入新的密码（至少 8 位）：");
    if (!password) return;
    if (password.length < 8) { accountMessage.textContent = "密码至少 8 位。"; accountMessage.className = "auth-message err"; return; }
    const { error } = await db.auth.updateUser({password});
    accountMessage.textContent = error ? ("修改失败：" + error.message) : "密码已更新。";
    accountMessage.className = "auth-message " + (error ? "err" : "ok");
  });
  modal?.querySelector("[data-logout]")?.addEventListener("click", async () => {
    await db.auth.signOut();
    hideModal(); await render();
  });

  if (login) login.addEventListener("click", openAccount);
  buttons.forEach(b => b.disabled = false);
  let tries = 0;
  const boot = setInterval(() => {
    tries++;
    if (init()) {
      clearInterval(boot);
      db.auth.onAuthStateChange(() => render());
      render();
    } else if (tries >= 100) {
      clearInterval(boot);
      result.innerHTML = "<b>账户系统加载失败</b><span>请按 Ctrl+F5 强制刷新页面。</span>";
    }
  },50);
})();