(() => {
  const TOKEN_KEY = "autoblog_ops_token";
  const els = {
    token: document.getElementById("token"),
    loginBtn: document.getElementById("loginBtn"),
    loginErr: document.getElementById("loginErr"),
    desk: document.getElementById("desk"),
    note: document.getElementById("note"),
    issueMsg: document.getElementById("issueMsg"),
    customerMsg: document.getElementById("customerMsg"),
    rows: document.getElementById("rows"),
  };

  let token = sessionStorage.getItem(TOKEN_KEY) || "";
  let biz = null;

  function showErr(msg) {
    els.loginErr.hidden = !msg;
    els.loginErr.textContent = msg || "";
  }

  async function admin(path, opts = {}) {
    const res = await fetch(path, {
      ...opts,
      headers: {
        "Content-Type": "application/json",
        "X-Admin-Token": token,
        ...(opts.headers || {}),
      },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const d = data.detail || data.message || `HTTP ${res.status}`;
      throw new Error(typeof d === "string" ? d : JSON.stringify(d));
    }
    return data;
  }

  function customerCopy(lic) {
    const monthly = Number(biz?.monthlyPrice || 24900).toLocaleString("ko-KR");
    return [
      "오토블로그 키 발급됐습니다.",
      "",
      `키: ${lic.license_key}`,
      `기간: ${lic.expires_at} 까지`,
      `플랜: ${lic.plan_label || lic.plan} (일 ${lic.daily_limit}건)`,
      "블로그 / 당근 / 네이버지도 / 카톡 초안이 한 번에 나갑니다.",
      "",
      "폰: https://blog-chrometool.onrender.com/app/",
      "키 넣고 [등록] → 현장 입력 → 생성 후 채널별 복사",
      "사진·짧은 영상은 글에 자리가 나옵니다. 각 앱에서 직접 넣으세요.",
      "",
      `구독 문의·연장은 ${biz?.contactMethod || "카톡"} ${biz?.contact || ""}`.trim(),
      `(올인원 월 ${monthly}원)`,
    ].join("\n");
  }

  async function loadList() {
    const data = await admin("/admin/licenses");
    const list = data.licenses || [];
    els.rows.innerHTML = list
      .map((lic) => {
        const key = lic.license_key;
        return `<tr>
          <td><code>${key}</code></td>
          <td>${lic.plan_label || lic.plan}</td>
          <td>${lic.expires_at}</td>
          <td>${lic.status}</td>
          <td>${lic.daily_used ?? 0}/${lic.daily_limit}</td>
          <td>${lic.note || ""}</td>
          <td class="actions">
            <button type="button" data-act="copy" data-key="${key}">안내</button>
            <button type="button" data-act="extend30" data-key="${key}">+30일</button>
            <button type="button" data-act="suspend" data-key="${key}">정지</button>
            <button type="button" data-act="activate" data-key="${key}">활성</button>
          </td>
        </tr>`;
      })
      .join("");
  }

  const ISSUES = {
    "allin-30": { plan: "paid", days: 30, notePrefix: "올인원 24900" },
    "allin-90": { plan: "paid", days: 90, notePrefix: "올인원 69000" },
    "allin-365": { plan: "paid", days: 365, notePrefix: "올인원 249000" },
    "legacy-30": { plan: "paid", days: 30, notePrefix: "일기 12900" },
    trial: { plan: "trial", days: 30, notePrefix: "체험" },
    "family-30": { plan: "family_free", days: 30, notePrefix: "지인" },
  };

  async function issue(kind) {
    const spec = ISSUES[kind];
    const extra = els.note.value.trim();
    const note = extra ? `${spec.notePrefix} / ${extra}` : spec.notePrefix;
    const lic = await admin("/admin/licenses", {
      method: "POST",
      body: JSON.stringify({
        plan: spec.plan,
        days: spec.days,
        note,
      }),
    });
    els.customerMsg.value = customerCopy(lic);
    els.issueMsg.hidden = false;
    els.issueMsg.textContent = `발급됨: ${lic.license_key}`;
    await loadList();
  }

  async function enter() {
    token = els.token.value.trim();
    if (!token) {
      showErr("토큰을 입력해 주세요.");
      return;
    }
    try {
      await admin("/admin/licenses");
      sessionStorage.setItem(TOKEN_KEY, token);
      showErr("");
      document.getElementById("loginCard").hidden = true;
      els.desk.hidden = false;
      try {
        const res = await fetch("/api/business");
        if (res.ok) biz = await res.json();
      } catch {
        /* optional */
      }
      await loadList();
    } catch (e) {
      sessionStorage.removeItem(TOKEN_KEY);
      showErr(e.message || "인증 실패");
    }
  }

  els.loginBtn.addEventListener("click", enter);
  document.getElementById("copyMsgBtn").addEventListener("click", async () => {
    const t = els.customerMsg.value;
    if (!t) return;
    await navigator.clipboard.writeText(t);
    els.issueMsg.hidden = false;
    els.issueMsg.textContent = "안내문을 복사했습니다.";
  });
  document.getElementById("refreshBtn").addEventListener("click", () => loadList().catch((e) => alert(e.message)));
  document.querySelectorAll("[data-issue]").forEach((btn) => {
    btn.addEventListener("click", () => issue(btn.dataset.issue).catch((e) => alert(e.message)));
  });
  els.rows.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("button[data-act]");
    if (!btn) return;
    const key = btn.dataset.key;
    try {
      if (btn.dataset.act === "copy") {
        const lic = await admin(`/admin/licenses/${encodeURIComponent(key)}`);
        lic.plan_label = lic.plan_label || lic.plan;
        els.customerMsg.value = customerCopy(lic);
        els.issueMsg.hidden = false;
        els.issueMsg.textContent = `${key} 안내문 작성됨`;
        return;
      }
      if (btn.dataset.act === "extend30") {
        await admin(`/admin/licenses/${encodeURIComponent(key)}/extend`, {
          method: "POST",
          body: JSON.stringify({ days: 30 }),
        });
      }
      if (btn.dataset.act === "suspend") {
        await admin(`/admin/licenses/${encodeURIComponent(key)}/suspend`, { method: "POST" });
      }
      if (btn.dataset.act === "activate") {
        await admin(`/admin/licenses/${encodeURIComponent(key)}/activate`, { method: "POST" });
      }
      await loadList();
    } catch (e) {
      alert(e.message);
    }
  });

  if (token) {
    els.token.value = token;
    enter();
  }
})();
