let isLicenseValid = false;

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

function renderBusinessNotice() {
  const el = document.getElementById("bankNotice");
  if (!el || typeof BUSINESS === "undefined") return;
  const monthly = BUSINESS.monthlyPrice.toLocaleString("ko-KR");
  const yearly = (BUSINESS.yearlyPrice || 129000).toLocaleString("ko-KR");
  el.innerHTML = `
    💳 <b>구독 안내</b><br>
    월 ${monthly}원 (30일) · 연 ${yearly}원 (365일)<br>
    ${BUSINESS.bankName} ${BUSINESS.accountNumber} (예금주: ${BUSINESS.accountHolder})<br>
    입금 후 ${BUSINESS.contactMethod}(${BUSINESS.contact}) 주시면 ${BUSINESS.keyDeliveryMinutes}분 내 키를 발급해 드립니다.<br>
    <span style="color:#94a3b8;font-size:11px;">※ 서버 첫 연결 시 30초 정도 걸릴 수 있습니다 (무료 호스팅).</span>
  `;
}

function renderObstacles(type) {
  const box = document.getElementById("obstacleChecks");
  if (!box) return;
  if (type === "custom") {
    box.innerHTML =
      `<label class="full"><input type="text" id="obstacleCustom" placeholder="현장 고충을 직접 적어 주세요"></label>`;
    return;
  }
  box.innerHTML = OBSTACLES[type]
    .map(
      ([v, label]) =>
        `<label><input type="checkbox" value="${v}"> ${label}</label>`
    )
    .join("");
}

function applyPlaceholders(type) {
  const p = PLACEHOLDERS[type] || PLACEHOLDERS.custom;
  const order = document.getElementById("orderDetail");
  const issue = document.getElementById("issue");
  const process = document.getElementById("process");
  const equipment = document.getElementById("equipment");
  if (order) order.placeholder = p.order;
  if (issue) issue.placeholder = p.issue;
  if (process) process.placeholder = p.process;
  if (equipment) equipment.placeholder = p.equipment;
}

const els = {
  badge: () => document.getElementById("licenseBadge"),
  usageCard: () => document.getElementById("usageCard"),
  usagePlan: () => document.getElementById("usagePlan"),
  usageDays: () => document.getElementById("usageDays"),
  usageDaily: () => document.getElementById("usageDaily"),
  usageMonthly: () => document.getElementById("usageMonthly"),
  keyInput: () => document.getElementById("licenseKeyInput"),
  verifyBtn: () => document.getElementById("verifyKeyBtn"),
  bankToggle: () => document.getElementById("bankToggle"),
  bankNotice: () => document.getElementById("bankNotice"),
  licenseError: () => document.getElementById("licenseError"),
  generateBtn: () => document.getElementById("generateBtn"),
  resultSection: () => document.getElementById("resultSection"),
  generatedText: () => document.getElementById("generatedText"),
  modelTag: () => document.getElementById("modelTag"),
  copyBtn: () => document.getElementById("copyBtn"),
  injectBtn: () => document.getElementById("injectBtn"),
};

function showLicenseError(msg) {
  const el = els.licenseError();
  if (!msg) {
    el.style.display = "none";
    el.textContent = "";
    return;
  }
  el.textContent = msg;
  el.style.display = "block";
}

function setBadgeInactive(text) {
  const badge = els.badge();
  badge.className = "status-badge status-inactive";
  badge.textContent = text;
  isLicenseValid = false;
  els.generateBtn().disabled = true;
  els.usageCard().classList.remove("visible");
}

function renderUsage(data) {
  const card = els.usageCard();
  card.classList.add("visible");
  els.usagePlan().textContent = data.plan_label || data.plan || "—";
  els.usageDays().textContent =
    data.plan === "trial" || data.plan === "demo"
      ? "1건 사용 시 종료"
      : `D-${data.remaining_days ?? "?"}일`;
  const dailyRem =
    data.daily_remaining ??
    Math.max(0, (data.daily_limit || 0) - (data.daily_used || 0));
  els.usageDaily().textContent = `${dailyRem}건 (한도 ${data.daily_limit}건)`;
  if (data.monthly_unlimited) {
    els.usageMonthly().textContent = "무제한";
  } else {
    const monthlyRem =
      data.monthly_remaining ??
      Math.max(0, (data.monthly_limit || 0) - (data.monthly_used || 0));
    els.usageMonthly().textContent = `${monthlyRem}건 (한도 ${data.monthly_limit}건)`;
  }
}

function setBadgeActive(data) {
  const badge = els.badge();
  const dailyRem =
    data.daily_remaining ??
    Math.max(0, (data.daily_limit || 0) - (data.daily_used || 0));
  badge.className =
    dailyRem <= 0
      ? "status-badge status-warning"
      : "status-badge status-active";
  badge.textContent = `${data.plan_label || "구독"} · 오늘 남은 ${dailyRem}건`;
  isLicenseValid = true;
  els.generateBtn().disabled = dailyRem <= 0;
  renderUsage(data);
  showLicenseError(
    dailyRem <= 0
      ? `오늘 생성 한도(${data.daily_limit}건)를 모두 사용했습니다. 내일 다시 이용 가능합니다.`
      : ""
  );
}

async function verifyLicenseKey(key) {
  if (!key) {
    setBadgeInactive("라이선스 미등록");
    showLicenseError("");
    return;
  }

  els.verifyBtn().disabled = true;
  els.verifyBtn().textContent = "...";

  try {
    const res = await fetch(`${BACKEND_URL}/api/license/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ license_key: key }),
    });

    if (!res.ok) throw new Error("서버 응답 오류");

    const data = await res.json();

    if (data.valid) {
      setBadgeActive(data);
      await chrome.storage.local.set({ licenseKey: key });
      showLicenseError("");
    } else {
      setBadgeInactive("라이선스 만료/무효");
      showLicenseError(data.message || "라이선스를 확인할 수 없습니다.");
    }
  } catch {
    setBadgeInactive("서버 연결 실패");
    showLicenseError(
      "백엔드 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해 주세요."
    );
  } finally {
    els.verifyBtn().disabled = false;
    els.verifyBtn().textContent = "등록";
  }
}

function collectObstacles() {
  const custom = document.getElementById("obstacleCustom");
  if (custom) {
    const v = custom.value.trim();
    return v ? [v] : [];
  }
  return Array.from(
    document.querySelectorAll("#obstacleChecks input[type='checkbox']:checked")
  ).map((cb) => cb.value);
}

function getFormPayload() {
  return {
    license_key: els.keyInput().value.trim(),
    biz_type: document.getElementById("bizType").value,
    company_name: document.getElementById("companyName").value.trim(),
    order_detail: document.getElementById("orderDetail").value.trim(),
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
  };
}

function validateForm(payload) {
  if (!payload.location) return "현장위치를 입력해 주세요.";
  if (!payload.issue) return "해결사항을 입력해 주세요.";
  if (!payload.process && !payload.equipment) {
    return "해결과정 또는 사용장비를 입력해 주세요.";
  }
  if (!payload.tone) return "글 스타일을 선택해 주세요.";
  return null;
}

document.addEventListener("DOMContentLoaded", () => {
  renderBusinessNotice();
  const bizType = document.getElementById("bizType");
  renderObstacles(bizType.value);
  applyPlaceholders(bizType.value);
  bizType.addEventListener("change", () => {
    renderObstacles(bizType.value);
    applyPlaceholders(bizType.value);
  });
  els.bankToggle().addEventListener("click", () => {
    els.bankNotice().classList.toggle("visible");
  });
  chrome.storage.local.get(["licenseKey"], (result) => {
    const key = result.licenseKey || "";
    els.keyInput().value = key;
    if (key) verifyLicenseKey(key);
  });
});

els.verifyBtn().addEventListener("click", () => {
  verifyLicenseKey(els.keyInput().value.trim());
});

els.generateBtn().addEventListener("click", async () => {
  if (!isLicenseValid) {
    alert("라이선스 인증이 필요합니다.");
    return;
  }

  const payload = getFormPayload();
  const formError = validateForm(payload);
  if (formError) {
    alert(formError);
    return;
  }

  const btn = els.generateBtn();
  btn.disabled = true;
  btn.textContent = "⏳ AI가 작성 중입니다...";

  try {
    const res = await fetch(`${BACKEND_URL}/api/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "작성에 실패했습니다.");
    }

    els.generatedText().value = data.result;
    els.modelTag().textContent = data.model ? `생성 엔진: ${data.model}` : "";
    els.resultSection().classList.add("visible");

    await verifyLicenseKey(payload.license_key);
  } catch (err) {
    alert("오류: " + err.message);
    if (err.message.includes("한도") || err.message.includes("체험")) {
      await verifyLicenseKey(payload.license_key);
    }
  } finally {
    btn.textContent = "🚀 AI 블로그 글 생성하기";
    if (isLicenseValid) {
      btn.disabled = false;
    }
  }
});

els.copyBtn().addEventListener("click", async () => {
  const text = els.generatedText().value;
  if (!text) {
    alert("먼저 글을 생성해 주세요.");
    return;
  }
  try {
    await navigator.clipboard.writeText(text);
    alert("클립보드에 복사되었습니다! 네이버 에디터에서 Ctrl+V 하세요.");
  } catch {
    alert("복사에 실패했습니다. 텍스트를 직접 선택해 복사해 주세요.");
  }
});

function sendInjectMessage(tabId, text, frameId) {
  return new Promise((resolve, reject) => {
    const options =
      typeof frameId === "number" ? { frameId } : undefined;
    chrome.tabs.sendMessage(
      tabId,
      { action: "INJECT_CONTENT", text },
      options,
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
        } else {
          resolve(response);
        }
      }
    );
  });
}

async function findNaverWriteTab() {
  const [active] = await chrome.tabs.query({
    active: true,
    currentWindow: true,
  });
  if (active?.url?.includes("blog.naver.com")) return active;

  const tabs = await chrome.tabs.query({
    currentWindow: true,
    url: ["*://blog.naver.com/*"],
  });
  return (
    tabs.find((t) => /Write|PostWrite|GoBlogWrite|Redirect=Write/i.test(t.url || "")) ||
    tabs[0] ||
    null
  );
}

function parseGeneratedForClipboard(rawText) {
  if (rawText.includes("[제목]") && rawText.includes("[본문]")) {
    const afterTitle = rawText.split("[제목]")[1];
    const bodyParts = afterTitle.split("[본문]");
    const title = bodyParts[0].trim();
    const rest = bodyParts[1] || "";
    let body = rest;
    let tags = "";
    if (rest.includes("[태그]")) {
      const tagParts = rest.split("[태그]");
      body = tagParts[0].trim();
      tags = tagParts[1].trim();
    } else {
      body = rest.trim();
    }
    if (tags) body = `${body}\n\n${tags}`;
    return { title, body };
  }
  return { title: "", body: rawText };
}

async function tryInject(tabId, text) {
  const { body } = parseGeneratedForClipboard(text);

  // Prime clipboard so content.js can execCommand('paste') into the body
  if (body) {
    try {
      await navigator.clipboard.writeText(body);
    } catch (e) {
      console.warn("[AutoBlog] clipboard prime failed:", e);
    }
  }

  let frameResults = [];
  try {
    await chrome.scripting.executeScript({
      target: { tabId, allFrames: true },
      files: ["content.js"],
    });
    frameResults = await chrome.scripting.executeScript({
      target: { tabId, allFrames: true },
      func: (payload) => {
        if (typeof window.__autoblogInject === "function") {
          return window.__autoblogInject(payload);
        }
        return { success: false, skipped: true, message: "injector 없음" };
      },
      args: [text],
    });
  } catch (e) {
    console.warn("[AutoBlog] allFrames inject:", e);
  }

  let result =
    (frameResults || []).find((r) => r?.result?.success)?.result ||
    (frameResults || []).find((r) => r?.result && r.result.skipped === false)
      ?.result ||
    null;

  // If title landed but body did not, try a focused paste pass in all frames
  if (result && result.titleInjected && !result.bodyInjected && body) {
    try {
      await navigator.clipboard.writeText(body);
      const pasteResults = await chrome.scripting.executeScript({
        target: { tabId, allFrames: true },
        func: () => {
          const isTitle = (el) =>
            !!(
              el?.closest?.(".se-documentTitle") ||
              el?.closest?.("[class*='documentTitle']")
            );
          const hints = document.querySelectorAll(
            ".se-main-container [contenteditable='true'], .se-component.se-text [contenteditable='true'], .se-main-container .se-placeholder, .se-main-container"
          );
          let target = null;
          for (const el of hints) {
            if (!isTitle(el)) {
              target = el;
              break;
            }
          }
          if (!target) return { success: false };
          target.click();
          target.focus?.();
          const ok = document.execCommand("paste");
          const sample = (document.querySelector(".se-main-container")?.innerText || "")
            .replace(/\s+/g, "")
            .slice(0, 30);
          return { success: !!ok && sample.length > 10, sampleLen: sample.length };
        },
      });
      if ((pasteResults || []).some((r) => r?.result?.success)) {
        return {
          success: true,
          titleInjected: true,
          bodyInjected: true,
          message: "주입 완료",
        };
      }
    } catch (e) {
      console.warn("[AutoBlog] body paste pass:", e);
    }
  }

  if (result?.success) return result;
  if (result) return result;

  try {
    return await sendInjectMessage(tabId, text);
  } catch {
    return {
      success: false,
      message: "에디터 프레임에 연결하지 못했습니다.",
    };
  }
}

async function copyToClipboard(text) {
  await navigator.clipboard.writeText(text);
}

els.injectBtn().addEventListener("click", async () => {
  const text = els.generatedText().value;
  if (!text) {
    alert("먼저 글을 생성해 주세요.");
    return;
  }

  const tab = await findNaverWriteTab();
  if (!tab?.id || !tab.url?.includes("blog.naver.com")) {
    alert("네이버 블로그 글쓰기(스마트에디터) 탭을 열어두고 실행해 주세요.");
    return;
  }

  const btn = els.injectBtn();
  btn.disabled = true;
  btn.textContent = "⏳ 에디터에 주입 중...";

  try {
    const result = await tryInject(tab.id, text);
    if (result?.success) {
      alert(
        "에디터에 주입 완료! 사진을 첨부하고 최종 확인 후 [발행]을 눌러주세요."
      );
      return;
    }

    // Title often succeeds while body fails — guide a one-step body paste
    if (result?.titleInjected && !result?.bodyInjected) {
      const { body } = parseGeneratedForClipboard(text);
      try {
        await copyToClipboard(body || text);
        alert(
          "제목은 입력됐습니다.\n\n본문 칸(글 쓰는 빈 영역)을 한 번 클릭한 뒤\n⌘+V (Ctrl+V)로 붙여넣기 하세요.\n\n본문은 이미 클립보드에 복사해 두었습니다."
        );
        return;
      } catch {
        /* fall through to generic */
      }
    }

    throw new Error(result?.message || "주입 실패");
  } catch {
    const useCopy = confirm(
      "에디터 자동 주입에 실패했습니다.\n\n클립보드로 복사한 뒤 에디터에서 Ctrl+V 하시겠습니까?"
    );
    if (useCopy) {
      try {
        await copyToClipboard(text);
        alert("클립보드에 복사되었습니다! 에디터에서 Ctrl+V 하세요.");
      } catch {
        alert("복사에도 실패했습니다. [클립보드 복사] 버튼을 이용해 주세요.");
      }
    }
  } finally {
    btn.disabled = false;
    btn.textContent = "📝 네이버 에디터로 보내기";
  }
});
