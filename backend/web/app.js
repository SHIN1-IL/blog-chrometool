(() => {
  const API_BASE = ""; // same origin on Render

  const els = {
    badge: document.getElementById("licenseBadge"),
    key: document.getElementById("licenseKey"),
    verifyBtn: document.getElementById("verifyBtn"),
    licenseError: document.getElementById("licenseError"),
    bankNotice: document.getElementById("bankNotice"),
    form: document.getElementById("genForm"),
    generateBtn: document.getElementById("generateBtn"),
    genError: document.getElementById("genError"),
    resultSection: document.getElementById("resultSection"),
    generatedText: document.getElementById("generatedText"),
    modelTag: document.getElementById("modelTag"),
    copyBtn: document.getElementById("copyBtn"),
    copyMsg: document.getElementById("copyMsg"),
  };

  let licenseKey = localStorage.getItem("autoblog_license_key") || "";
  let isValid = false;

  if (licenseKey) {
    els.key.value = licenseKey;
  }

  function showError(el, msg) {
    if (!msg) {
      el.hidden = true;
      el.textContent = "";
      return;
    }
    el.hidden = false;
    el.textContent = msg;
  }

  function setBadge(kind, text) {
    els.badge.className = `badge ${kind}`;
    els.badge.textContent = text;
  }

  function renderBank(biz) {
    if (!biz) return;
    const price = Number(biz.monthlyPrice || 29000).toLocaleString("ko-KR");
    els.bankNotice.innerHTML =
      `💳 <b>구독 안내:</b> 월 ${price}원 (30일)<br>` +
      `${biz.bankName} ${biz.accountNumber} (예금주: ${biz.accountHolder})<br>` +
      `입금 후 ${biz.contactMethod}(${biz.contact}) 주시면 ${biz.keyDeliveryMinutes}분 내 키를 발급해 드립니다.<br>` +
      `<span style="color:#94a3b8;font-size:12px;">※ 서버 첫 연결 시 30초 정도 걸릴 수 있습니다 (무료 호스팅).</span>`;
  }

  async function api(path, body) {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const detail = data.detail || data.message || `요청 실패 (${res.status})`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return data;
  }

  async function loadBusiness() {
    try {
      const res = await fetch(`${API_BASE}/api/business`);
      if (res.ok) renderBank(await res.json());
    } catch {
      /* optional */
    }
  }

  async function verify(silent) {
    const key = els.key.value.trim();
    if (!key) {
      if (!silent) showError(els.licenseError, "라이선스 키를 입력해 주세요.");
      return;
    }
    showError(els.licenseError, "");
    els.verifyBtn.disabled = true;
    els.verifyBtn.textContent = "확인중";
    try {
      const data = await api("/api/license/verify", { license_key: key });
      if (!data.valid) {
        isValid = false;
        els.generateBtn.disabled = true;
        setBadge("inactive", "라이선스 무효");
        showError(els.licenseError, data.message || "등록할 수 없는 키입니다.");
        return;
      }
      isValid = true;
      licenseKey = key;
      localStorage.setItem("autoblog_license_key", key);
      els.generateBtn.disabled = false;
      const days = data.remaining_days ?? "?";
      const used = data.daily_used ?? 0;
      const limit = data.daily_limit ?? 10;
      setBadge(
        used >= limit ? "warn" : "active",
        `구독 활성 (D-${days}일) · 오늘 ${used}/${limit}건`
      );
      showError(els.licenseError, "");
    } catch (e) {
      isValid = false;
      els.generateBtn.disabled = true;
      setBadge("inactive", "서버 연결 실패");
      showError(
        els.licenseError,
        e.message.includes("Failed") || e.message.includes("fetch")
          ? "서버에 연결할 수 없습니다. 잠시 후 다시 시도해 주세요."
          : e.message
      );
    } finally {
      els.verifyBtn.disabled = false;
      els.verifyBtn.textContent = "등록";
    }
  }

  els.verifyBtn.addEventListener("click", () => verify(false));

  els.form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (!isValid || !licenseKey) {
      showError(els.genError, "먼저 라이선스 키를 등록해 주세요.");
      return;
    }
    showError(els.genError, "");
    els.copyMsg.hidden = true;
    els.generateBtn.disabled = true;
    els.generateBtn.textContent = "생성 중… (최대 1분)";

    const obstacles = [...document.querySelectorAll('input[name="obstacle"]:checked')].map(
      (el) => el.value
    );

    try {
      const data = await api("/api/generate", {
        license_key: licenseKey,
        location: document.getElementById("location").value.trim(),
        weather: document.getElementById("weather").value,
        issue: document.getElementById("issue").value.trim(),
        obstacles,
        solution: document.getElementById("solution").value.trim(),
        feeling: document.getElementById("feeling").value.trim(),
        tone: document.getElementById("tone").value,
      });
      els.resultSection.hidden = false;
      els.generatedText.value = data.result || "";
      els.modelTag.textContent = data.model ? `엔진: ${data.model}` : "";
      els.resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
      await verify(true);
    } catch (e) {
      showError(els.genError, e.message || "생성 실패");
    } finally {
      els.generateBtn.disabled = !isValid;
      els.generateBtn.textContent = "AI 블로그 글 생성하기";
    }
  });

  els.copyBtn.addEventListener("click", async () => {
    const text = els.generatedText.value;
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      els.copyMsg.hidden = false;
      els.copyMsg.textContent = "복사되었습니다. 네이버 블로그 앱에서 붙여넣기 하세요.";
    } catch {
      els.generatedText.focus();
      els.generatedText.select();
      els.copyMsg.hidden = false;
      els.copyMsg.textContent = "복사 버튼을 쓸 수 없습니다. 글을 길게 눌러 복사해 주세요.";
    }
  });

  loadBusiness();
  if (licenseKey) verify(true);
})();
