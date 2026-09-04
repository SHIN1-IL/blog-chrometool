let isLicenseValid = false;

function renderBusinessNotice() {
  const el = document.getElementById("bankNotice");
  if (!el || typeof BUSINESS === "undefined") return;
  const price = BUSINESS.monthlyPrice.toLocaleString("ko-KR");
  el.innerHTML = `
    💳 <b>구독 안내:</b> 월 ${price}원 (30일)<br>
    ${BUSINESS.bankName} ${BUSINESS.accountNumber} (예금주: ${BUSINESS.accountHolder})<br>
    입금 후 ${BUSINESS.contactMethod}(${BUSINESS.contact}) 주시면 ${BUSINESS.keyDeliveryMinutes}분 내 키를 발급해 드립니다.<br>
    <span style="color:#94a3b8;font-size:11px;">※ 서버 첫 연결 시 30초 정도 걸릴 수 있습니다 (무료 호스팅).</span>
  `;
}

const els = {
  badge: () => document.getElementById("licenseBadge"),
  keyInput: () => document.getElementById("licenseKeyInput"),
  verifyBtn: () => document.getElementById("verifyKeyBtn"),
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
}

function setBadgeActive(data) {
  const badge = els.badge();
  badge.className = "status-badge status-active";
  badge.textContent =
    `구독 활성 (D-${data.remaining_days}일) · 오늘 ${data.daily_used}/${data.daily_limit}건`;
  isLicenseValid = true;
  els.generateBtn().disabled = data.daily_used >= data.daily_limit;
  showLicenseError(
    data.daily_used >= data.daily_limit
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

function getFormPayload() {
  const obstacles = Array.from(
    document.querySelectorAll(".checkbox-group input:checked")
  ).map((cb) => cb.value);

  return {
    license_key: els.keyInput().value.trim(),
    location: document.getElementById("location").value.trim(),
    weather: document.getElementById("weather").value,
    issue: document.getElementById("issue").value.trim(),
    obstacles,
    solution: document.getElementById("solution").value.trim(),
    feeling: document.getElementById("feeling").value.trim(),
    tone: document.getElementById("tone").value,
  };
}

function validateForm(payload) {
  if (!payload.location) return "현장 위치를 입력해 주세요.";
  if (!payload.issue) return "해결할 문제를 입력해 주세요.";
  if (!payload.solution) return "사용한 장비/해결 공정을 입력해 주세요.";
  if (!payload.tone) return "글 스타일을 선택해 주세요.";
  return null;
}

document.addEventListener("DOMContentLoaded", () => {
  renderBusinessNotice();
  chrome.storage.local.get(["licenseKey"], (result) => {
    const key = result.licenseKey || "DEMO-KEY";
    els.keyInput().value = key;
    verifyLicenseKey(key);
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
    if (err.message.includes("한도")) {
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
