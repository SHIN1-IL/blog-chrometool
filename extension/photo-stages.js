(function () {
  var STAGES = [
    { id: "start", label: "초반현장" },
    { id: "mid1", label: "중간과정1" },
    { id: "mid2", label: "중간과정2" },
    { id: "mid3", label: "중간과정3" },
    { id: "end", label: "마무리현장" },
  ];
  var STAGE_MAX = 10;
  var TOTAL_MAX = 50;

  function createStore() {
    var photos = {};
    STAGES.forEach(function (stage) {
      photos[stage.id] = [];
    });

    function total() {
      return STAGES.reduce(function (sum, stage) {
        return sum + photos[stage.id].length;
      }, 0);
    }

    function add(stageId, fileList) {
      var stage = photos[stageId];
      var result = { added: 0, skippedStage: 0, skippedTotal: 0, skippedType: 0 };
      if (!stage) return result;
      Array.prototype.forEach.call(fileList || [], function (file) {
        if (!file.type || file.type.indexOf("image/") !== 0) {
          result.skippedType += 1;
          return;
        }
        if (stage.length >= STAGE_MAX) {
          result.skippedStage += 1;
          return;
        }
        if (total() >= TOTAL_MAX) {
          result.skippedTotal += 1;
          return;
        }
        stage.push({
          id: Date.now().toString(36) + Math.random().toString(36).slice(2, 7),
          url: URL.createObjectURL(file),
        });
        result.added += 1;
      });
      return result;
    }

    function remove(stageId, id) {
      var stage = photos[stageId] || [];
      var index = -1;
      for (var i = 0; i < stage.length; i += 1) {
        if (stage[i].id === id) index = i;
      }
      if (index >= 0) {
        URL.revokeObjectURL(stage[index].url);
        stage.splice(index, 1);
      }
    }

    return { photos: photos, add: add, remove: remove, total: total };
  }

  function limitMessage(stageLabel, result) {
    var bits = [];
    if (result.added) bits.push(result.added + "장을 넣었습니다.");
    if (result.skippedStage) {
      bits.push(stageLabel + "은 최대 10장입니다. " + result.skippedStage + "장은 넣지 않았습니다.");
    }
    if (result.skippedTotal) {
      bits.push("전체 50장을 넘겨 " + result.skippedTotal + "장은 넣지 않았습니다.");
    }
    if (result.skippedType) {
      bits.push("사진이 아닌 파일 " + result.skippedType + "개는 제외했습니다.");
    }
    return bits.join(" ");
  }

  function stripPhotoMarkers(text) {
    return String(text || "")
      .replace(/\[현장 사진[^\]]*\]/g, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  function chunksOf(text) {
    var clean = stripPhotoMarkers(text);
    if (!clean) return [];
    var chunks = clean.split(/\n\s*\n/).map(function (part) {
      return part.trim();
    }).filter(Boolean);
    if (chunks.length === 1) {
      var lines = chunks[0].split(/\n/).map(function (line) {
        return line.trim();
      }).filter(Boolean);
      if (lines.length > 1) chunks = lines;
    }
    if (chunks.length === 1 && chunks[0].length > 80) {
      var sentences = [];
      var buf = "";
      var source = chunks[0];
      for (var i = 0; i < source.length; i += 1) {
        buf += source.charAt(i);
        var mark = ".!?。".indexOf(source.charAt(i)) >= 0;
        var boundary = mark && (i + 1 >= source.length || /\s/.test(source.charAt(i + 1)));
        if (boundary) {
          if (buf.trim()) sentences.push(buf.trim());
          buf = "";
        }
      }
      if (buf.trim()) sentences.push(buf.trim());
      if (sentences.length > 1) chunks = sentences;
    }
    return chunks;
  }

  function splitIntoStages(text) {
    var chunks = chunksOf(text);
    var parts = ["", "", "", "", ""];
    if (!chunks.length) return parts;
    var base = Math.floor(chunks.length / STAGES.length);
    var rem = chunks.length % STAGES.length;
    var cursor = 0;
    for (var i = 0; i < STAGES.length; i += 1) {
      var take = base + (rem > 0 ? 1 : 0);
      if (rem > 0) rem -= 1;
      parts[i] = chunks.slice(cursor, cursor + take).join("\n\n");
      cursor += take;
    }
    return parts;
  }

  function blogTextFromRaw(raw, store) {
    if (!store || store.total() === 0) return stripPhotoMarkers(raw);
    var parts = splitIntoStages(raw);
    return STAGES.map(function (stage, index) {
      var count = (store.photos[stage.id] || []).length;
      var lines = ["【" + stage.label + "】"];
      if (parts[index]) lines.push(parts[index]);
      if (count) {
        lines.push(
          "(이 단계 사진 " + count + "장. 화면의 " + stage.label + " 사진을 1번부터 네이버에 첨부하세요.)"
        );
      }
      return lines.join("\n");
    }).join("\n\n");
  }

  function refreshAttach(root, store) {
    var totalEl = root.querySelector("[data-photo-total]");
    if (totalEl) totalEl.textContent = "전체 " + store.total() + "/50";
    STAGES.forEach(function (stage) {
      var list = store.photos[stage.id];
      var countEl = root.querySelector('[data-count="' + stage.id + '"]');
      if (countEl) countEl.textContent = list.length + "/10";
      var thumbs = root.querySelector('[data-thumbs="' + stage.id + '"]');
      if (!thumbs) return;
      thumbs.innerHTML = list.map(function (photo, index) {
        return (
          '<button type="button" class="photo-thumb" data-remove="' + photo.id + '" data-stage="' + stage.id + '">' +
          '<img src="' + photo.url + '" alt="' + stage.label + " " + (index + 1) + '">' +
          "<span>" + (index + 1) + "</span></button>"
        );
      }).join("");
    });
  }

  function renderResult(container, store) {
    if (!container) return;
    if (!store || store.total() === 0) {
      container.hidden = true;
      container.innerHTML = "";
      return;
    }
    container.hidden = false;
    container.innerHTML =
      '<p class="hint">아래 순서대로 네이버에 사진을 첨부하세요. 복사되는 것은 글이고, 사진 파일은 네이버 붙여넣기에 들어가지 않습니다.</p>' +
      STAGES.map(function (stage) {
        var list = store.photos[stage.id];
        var imgs = list.length
          ? list.map(function (photo, index) {
              return (
                '<figure class="photo-thumb photo-thumb-static"><img src="' + photo.url + '" alt="' + stage.label + " " + (index + 1) + '"><figcaption>' + (index + 1) + "</figcaption></figure>"
              );
            }).join("")
          : '<p class="hint">이 단계 사진 없음</p>';
        return '<section class="blog-stage-row"><h3>' + stage.label + "</h3><div class=\"photo-thumbs\">" + imgs + "</div></section>";
      }).join("");
  }

  function bind(root, store, onChange) {
    if (!root || root.dataset.bound === "1") return store;
    root.dataset.bound = "1";
    var msg = root.querySelector("[data-photo-msg]");
    function takeFiles(stageId, fileList, input) {
      var stage = STAGES.filter(function (item) { return item.id === stageId; })[0];
      var result = store.add(stageId, fileList);
      if (input) input.value = "";
      refreshAttach(root, store);
      if (msg) {
        var text = limitMessage(stage ? stage.label : "이 단계", result);
        msg.hidden = !text;
        msg.textContent = text;
      }
      if (onChange) onChange();
    }

    root.addEventListener("change", function (event) {
      var input = event.target;
      if (!input || !input.getAttribute("data-stage-input")) return;
      takeFiles(input.getAttribute("data-stage-input"), input.files, input);
    });

    root.addEventListener("dragover", function (event) {
      var box = event.target.closest ? event.target.closest(".photo-stage") : null;
      if (!box || !root.contains(box)) return;
      event.preventDefault();
      if (event.dataTransfer) event.dataTransfer.dropEffect = "copy";
      box.classList.add("photo-stage-drop");
    });

    root.addEventListener("dragleave", function (event) {
      var box = event.target.closest ? event.target.closest(".photo-stage") : null;
      if (!box || !root.contains(box)) return;
      var next = event.relatedTarget;
      if (next && box.contains(next)) return;
      box.classList.remove("photo-stage-drop");
    });

    root.addEventListener("drop", function (event) {
      var box = event.target.closest ? event.target.closest(".photo-stage") : null;
      if (!box || !root.contains(box)) return;
      event.preventDefault();
      box.classList.remove("photo-stage-drop");
      var input = box.querySelector("[data-stage-input]");
      if (!input || !event.dataTransfer) return;
      takeFiles(input.getAttribute("data-stage-input"), event.dataTransfer.files, null);
    });
    root.addEventListener("click", function (event) {
      var button = event.target.closest ? event.target.closest("[data-remove]") : null;
      if (!button || !root.contains(button)) return;
      store.remove(button.getAttribute("data-stage"), button.getAttribute("data-remove"));
      refreshAttach(root, store);
      if (msg) {
        msg.hidden = true;
        msg.textContent = "";
      }
      if (onChange) onChange();
    });
    refreshAttach(root, store);
    return store;
  }

  window.PhotoStages = {
    createStore: createStore,
    blogTextFromRaw: blogTextFromRaw,
    bind: bind,
    renderResult: renderResult,
    refreshAttach: refreshAttach,
  };
})();
