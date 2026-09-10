(function () {
  if (window.__autoblogContentLoaded) return;
  window.__autoblogContentLoaded = true;

  function parseGeneratedText(rawText) {
    let title = "";
    let body = rawText;
    let tags = "";

    const trimmed = (rawText || "").trim();
    if (trimmed.startsWith("{")) {
      try {
        const data = JSON.parse(trimmed);
        const blog = data.naver_blog || data;
        title = (blog.title || "").trim();
        body = (blog.content || "").trim();
        const tagList = Array.isArray(blog.tags) ? blog.tags : [];
        tags = tagList.join(" ");
        if (tags) body = `${body}\n\n${tags}`;
        return { title, body };
      } catch {
        /* fall through */
      }
    }

    if (rawText.includes("[제목]") && rawText.includes("[본문]")) {
      const afterTitle = rawText.split("[제목]")[1];
      const bodyParts = afterTitle.split("[본문]");
      title = bodyParts[0].trim();
      const rest = bodyParts[1] || "";
      if (rest.includes("[태그]")) {
        const tagParts = rest.split("[태그]");
        body = tagParts[0].trim();
        tags = tagParts[1].trim();
      } else {
        body = rest.trim();
      }
    }

    if (tags) {
      body = `${body}\n\n${tags}`;
    }

    return { title, body };
  }

  function isEditorFrame() {
    return !!(
      document.querySelector(".se-documentTitle") ||
      document.querySelector(".se-main-container") ||
      document.querySelector(".se-content") ||
      document.querySelector("[class*='se-section-documentTitle']")
    );
  }

  function isInTitle(el) {
    if (!el) return true;
    return !!(
      el.closest(".se-documentTitle") ||
      el.closest("[class*='documentTitle']") ||
      el.closest(".se-section-documentTitle")
    );
  }

  function findTitleEditable() {
    const candidates = [
      ".se-documentTitle [contenteditable='true']",
      ".se-section-documentTitle [contenteditable='true']",
      ".se-documentTitle .se-text-paragraph",
      ".se-documentTitle .se-ff-nanumgothic",
      "[class*='se-section-documentTitle'] [contenteditable='true']",
      ".se-title-text",
    ];
    for (const sel of candidates) {
      const el = document.querySelector(sel);
      if (el) return el;
    }
    return null;
  }

  function findBodyEditable() {
    const candidates = [
      ".se-main-container .se-component.se-text .se-component-content [contenteditable='true']",
      ".se-main-container .se-component-content [contenteditable='true']",
      ".se-component.se-text [contenteditable='true']",
      ".se-component-text [contenteditable='true']",
      ".se-section-text [contenteditable='true']",
      ".se-main-container [contenteditable='true']",
      ".se-content [contenteditable='true']",
      ".se-module-text [contenteditable='true']",
    ];
    for (const sel of candidates) {
      const els = document.querySelectorAll(sel);
      for (const el of els) {
        if (isInTitle(el)) continue;
        return el;
      }
    }

    const paragraphs = document.querySelectorAll(
      ".se-main-container .se-text-paragraph, .se-component-text .se-text-paragraph"
    );
    for (const p of paragraphs) {
      if (!isInTitle(p)) return p;
    }
    return null;
  }

  function bodyRoot() {
    return (
      document.querySelector(".se-main-container") ||
      document.querySelector(".se-content") ||
      document.body
    );
  }

  function sampleOf(text) {
    return (text || "").replace(/\s+/g, "").slice(0, 20);
  }

  function verifyInBody(text) {
    const sample = sampleOf(text);
    if (!sample) return true;
    const root = bodyRoot();
    const actual = (root.innerText || root.textContent || "").replace(/\s+/g, "");
    return actual.includes(sample);
  }

  function dispatchEditEvents(el) {
    if (!el) return;
    el.dispatchEvent(new Event("input", { bubbles: true }));
    el.dispatchEvent(new Event("change", { bubbles: true }));
    try {
      el.dispatchEvent(
        new InputEvent("input", {
          bubbles: true,
          cancelable: true,
          inputType: "insertText",
          data: null,
        })
      );
    } catch {
      /* older engines */
    }
  }

  function selectAllIn(el) {
    const selection = window.getSelection();
    if (!selection || !el) return false;
    try {
      const range = document.createRange();
      range.selectNodeContents(el);
      selection.removeAllRanges();
      selection.addRange(range);
      return true;
    } catch {
      return false;
    }
  }

  function placeCaret(el) {
    if (!el) return;
    try {
      el.focus();
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(el);
      range.collapse(true);
      selection.removeAllRanges();
      selection.addRange(range);
    } catch {
      try {
        el.focus();
      } catch {
        /* ignore */
      }
    }
  }

  function clickEl(el) {
    if (!el) return;
    try {
      el.dispatchEvent(
        new MouseEvent("mousedown", { bubbles: true, cancelable: true, view: window })
      );
      el.dispatchEvent(
        new MouseEvent("mouseup", { bubbles: true, cancelable: true, view: window })
      );
      el.click();
    } catch {
      try {
        el.click();
      } catch {
        /* ignore */
      }
    }
  }

  function activateBodyEditor() {
    const hints = [
      ".se-main-container .se-placeholder",
      ".se-component.se-text .se-placeholder",
      ".se-is-empty",
      "[class*='se-placeholder']",
      ".se-main-container",
      ".se-content",
    ];
    for (const sel of hints) {
      const el = document.querySelector(sel);
      if (el && !isInTitle(el)) {
        clickEl(el);
        break;
      }
    }

    // Drop focus off title
    const titleEl = findTitleEditable();
    if (titleEl) {
      try {
        titleEl.blur();
      } catch {
        /* ignore */
      }
    }

    const bodyEl = findBodyEditable();
    if (bodyEl) {
      clickEl(bodyEl);
      placeCaret(bodyEl);
    }
    return bodyEl;
  }

  function pastePlainText(el, text) {
    try {
      const dt = new DataTransfer();
      dt.setData("text/plain", text);
      dt.setData("text/html", text.replace(/\n/g, "<br>"));
      const evt = new ClipboardEvent("paste", {
        bubbles: true,
        cancelable: true,
        clipboardData: dt,
      });
      el.dispatchEvent(evt);
      return true;
    } catch {
      return false;
    }
  }

  function tryExecPaste() {
    try {
      return document.execCommand("paste");
    } catch {
      return false;
    }
  }

  function setEditableText(el, text) {
    if (!el || !text) return false;

    el.scrollIntoView({ block: "center", inline: "nearest" });
    clickEl(el);
    el.focus();

    if (el.tagName === "TEXTAREA" || el.tagName === "INPUT") {
      el.value = text;
      dispatchEditEvents(el);
      return el.value.includes(text.slice(0, 12));
    }

    selectAllIn(el);

    try {
      if (document.execCommand("insertText", false, text)) {
        dispatchEditEvents(el);
        if (verifyInBody(text) || sampleOf(el.textContent).includes(sampleOf(text).slice(0, 12))) {
          return true;
        }
      }
    } catch {
      /* next */
    }

    selectAllIn(el);
    pastePlainText(el, text);
    if (verifyInBody(text)) {
      dispatchEditEvents(el);
      return true;
    }

    try {
      selectAllIn(el);
      document.execCommand("selectAll", false, null);
      document.execCommand("delete", false, null);
      if (document.execCommand("insertText", false, text) && verifyInBody(text)) {
        dispatchEditEvents(el);
        return true;
      }
    } catch {
      /* next */
    }

    const leaf = el.querySelector(".se-ff-nanumgothic, span, p") || el;
    leaf.textContent = text;
    dispatchEditEvents(leaf);
    dispatchEditEvents(el);
    return verifyInBody(text);
  }

  function insertParagraphsViaExec(paragraphs) {
    for (let i = 0; i < paragraphs.length; i++) {
      const ok = document.execCommand("insertText", false, paragraphs[i]);
      if (!ok) return false;
      if (i < paragraphs.length - 1) {
        // Prefer Enter-like breaks SE understands
        if (!document.execCommand("insertParagraph", false, null)) {
          document.execCommand("insertHTML", false, "<br><br>");
        }
      }
    }
    return true;
  }

  function insertParagraphsViaHtml(bodyEl, paragraphs) {
    const html = paragraphs
      .map((p) => `<p>${p.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/\n/g, "<br>")}</p>`)
      .join("");
    try {
      placeCaret(bodyEl);
      if (document.execCommand("insertHTML", false, html)) return true;
    } catch {
      /* next */
    }
    try {
      const host =
        bodyEl.closest("[contenteditable='true']") ||
        bodyEl.closest(".se-component-content") ||
        bodyEl;
      host.innerHTML = paragraphs
        .map(
          (p) =>
            `<p class="se-text-paragraph se-text-paragraph-align-"><span>${p.replace(/\n/g, "<br>")}</span></p>`
        )
        .join("");
      dispatchEditEvents(host);
      return true;
    } catch {
      return false;
    }
  }

  function injectBodyParagraphs(body) {
    if (!body) return false;

    const paragraphs = body.split(/\n\n+/).filter(Boolean);
    if (paragraphs.length === 0) return false;

    let bodyEl = activateBodyEditor();
    if (!bodyEl) {
      bodyEl = findBodyEditable();
    }
    if (!bodyEl) return false;

    // 1) Full text insertText / paste event
    const combined = paragraphs.join("\n\n");
    placeCaret(bodyEl);
    selectAllIn(bodyEl);
    try {
      document.execCommand("delete", false, null);
    } catch {
      /* ignore */
    }

    if (document.execCommand("insertText", false, combined) && verifyInBody(paragraphs[0])) {
      dispatchEditEvents(bodyEl);
      return true;
    }

    // 2) ClipboardEvent paste of full body
    placeCaret(bodyEl);
    pastePlainText(bodyEl, combined);
    if (verifyInBody(paragraphs[0])) {
      dispatchEditEvents(bodyEl);
      return true;
    }

    // 3) Real clipboard paste (sidepanel may have primed clipboard)
    placeCaret(bodyEl);
    if (tryExecPaste() && verifyInBody(paragraphs[0])) {
      dispatchEditEvents(bodyEl);
      return true;
    }

    // 4) Paragraph by paragraph
    bodyEl = activateBodyEditor() || bodyEl;
    placeCaret(bodyEl);
    selectAllIn(bodyEl);
    try {
      document.execCommand("delete", false, null);
    } catch {
      /* ignore */
    }
    if (insertParagraphsViaExec(paragraphs) && verifyInBody(paragraphs[0])) {
      dispatchEditEvents(bodyEl);
      return true;
    }

    // 5) insertHTML / innerHTML
    bodyEl = activateBodyEditor() || bodyEl;
    if (insertParagraphsViaHtml(bodyEl, paragraphs) && verifyInBody(paragraphs[0])) {
      return true;
    }

    // 6) Last resort: set text on first body paragraph leaf
    const leaf =
      bodyEl.querySelector(".se-text-paragraph") ||
      bodyEl.querySelector("span") ||
      bodyEl;
    leaf.textContent = combined;
    dispatchEditEvents(leaf);
    dispatchEditEvents(bodyEl);
    return verifyInBody(paragraphs[0]);
  }

  function injectContent(rawText) {
    if (!isEditorFrame()) {
      return {
        success: false,
        skipped: true,
        titleInjected: false,
        bodyInjected: false,
        message: "에디터 프레임 아님",
      };
    }

    const { title, body } = parseGeneratedText(rawText);
    let titleInjected = false;
    let bodyInjected = false;

    if (title) {
      const titleEl = findTitleEditable();
      titleInjected = setEditableText(titleEl, title);
    } else {
      titleInjected = true;
    }

    if (body) {
      bodyInjected = injectBodyParagraphs(body);
      // Re-check against main container (SE may relocate nodes)
      if (!bodyInjected) {
        bodyInjected = verifyInBody(body);
      }
    } else {
      bodyInjected = true;
    }

    const success = titleInjected && bodyInjected;
    return {
      success,
      skipped: false,
      titleInjected,
      bodyInjected,
      message: success
        ? "주입 완료"
        : !titleInjected && !bodyInjected
          ? "제목·본문 영역을 찾지 못했거나 입력에 실패했습니다."
          : !titleInjected
            ? "제목 영역 주입 실패"
            : "본문 영역 주입 실패",
    };
  }

  window.__autoblogInject = injectContent;
  window.__autoblogParse = parseGeneratedText;

  chrome.runtime.onMessage.addListener((request, _sender, sendResponse) => {
    if (request.action !== "INJECT_CONTENT") return;

    try {
      const result = injectContent(request.text);
      sendResponse(result);
    } catch (e) {
      console.error("[AutoBlog] DOM 주입 에러:", e);
      sendResponse({ success: false, message: e.message });
    }
    return true;
  });
})();
