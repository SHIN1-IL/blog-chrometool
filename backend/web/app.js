(() => {
  const API_BASE = ""; // same origin on Render

  const OBSTACLES = {
    plumbing: [
      ["배관 노후 심각", "배관 노후"],
      ["기름 슬러지 과다", "슬러지 과다"],
      ["작업 공간 협소", "공간 협소"],
      ["타업체 해결 실패", "타사 실패건"],
    ],
    cleaning: [
      ["심한 오염/찌든 때", "찌든 때"],
      ["가구·가전 이동 곤란", "이동 곤란"],
      ["악취·곰팡이", "악취/곰팡이"],
      ["입주 전 폐기물 과다", "폐기물 과다"],
    ],
    custom: [],
  };

  const PLACEHOLDERS = {
    plumbing: {
      order: "예: 싱크대 하부 누수 수리",
      issue: "예: 싱크대 하부장 누수 및 곰팡이 냄새",
      process: "예: 내시경 확인 후 주름관 교체 및 방수 실링",
      equipment: "예: 배관 내시경, 주름관",
    },
    cleaning: {
      order: "예: 입주 전 전체 청소",
      issue: "예: 입주 청소 · 주방/욕실 찌든 때 제거",
      process: "예: 가구 이동 후 스팀 클리닝 및 환기",
      equipment: "예: 스팀기, 진공청소기, 세제",
    },
    custom: {
      order: "예: 오늘 받은 주문 내용",
      issue: "예: 해결한 핵심 내용",
      process: "예: 작업 순서와 해결 과정",
      equipment: "예: 사용한 도구/장비",
    },
  };

  const els = {
    badge: document.getElementById("licenseBadge"),
    usageCard: document.getElementById("usageCard"),
    usagePlan: document.getElementById("usagePlan"),
    usageDays: document.getElementById("usageDays"),
    usageDaily: document.getElementById("usageDaily"),
    usageMonthly: document.getElementById("usageMonthly"),
    key: document.getElementById("licenseKey"),
    verifyBtn: document.getElementById("verifyBtn"),
    licenseError: document.getElementById("licenseError"),
    bankToggle: document.getElementById("bankToggle"),
    bankNotice: document.getElementById("bankNotice"),
    form: document.getElementById("genForm"),
    bizType: document.getElementById("bizType"),
    generateBtn: document.getElementById("generateBtn"),
    genError: document.getElementById("genError"),
    resultSection: document.getElementById("resultSection"),
    modelTag: document.getElementById("modelTag"),
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

  function hideUsage() {
    els.usageCard.hidden = true;
  }

  function renderUsage(data) {
    els.usageCard.hidden = false;
    els.usagePlan.textContent = data.plan_label || data.plan || "—";
    els.usageDays.textContent =
      data.plan === "trial" || data.plan === "demo"
        ? "1건 사용 시 종료"
        : `D-${data.remaining_days ?? "?"}일`;
    const dailyRem =
      data.daily_remaining ??
      Math.max(0, (data.daily_limit || 0) - (data.daily_used || 0));
    els.usageDaily.textContent = `${dailyRem}건 (한도 ${data.daily_limit}건)`;
    if (data.monthly_unlimited) {
      els.usageMonthly.textContent = "무제한";
    } else {
      const monthlyRem =
        data.monthly_remaining ??
        Math.max(0, (data.monthly_limit || 0) - (data.monthly_used || 0));
      els.usageMonthly.textContent = `${monthlyRem}건 (한도 ${data.monthly_limit}건)`;
    }
  }

  function renderBank(biz) {
    if (!biz) return;
    const monthly = Number(biz.monthlyPrice || 24900).toLocaleString("ko-KR");
    const yearly = Number(biz.yearlyPrice || 249000).toLocaleString("ko-KR");
    const quarterly = Number(biz.quarterlyPrice || 69000).toLocaleString("ko-KR");
    const legacy = Number(biz.legacyMonthlyPrice || 12900).toLocaleString("ko-KR");
    els.bankNotice.innerHTML =
      `💳 <b>동네광고 올인원</b><br>` +
      `월 ${monthly}원 · 3개월 ${quarterly}원 · 연 ${yearly}원<br>` +
      `한 번 입력 → 블로그 · 당근 · 네이버지도 · 카톡<br>` +
      `${biz.bankName} ${biz.accountNumber} (예금주: ${biz.accountHolder})<br>` +
      `입금 후 ${biz.contactMethod}(${biz.contact}) → ${biz.keyDeliveryMinutes}분 내 키<br>` +
      `<span style="color:#94a3b8;font-size:12px;">기존 월 ${legacy}원은 연장만. 서버 첫 연결 약 30초.</span>`;
  }

  function renderObstacles(type) {
    const box = document.getElementById("obstacleChecks");
    const items = OBSTACLES[type] || [];
    if (items.length === 0) {
      box.innerHTML = "";
      return;
    }
    box.innerHTML = items
      .map(
        ([v, label]) =>
          `<label><input type="checkbox" name="obstacle" value="${v}" /> ${label}</label>`
      )
      .join("");
  }

  function applyPlaceholders(type) {
    const p = PLACEHOLDERS[type] || PLACEHOLDERS.custom;
    document.getElementById("issue").placeholder = p.issue;
    document.getElementById("process").placeholder = p.process;
    document.getElementById("equipment").placeholder = p.equipment;
  }

  function onBizTypeChange() {
    const type = els.bizType.value;
    renderObstacles(type);
    applyPlaceholders(type);
  }

  els.bizType.addEventListener("change", onBizTypeChange);
  onBizTypeChange();

  els.bankToggle.addEventListener("click", () => {
    els.bankNotice.hidden = !els.bankNotice.hidden;
    els.bankToggle.classList.toggle("open", !els.bankNotice.hidden);
  });

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
      hideUsage();
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
        hideUsage();
        showError(els.licenseError, data.message || "등록할 수 없는 키입니다.");
        return;
      }
      isValid = true;
      licenseKey = key;
      localStorage.setItem("autoblog_license_key", key);
      const dailyRem =
        data.daily_remaining ??
        Math.max(0, (data.daily_limit || 0) - (data.daily_used || 0));
      els.generateBtn.disabled = dailyRem <= 0;
      const kind = dailyRem <= 0 ? "warn" : "active";
      setBadge(
        kind,
        `${data.plan_label || "구독"} · 오늘 남은 ${dailyRem}건`
      );
      renderUsage(data);
      showError(els.licenseError, "");
    } catch (e) {
      isValid = false;
      els.generateBtn.disabled = true;
      setBadge("inactive", "서버 연결 실패");
      hideUsage();
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

  function applyChannels(data) {
    const blog = data.naver_blog || {};
    document.getElementById("blogTitle").value = blog.title || "";
    document.getElementById("blogContent").value = blog.content || "";
    document.getElementById("blogTags").value = (blog.tags || []).join(" ");
    document.getElementById("daangnText").value = data.daangn_post || "";
    const place = data.place_review || {};
    document.getElementById("reviewSms").value = place.customer_sms || "";
    document.getElementById("placeNews").value = place.place_news || "";
    document.getElementById("placeKeywords").value = (place.place_keywords || []).join(", ");
    const kakao = data.kakao || {};
    document.getElementById("kakaoCustomer").value = kakao.customer_talk || "";
    document.getElementById("kakaoChannel").value = kakao.channel_post || "";
    els.modelTag.textContent = data.model ? `엔진: ${data.model}` : "";
  }

  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach((c) => c.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById(btn.dataset.tab).classList.add("active");
    });
  });

  function collectObstacles() {
    const checked = [
      ...document.querySelectorAll('input[name="obstacle"]:checked'),
    ].map((el) => el.value);
    const other = (document.getElementById("obstacleOther")?.value || "").trim();
    if (other) checked.push(other);
    return checked;
  }

  function bindVoiceInputs() {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    const hint = document.getElementById("voiceHint");
    if (!SR) {
      document.querySelectorAll(".mic-btn").forEach((b) => {
        b.style.display = "none";
      });
      if (hint) {
        hint.textContent =
          "이 브라우저는 음성 입력을 지원하지 않습니다. PC·안드로이드 크롬을 이용해 주세요.";
      }
      return;
    }
    let active = null;
    document.querySelectorAll(".mic-btn").forEach((btn) => {
      btn.addEventListener("click", (ev) => {
        ev.preventDefault();
        const input = document.getElementById(btn.dataset.for);
        if (!input) return;
        if (active) {
          try {
            active.stop();
          } catch {
            /* ignore */
          }
          active = null;
          document.querySelectorAll(".mic-btn").forEach((b) =>
            b.classList.remove("listening")
          );
        }
        const rec = new SR();
        rec.lang = "ko-KR";
        rec.interimResults = false;
        rec.onresult = (e) => {
          const said = e.results[0][0].transcript.trim();
          input.value = input.value ? `${input.value} ${said}` : said;
        };
        rec.onend = () => {
          btn.classList.remove("listening");
          if (active === rec) active = null;
        };
        rec.onerror = () => btn.classList.remove("listening");
        btn.classList.add("listening");
        active = rec;
        rec.start();
      });
    });
  }

  bindVoiceInputs();

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

    try {
      const data = await api("/api/generate", {
        license_key: licenseKey,
        biz_type: els.bizType.value,
        company_name: document.getElementById("companyName").value.trim(),
        order_detail: "",
        location: document.getElementById("location").value.trim(),
        customer_impression: document.getElementById("customerImpression").value.trim(),
        weather: document.getElementById("weather").value,
        issue: document.getElementById("issue").value.trim(),
        obstacles: collectObstacles(),
        process: document.getElementById("process").value.trim(),
        equipment: document.getElementById("equipment").value.trim(),
        customer_reaction: document.getElementById("customerReaction").value.trim(),
        feeling: document.getElementById("feeling").value.trim(),
        extra: document.getElementById("extra").value.trim(),
        tone: document.getElementById("tone").value,
        photo_count: Number(document.getElementById("photoCount").value || 3),
        video_count: Number(document.getElementById("videoCount").value || 0),
      });
      els.resultSection.hidden = false;
      applyChannels(data);
      els.resultSection.scrollIntoView({ behavior: "smooth", block: "start" });
      await verify(true);
    } catch (e) {
      showError(els.genError, e.message || "생성 실패");
    } finally {
      els.generateBtn.disabled = !isValid;
      els.generateBtn.textContent = "오늘 현장 광고 만들기";
    }
  });

  async function copyFrom(id, ok) {
    const el = document.getElementById(id);
    const text = el ? el.value : "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      els.copyMsg.hidden = false;
      els.copyMsg.textContent = ok;
    } catch {
      els.copyMsg.hidden = false;
      els.copyMsg.textContent = "길게 눌러 복사해 주세요.";
    }
  }

  document.getElementById("copyBlogBtn").addEventListener("click", () => {
    const t = [
      document.getElementById("blogTitle").value,
      document.getElementById("blogContent").value,
      document.getElementById("blogTags").value,
    ].join("\n\n");
    navigator.clipboard.writeText(t.trim()).then(
      () => {
        els.copyMsg.hidden = false;
        els.copyMsg.textContent = "복사되었습니다. 네이버 블로그 앱에 붙여넣기 하세요.";
      },
      () => {
        els.copyMsg.hidden = false;
        els.copyMsg.textContent = "길게 눌러 복사해 주세요.";
      }
    );
  });
  document.getElementById("copyDaangnBtn").addEventListener("click", () =>
    copyFrom("daangnText", "당근 문구가 복사되었습니다.")
  );
  document.getElementById("copySmsBtn").addEventListener("click", () =>
    copyFrom("reviewSms", "문자가 복사되었습니다.")
  );
  document.getElementById("copyPlaceNewsBtn").addEventListener("click", () =>
    copyFrom("placeNews", "플레이스 소식이 복사되었습니다.")
  );
  document.getElementById("copyKwBtn").addEventListener("click", () =>
    copyFrom("placeKeywords", "키워드가 복사되었습니다.")
  );
  document.getElementById("copyKakaoCustomerBtn").addEventListener("click", () =>
    copyFrom("kakaoCustomer", "고객 카톡이 복사되었습니다.")
  );
  document.getElementById("copyKakaoChannelBtn").addEventListener("click", () =>
    copyFrom("kakaoChannel", "채널 소식이 복사되었습니다.")
  );

  loadBusiness();
  if (licenseKey) verify(true);
})();
