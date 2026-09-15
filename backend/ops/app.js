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
    const blogM = Number(biz?.blogMonthlyPrice || biz?.legacyMonthlyPrice || 12900).toLocaleString("ko-KR");
    const allinM = Number(biz?.allinMonthlyPrice || biz?.monthlyPrice || 24900).toLocaleString("ko-KR");
    const plan = lic.plan || "";
    const isBlog = plan.includes("blog") && !plan.includes("allin");
    const product = isBlog ? "현장블로그 3분" : "동네광고 올인원";
    const features = isBlog
      ? "네이버 블로그 초안만 나갑니다."
      : "블로그 / 당근 / 네이버지도 / 카톡 초안이 한 번에 나갑니다.";
    const priceHint = isBlog
      ? `유료 월 ${blogM}원 · 하루 1건 · 달 30건`
      : `유료 월 ${allinM}원 · 하루 3건 · 달 90건`;
    return [
      "오토블로그 키 발급됐습니다.",
      "",
      `키: ${lic.license_key}`,
      `상품: ${product}`,
      `플랜: ${lic.plan_label || lic.plan}`,
      `기간: ${lic.expires_at} 까지`,
      `한도: 일 ${lic.daily_limit}건 / 달 ${lic.monthly_limit}건`,
      features,
      priceHint,
      "",
      "폰: https://blog-chrometool.onrender.com/app/",
      "키 넣고 [등록] → 현장 입력 → 생성 후 복사",
      "사진·짧은 영상은 글에 자리가 나옵니다. 각 앱에서 직접 넣으세요.",
      "",
      `구독 문의·연장은 ${biz?.contactMethod || "카톡"} ${biz?.contact || ""} / ${biz?.contactEmail || "acrosstool@gmail.com"}`.trim(),
    ].join("\n");
  }

  function escapeHtml(s) {
    return String(s ?? "")
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;");
  }

  async function loadList() {
    const data = await admin("/admin/licenses");
    const list = data.licenses || [];
    els.rows.innerHTML = list
      .map((lic) => {
        const key = lic.license_key;
        return `<tr>
          <td><code>${escapeHtml(key)}</code></td>
          <td>${escapeHtml(lic.plan_label || lic.plan)}</td>
          <td>${escapeHtml(lic.expires_at)}</td>
          <td>${escapeHtml(lic.status)}</td>
          <td>${lic.daily_used ?? 0}/${lic.daily_limit}</td>
          <td>
            <input class="note-edit" data-key="${escapeHtml(key)}" value="${escapeHtml(lic.note || "")}" />
          </td>
          <td class="actions">
            <button type="button" data-act="savenote" data-key="${escapeHtml(key)}">메모저장</button>
            <button type="button" data-act="copy" data-key="${escapeHtml(key)}">안내</button>
            <button type="button" data-act="extend30" data-key="${escapeHtml(key)}">+30일</button>
            <button type="button" data-act="suspend" data-key="${escapeHtml(key)}">정지</button>
            <button type="button" data-act="activate" data-key="${escapeHtml(key)}">활성</button>
          </td>
        </tr>`;
      })
      .join("");
  }

  const ISSUES = {
    "blog-30": { plan: "paid_blog", days: 30, notePrefix: "블로그 12900" },
    "blog-180": { plan: "paid_blog", days: 180, notePrefix: "블로그 64500" },
    "blog-365": { plan: "paid_blog", days: 365, notePrefix: "블로그 129000" },
    "allin-30": { plan: "paid_allin", days: 30, notePrefix: "올인원 24900" },
    "allin-180": { plan: "paid_allin", days: 180, notePrefix: "올인원 124500" },
    "allin-365": { plan: "paid_allin", days: 365, notePrefix: "올인원 249000" },
    "trial-blog": { plan: "trial_blog", days: 30, notePrefix: "블로그 체험" },
    "trial-allin": { plan: "trial_allin", days: 30, notePrefix: "올인원 체험" },
    "family-blog": { plan: "family_blog", days: 30, notePrefix: "블로그 지인" },
    "family-allin": { plan: "family_allin", days: 30, notePrefix: "올인원 지인" },
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

  function cleanToken(raw) {
    return String(raw || "")
      .replace(/[\u200B-\u200D\uFEFF]/g, "")
      .replace(/^["'\s]+|["'\s]+$/g, "")
      .trim();
  }

  async function enter(ev) {
    if (ev) ev.preventDefault();
    token = cleanToken(els.token.value);
    els.token.value = token;
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

  document.getElementById("loginForm").addEventListener("submit", enter);
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
  els.rows.addEventListener("keydown", async (ev) => {
    if (ev.key !== "Enter") return;
    const input = ev.target.closest(".note-edit");
    if (!input) return;
    ev.preventDefault();
    const key = input.dataset.key;
    try {
      await admin(`/admin/licenses/${encodeURIComponent(key)}/note`, {
        method: "PATCH",
        body: JSON.stringify({ note: input.value }),
      });
      els.issueMsg.hidden = false;
      els.issueMsg.textContent = `${key} 메모 저장됨`;
      await loadList();
    } catch (e) {
      alert(e.message);
    }
  });
  els.rows.addEventListener("click", async (ev) => {
    const btn = ev.target.closest("button[data-act]");
    if (!btn) return;
    const key = btn.dataset.key;
    try {
      if (btn.dataset.act === "savenote") {
        const input = els.rows.querySelector(`.note-edit[data-key="${key}"]`);
        const note = input ? input.value : "";
        await admin(`/admin/licenses/${encodeURIComponent(key)}/note`, {
          method: "PATCH",
          body: JSON.stringify({ note }),
        });
        els.issueMsg.hidden = false;
        els.issueMsg.textContent = `${key} 메모 저장됨`;
        await loadList();
        return;
      }
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
