// Prompt Relay Station Application

const DEFAULT_AIRPORT_IMAGES = [
  {
    id: "img_01",
    filename: "1.png",
    title: "CCTV: Check-in Area A",
    category: "CCTV Surveillance",
    badge: "CAM 03 • Check-in A",
    timestamp: "08:14:23",
    prompt_hint: "Inspect the airline counter transaction. Prompt Agent 1 to read the visible camera timestamp, identify the passenger checking in, describe the luggage item and color, and extract any counter details.",
    description: "Passenger Daniel Kim checks in luggage at airline counter; blue suitcase tagged and dispatched onto conveyor system.",
    src: "/image_data/1.png"
  },
  {
    id: "img_02",
    filename: "2.png",
    title: "CCTV: Gate B07 Corridor",
    category: "CCTV Surveillance",
    badge: "CAM 12 • Gate B07 Corridor",
    timestamp: "08:47:10",
    prompt_hint: "Observe the person moving rapidly through the concourse. Prompt Agent 1 to record the camera timestamp, describe the subject's clothing and appearance, identify the gate signage in view, and note their direction of movement.",
    description: "Unidentified person in dark hooded jacket and gloves captured walking rapidly away from Gate B07 corridor.",
    src: "/image_data/2.png"
  },
  {
    id: "img_03",
    filename: "3.png",
    title: "CCTV: Baggage Handling Area",
    category: "CCTV Surveillance",
    badge: "CAM 21 • Apron Bay",
    timestamp: "09:02:55",
    prompt_hint: "Review ground operations on the apron. Prompt Agent 1 to record the timestamp, observe ramp crew loading actions, and evaluate if this shows routine ground operations or an emergency anomaly.",
    description: "Ramp crew loading checked cargo containers onto apron; routine ground operations.",
    src: "/image_data/3.png"
  },
  {
    id: "img_04",
    filename: "4.png",
    title: "Flight Information Display",
    category: "Flight Monitor",
    badge: "Terminal 1 FIDS",
    timestamp: "08:30:00",
    prompt_hint: "Perform OCR on the digital flight monitor screen. Prompt Agent 1 to extract the system date/time, the flight numbers, destinations, assigned gates, and operational status for Flight SW 472 and adjacent flights.",
    description: "Flight SW 472 to New York listed as 'Boarding' at Gate B07. Other flights on time or delayed.",
    src: "/image_data/4.png"
  },
  {
    id: "img_05",
    filename: "5.png",
    title: "Passenger Messages (Chat)",
    category: "Passenger Chat",
    badge: "WhatsApp Screenshot",
    timestamp: "08:35 - 08:47",
    prompt_hint: "Transcribe the passenger chat thread. Prompt Agent 1 to extract the sender name, message timestamps, and the specific security observation reported regarding unattended property near the gate.",
    description: "Passenger Aarav Mehta messages: 'There\\'s a blue bag near the seats... looks unattended. No passenger in sight.'",
    src: "/image_data/5.png"
  },
  {
    id: "img_06",
    filename: "6.png",
    title: "Security Observation Report",
    category: "Security Log",
    badge: "Officer R. Nair Incident Log",
    timestamp: "08:49:00",
    prompt_hint: "Transcribe the official security observation log. Prompt Agent 1 to extract the report date, logged time, gate location, reporting officer name, physical description of the item found, and the immediate security action taken.",
    description: "Officer R. Nair logs unattended blue suitcase near B07 window seats. Area under observation awaiting K9 explosive sweep.",
    src: "/image_data/6.png"
  },
  {
    id: "img_07",
    filename: "7.png",
    title: "Terminal 1 Departure Map",
    category: "Terminal Layout",
    badge: "Terminal 1 Map",
    timestamp: "Concourse Plan",
    prompt_hint: "Inspect the concourse floor plan. Prompt Agent 1 to identify the position of Gate B07, surrounding passenger gates, and security perimeter boundaries required for cordon procedures.",
    description: "Concourse map showing Gate B07 location, passenger corridors, and restricted apron access doors.",
    src: "/image_data/7.png"
  },
  {
    id: "img_08",
    filename: "8.png",
    title: "Handwritten Note near B07",
    category: "Physical Clue",
    badge: "Paper Scrap",
    timestamp: "Found near B07",
    prompt_hint: "Perform OCR on the paper scrap recovered at the gate. Prompt Agent 1 to extract the exact handwritten message and note the physical location where it was discovered.",
    description: "Slip of paper recovered near Gate B07 seating area with handwritten text: 'Meet at B07'.",
    src: "/image_data/8.png"
  },
  {
    id: "img_09",
    filename: "9.png",
    title: "Baggage Tag: Recovered Luggage",
    category: "Physical Clue",
    badge: "SkyWays Bag Tag",
    timestamp: "Attached to Bag",
    prompt_hint: "Perform detailed OCR on the airline luggage tag attached to the unattended item. Prompt Agent 1 to extract the airline name, passenger full name, assigned flight number, and destination.",
    description: "SkyWays baggage tag on the blue suitcase reading: 'Passenger: Daniel Kim | Flight: SW 472'.",
    src: "/image_data/9.png"
  },
  {
    id: "img_10",
    filename: "10.png",
    title: "Daily Chronicle Newspaper (Decoy)",
    category: "Peripheral Decoy",
    badge: "Daily Chronicle",
    timestamp: "Morning Edition",
    prompt_hint: "Review the newspaper article clipping found in the seating area. Prompt Agent 1 to read the headline and determine whether this material contains operational incident facts or represents irrelevant peripheral noise to filter out.",
    description: "Discarded newspaper article: 'City Marathon Brings Thousands Together'; no relation to flight operations.",
    src: "/image_data/10.png"
  }
];

const state = {
  sessionId: null,
  teamName: "",
  caseId: "case_04_airport_crisis",
  caseTitle: "Airport Crisis: Flight 472 Emergency",
  caseFile: "",
  theme: "Airport Crisis",
  selectedMode: "image",
  images: [...DEFAULT_AIRPORT_IMAGES],
  operationalRules: [],
  user1Prompt: "",
  agent1Output: "",
  user2Prompt: "",
  agent2Output: "",
  user3Prompt: "",
  finalVerdict: null,
  evaluation: null,
  currentAirportFilter: "all",
};

// Active Image Indices
let currentP1ImageIndex = 0;
let currentP2ImageIndex = 0;
let currentP3ImageIndex = 0;
let currentModalImageIndex = 0;

async function loadCases() {
  try {
    const res = await fetch("/api/game/cases");
    if (!res.ok) return;
    const cases = await res.json();
    const caseSelect = document.getElementById("case-select");
    const mysterySelect = document.getElementById("mystery-select");

    if (caseSelect) {
      caseSelect.innerHTML = "";
      cases.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.case_id;
        opt.textContent = `${c.title} (${c.difficulty})`;
        if (c.case_id === "case_04_airport_crisis") opt.selected = true;
        caseSelect.appendChild(opt);
      });
      const randOpt = document.createElement("option");
      randOpt.value = "";
      randOpt.textContent = "🎲 Random Scenario";
      caseSelect.appendChild(randOpt);
    }

    if (mysterySelect) {
      mysterySelect.innerHTML = "";
      const mysteryCases = cases.filter((c) => c.theme !== "Airport Crisis");
      mysteryCases.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.case_id;
        opt.textContent = `${c.title} (${c.difficulty})`;
        mysterySelect.appendChild(opt);
      });
      const randOpt = document.createElement("option");
      randOpt.value = "";
      randOpt.textContent = "🎲 Random Mystery Scenario";
      mysterySelect.appendChild(randOpt);
    }
  } catch (err) {
    console.error("Failed to load cases:", err);
  }
}

function selectStoryMode(mode) {
  state.selectedMode = mode;
  const cardImage = document.getElementById("mode-card-image");
  const cardText = document.getElementById("mode-card-text");
  const badgeImage = document.getElementById("badge-mode-image");
  const badgeText = document.getElementById("badge-mode-text");
  const modeLabel = document.getElementById("mode-selected-label");
  const btnStart = document.getElementById("btn-start-game");
  const btnText = document.getElementById("btn-start-text");
  const caseSelect = document.getElementById("case-select");
  const mysterySelect = document.getElementById("mystery-select");

  if (mode === "image") {
    if (cardImage) {
      cardImage.className = "cursor-pointer rounded-2xl border-2 border-blue-500 bg-blue-950/30 p-4 sm:p-5 transition hover:bg-blue-950/50 flex flex-col justify-between space-y-3 shadow-lg shadow-blue-500/15 ring-1 ring-blue-500/30";
    }
    if (cardText) {
      cardText.className = "cursor-pointer rounded-2xl border border-slate-800 bg-slate-950/70 p-4 sm:p-5 transition hover:bg-slate-800/40 flex flex-col justify-between space-y-3";
    }
    if (badgeImage) badgeImage.className = "w-3.5 h-3.5 rounded-full bg-blue-400 ring-4 ring-blue-500/30";
    if (badgeText) badgeText.className = "w-3.5 h-3.5 rounded-full bg-slate-700";
    if (modeLabel) {
      modeLabel.textContent = "Active: 🖼️ Image-Based Stories";
      modeLabel.className = "text-[11px] font-mono text-blue-400 font-semibold";
    }
    if (caseSelect) caseSelect.value = "case_04_airport_crisis";
    if (btnText) btnText.textContent = "Launch Flight 472 Emergency Operation (Image-Based)";
    if (btnStart) {
      btnStart.className = "w-full py-4 px-6 rounded-xl bg-blue-500 hover:bg-blue-400 text-slate-950 font-extrabold text-sm transition transform active:scale-[0.98] shadow-lg shadow-blue-500/20 flex items-center justify-center gap-2";
    }
  } else {
    if (cardImage) {
      cardImage.className = "cursor-pointer rounded-2xl border border-slate-800 bg-slate-950/70 p-4 sm:p-5 transition hover:bg-slate-800/40 flex flex-col justify-between space-y-3";
    }
    if (cardText) {
      cardText.className = "cursor-pointer rounded-2xl border-2 border-amber-500 bg-amber-950/30 p-4 sm:p-5 transition hover:bg-amber-950/50 flex flex-col justify-between space-y-3 shadow-lg shadow-amber-500/15 ring-1 ring-amber-500/30";
    }
    if (badgeImage) badgeImage.className = "w-3.5 h-3.5 rounded-full bg-slate-700";
    if (badgeText) badgeText.className = "w-3.5 h-3.5 rounded-full bg-amber-400 ring-4 ring-amber-500/30";
    if (modeLabel) {
      modeLabel.textContent = "Active: 📝 Text-Based Stories";
      modeLabel.className = "text-[11px] font-mono text-amber-400 font-semibold";
    }
    if (caseSelect && mysterySelect) caseSelect.value = mysterySelect.value;
    if (btnText) btnText.textContent = "Launch Murder Mystery Investigation (Text-Based)";
    if (btnStart) {
      btnStart.className = "w-full py-4 px-6 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-extrabold text-sm transition transform active:scale-[0.98] shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2";
    }
  }
}

function syncMysteryCase(caseId) {
  const caseSelect = document.getElementById("case-select");
  if (caseSelect) caseSelect.value = caseId;
  selectStoryMode("text");
}

function setupKeyboardShortcuts() {
  const textareas = [
    { id: "step1-prompt-input", action: handleSubmitStep1 },
    { id: "step2-prompt-input", action: handleSubmitStep2 },
    { id: "step3-prompt-input", action: handleSubmitStep3 },
  ];

  textareas.forEach(({ id, action }) => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener("keydown", (e) => {
        if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
          e.preventDefault();
          action();
        }
      });
    }
  });

  document.addEventListener("keydown", (e) => {
    const modal = document.getElementById("modal-image-viewer");
    const isModalOpen = modal && !modal.classList.contains("hidden");

    if (isModalOpen) {
      if (e.key === "Escape") {
        closeImageViewer();
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        prevImage();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        nextImage();
      }
      return;
    }

    // Modal closed: Arrow keys navigate evidence images unless user is typing in input/textarea
    const tag = document.activeElement ? document.activeElement.tagName.toLowerCase() : "";
    if (tag === "textarea" || tag === "input") return;

    const s1 = document.getElementById("screen-step1");
    const s2 = document.getElementById("screen-step2");
    const s3 = document.getElementById("screen-step3");

    if (s1 && !s1.classList.contains("hidden")) {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        prevP1Image();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        nextP1Image();
      }
    } else if (s2 && !s2.classList.contains("hidden")) {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        prevP2Image();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        nextP2Image();
      }
    } else if (s3 && !s3.classList.contains("hidden")) {
      if (e.key === "ArrowLeft") {
        e.preventDefault();
        prevP3Image();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        nextP3Image();
      }
    }
  });
}

function setupEvidenceControls() {
  // Step 1 Controls
  const p1Prev = document.getElementById("p1-btn-prev");
  if (p1Prev) p1Prev.onclick = prevP1Image;
  const p1Next = document.getElementById("p1-btn-next");
  if (p1Next) p1Next.onclick = nextP1Image;
  const p1Zoom = document.getElementById("p1-btn-zoom");
  if (p1Zoom) p1Zoom.onclick = () => openActiveImageViewer(1);

  const p1ImgContainer = document.getElementById("p1-img-container");
  if (p1ImgContainer) p1ImgContainer.onclick = () => openActiveImageViewer(1);
  const p1ArrowPrev = document.getElementById("p1-img-arrow-prev");
  if (p1ArrowPrev) p1ArrowPrev.onclick = (e) => { e.stopPropagation(); prevP1Image(); };
  const p1ArrowNext = document.getElementById("p1-img-arrow-next");
  if (p1ArrowNext) p1ArrowNext.onclick = (e) => { e.stopPropagation(); nextP1Image(); };

  // Step 2 Controls
  const p2Prev = document.getElementById("p2-btn-prev");
  if (p2Prev) p2Prev.onclick = prevP2Image;
  const p2Next = document.getElementById("p2-btn-next");
  if (p2Next) p2Next.onclick = nextP2Image;
  const p2Zoom = document.getElementById("p2-btn-zoom");
  if (p2Zoom) p2Zoom.onclick = () => openActiveImageViewer(2);

  const p2ImgContainer = document.getElementById("p2-img-container");
  if (p2ImgContainer) p2ImgContainer.onclick = () => openActiveImageViewer(2);
  const p2ArrowPrev = document.getElementById("p2-img-arrow-prev");
  if (p2ArrowPrev) p2ArrowPrev.onclick = (e) => { e.stopPropagation(); prevP2Image(); };
  const p2ArrowNext = document.getElementById("p2-img-arrow-next");
  if (p2ArrowNext) p2ArrowNext.onclick = (e) => { e.stopPropagation(); nextP2Image(); };

  // Step 3 Controls
  const p3Prev = document.getElementById("p3-btn-prev");
  if (p3Prev) p3Prev.onclick = prevP3Image;
  const p3Next = document.getElementById("p3-btn-next");
  if (p3Next) p3Next.onclick = nextP3Image;
  const p3Zoom = document.getElementById("p3-btn-zoom");
  if (p3Zoom) p3Zoom.onclick = () => openActiveImageViewer(3);

  const p3ImgContainer = document.getElementById("p3-img-container");
  if (p3ImgContainer) p3ImgContainer.onclick = () => openActiveImageViewer(3);
  const p3ArrowPrev = document.getElementById("p3-img-arrow-prev");
  if (p3ArrowPrev) p3ArrowPrev.onclick = (e) => { e.stopPropagation(); prevP3Image(); };
  const p3ArrowNext = document.getElementById("p3-img-arrow-next");
  if (p3ArrowNext) p3ArrowNext.onclick = (e) => { e.stopPropagation(); nextP3Image(); };

  // Modal Evidence Viewer Controls
  const modalPrev = document.getElementById("modal-btn-prev");
  if (modalPrev) modalPrev.onclick = prevImage;
  const modalNext = document.getElementById("modal-btn-next");
  if (modalNext) modalNext.onclick = nextImage;
  const modalClose = document.getElementById("modal-btn-close");
  if (modalClose) modalClose.onclick = closeImageViewer;

  // Thumbnail strips delegation (supports dynamically re-rendered and static buttons)
  const p1Strip = document.getElementById("p1-thumbnail-strip");
  if (p1Strip) {
    p1Strip.onclick = (e) => {
      const btn = e.target.closest(".p1-thumb-btn");
      if (btn && btn.dataset.index !== undefined) {
        const idx = parseInt(btn.dataset.index, 10);
        if (!isNaN(idx)) setP1ActiveImage(idx);
      }
    };
  }

  const p2Strip = document.getElementById("p2-thumbnail-strip");
  if (p2Strip) {
    p2Strip.onclick = (e) => {
      const btn = e.target.closest(".p2-thumb-btn");
      if (btn && btn.dataset.index !== undefined) {
        const idx = parseInt(btn.dataset.index, 10);
        if (!isNaN(idx)) setP2ActiveImage(idx);
      }
    };
  }

  const p3Strip = document.getElementById("p3-thumbnail-strip");
  if (p3Strip) {
    p3Strip.onclick = (e) => {
      const btn = e.target.closest(".p3-thumb-btn");
      if (btn && btn.dataset.index !== undefined) {
        const idx = parseInt(btn.dataset.index, 10);
        if (!isNaN(idx)) setP3ActiveImage(idx);
      }
    };
  }

  const modalStrip = document.getElementById("modal-thumbnail-strip");
  if (modalStrip) {
    modalStrip.onclick = (e) => {
      const btn = e.target.closest(".modal-thumb-btn");
      if (btn && btn.dataset.index !== undefined) {
        const idx = parseInt(btn.dataset.index, 10);
        if (!isNaN(idx)) {
          currentModalImageIndex = idx;
          renderModalImage();
        }
      }
    };
  }

  // Quick jump pill listeners
  document.querySelectorAll(".p1-quick-jump-btn").forEach((btn) => {
    btn.onclick = (e) => {
      e.stopPropagation();
      const idx = parseInt(btn.dataset.index, 10);
      if (!isNaN(idx)) setP1ActiveImage(idx);
    };
  });

  // Filter tab listeners
  document.querySelectorAll(".airport-filter-btn").forEach((btn) => {
    btn.onclick = () => {
      const filter = btn.dataset.filter || "all";
      filterAirportEvidence(filter);
    };
  });
}

// ========================================================
// SCREEN & MODAL MANAGEMENT
// ========================================================

function showScreen(screenId) {
  const screens = ["screen-welcome", "screen-step1", "screen-step2", "screen-step3", "screen-results"];
  screens.forEach((id) => {
    const el = document.getElementById(id);
    if (el) {
      if (id === screenId) {
        el.classList.remove("hidden");
      } else {
        el.classList.add("hidden");
      }
    }
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function showModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.remove("hidden");
}

function hideModal(modalId) {
  const el = document.getElementById(modalId);
  if (el) el.classList.add("hidden");
}

function showLoading(text = "Running Agent...") {
  const overlay = document.getElementById("loading-overlay");
  const textEl = document.getElementById("loading-text");
  if (textEl) textEl.textContent = text;
  if (overlay) overlay.classList.remove("hidden");
}

function hideLoading() {
  const overlay = document.getElementById("loading-overlay");
  if (overlay) overlay.classList.add("hidden");
}

function showError(msg) {
  const banner = document.getElementById("error-banner");
  const msgEl = document.getElementById("error-message");
  if (msgEl) msgEl.textContent = msg;
  if (banner) banner.classList.remove("hidden");
}

function dismissError() {
  const banner = document.getElementById("error-banner");
  if (banner) banner.classList.add("hidden");
}

async function getErrorMessage(res) {
  try {
    const text = await res.text();
    try {
      const json = JSON.parse(text);
      return json.detail || text;
    } catch {
      return text || `Server error (${res.status})`;
    }
  } catch {
    return `Server error (${res.status})`;
  }
}

// ========================================================
// VISUAL EVIDENCE & OPERATIONAL RULES HELPERS
// ========================================================

function resolveImgSrc(src) {
  if (!src) return "";
  if (window.location.protocol === "file:") {
    const filename = src.split("/").pop();
    return `../image_data/${filename}`;
  }
  return src;
}

function insertExamplePrompt(step) {
  const isImageBased = (state.images && state.images.length > 0) || state.theme === "Airport Crisis" || (state.caseId && state.caseId.includes("airport"));

  if (step === 1) {
    const el = document.getElementById("step1-prompt-input");
    if (!el) return;
    if (isImageBased) {
      el.value = "Extract verified facts from the provided visual evidence feeds for Flight SW 472. Direct the agent to read camera timestamps, identify individuals and personnel, note baggage items and tags, record terminal locations, and log observed movements. Distinguish confirmed visual evidence from unverified sightings or distractions. Do not infer causes or declare final operational actions.";
    } else {
      el.value = "Extract all verified facts, movements, and physical evidence chronologically. Include times and alibis, but ignore coffee orders and rumors. Do not accuse any suspect.";
    }
    el.focus();
  } else if (step === 2) {
    const el = document.getElementById("step2-prompt-input");
    if (!el) return;
    if (isImageBased) {
      el.value = "Using the extracted evidence and surveillance photos, reconstruct the Flight SW 472 incident timeline minute-by-minute in chronological sequence. Connect passenger movements, gate boarding announcements, and the unattended baggage discovery while separating confirmed dependencies from uncertain ones. Do not declare final operational actions.";
    } else {
      el.value = "Construct an objective, minute-by-minute timeline from this evidence. Order events strictly by timestamp. Do NOT name any suspect as the murderer.";
    }
    el.focus();
  } else if (step === 3) {
    const el = document.getElementById("step3-prompt-input");
    if (!el) return;
    if (isImageBased) {
      el.value = "Using the reconstructed incident sequence and airport operational rules (SEC-101, OPS-204, CLR-305), determine the valid operational action for Flight SW 472. Identify supporting rules, the current blocking condition, and requirements before operations can resume. Output strictly valid JSON with keys: culprit, method, clue.";
    } else {
      el.value = "Based on the timeline, determine who committed the murder, their exact method, and the smoking gun clue. Output strictly valid JSON with keys: culprit, method, clue.";
    }
    el.focus();
  }
}

function getCategoryBadgeClass(category) {
  switch (category) {
    case "CCTV Surveillance":
      return "bg-blue-500/20 text-blue-300 border border-blue-500/40";
    case "Flight Monitor":
      return "bg-cyan-500/20 text-cyan-300 border border-cyan-500/40";
    case "Passenger Chat":
      return "bg-indigo-500/20 text-indigo-300 border border-indigo-500/40";
    case "Security Log":
      return "bg-amber-500/20 text-amber-300 border border-amber-500/40";
    case "Terminal Layout":
      return "bg-teal-500/20 text-teal-300 border border-teal-500/40";
    case "Physical Clue":
      return "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40";
    case "Peripheral Decoy":
      return "bg-purple-500/20 text-purple-300 border border-purple-500/40";
    default:
      return "bg-slate-800 text-slate-300 border border-slate-700";
  }
}

// ========================================================
// STEP 1: ACTIVE IMAGE & THUMBNAILS (PLAYER 1)
// ========================================================

function isImageInFilter(img, filterCategory) {
  if (!filterCategory || filterCategory === "all") return true;
  if (filterCategory === "CCTV Surveillance") return img.category === "CCTV Surveillance";
  if (filterCategory === "Flight & Chat") return img.category === "Flight Monitor" || img.category === "Passenger Chat";
  if (filterCategory === "Security & Report") return img.category === "Security Log";
  if (filterCategory === "Physical & Layout") {
    return img.category === "Terminal Layout" || img.category === "Physical Clue" || img.category === "Peripheral Decoy";
  }
  return true;
}

function setP1ActiveImage(index) {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;

  currentP1ImageIndex = (index + images.length) % images.length;
  const img = images[currentP1ImageIndex];
  if (!img) return;

  const numEl = document.getElementById("p1-active-num");
  const totalEl = document.getElementById("p1-total-num");
  const badgeEl = document.getElementById("p1-active-badge");
  const titleEl = document.getElementById("p1-active-title");
  const filenameEl = document.getElementById("p1-active-filename");
  const imgEl = document.getElementById("p1-active-img");
  const hintEl = document.getElementById("p1-active-hint");

  if (numEl) numEl.textContent = currentP1ImageIndex + 1;
  if (totalEl) totalEl.textContent = images.length;
  if (badgeEl) {
    badgeEl.textContent = img.badge || img.category || "Visual Feed";
    badgeEl.className = `px-2 py-0.5 rounded text-[10px] font-mono font-bold truncate ${getCategoryBadgeClass(img.category)}`;
  }
  if (titleEl) titleEl.textContent = img.title || "Visual Evidence";
  if (filenameEl) filenameEl.textContent = img.filename || "";
  if (imgEl) imgEl.src = resolveImgSrc(img.src);
  if (hintEl) {
    hintEl.textContent = img.prompt_hint || "Inspect this surveillance capture closely. Direct Agent 1 to read the visible camera timestamp, identify people, extract objects, and log movements visible in the photo.";
  }

  // Highlight active thumbnail in strip
  const thumbs = document.querySelectorAll(".p1-thumb-btn");
  thumbs.forEach((btn) => {
    const isAct = parseInt(btn.dataset.index, 10) === currentP1ImageIndex;
    if (isAct) {
      btn.className = "p1-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl border-2 border-blue-400 ring-2 ring-blue-500/40 bg-slate-900 transition shadow-lg text-left p-1.5 space-y-1";
    } else {
      btn.className = "p1-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 hover:border-blue-500/50 opacity-75 hover:opacity-100 transition shadow text-left p-1.5 space-y-1";
    }
  });

  // Highlight quick-jump pill button
  const pills = document.querySelectorAll(".p1-quick-jump-btn");
  pills.forEach((pill) => {
    const isAct = parseInt(pill.dataset.index, 10) === currentP1ImageIndex;
    if (isAct) {
      pill.className = "p1-quick-jump-btn px-2 py-0.5 rounded bg-blue-500 text-slate-950 font-bold font-mono text-[11px] shadow-sm cursor-pointer";
    } else {
      pill.className = "p1-quick-jump-btn px-2 py-0.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 font-mono text-[11px] transition cursor-pointer";
    }
  });
}

function prevP1Image() {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;

  if (state.currentAirportFilter && state.currentAirportFilter !== "all") {
    const matchingIndices = [];
    images.forEach((img, idx) => {
      if (isImageInFilter(img, state.currentAirportFilter)) matchingIndices.push(idx);
    });
    if (matchingIndices.length > 0) {
      const currPos = matchingIndices.indexOf(currentP1ImageIndex);
      const prevPos = currPos <= 0 ? matchingIndices.length - 1 : currPos - 1;
      setP1ActiveImage(matchingIndices[prevPos]);
      return;
    }
  }

  setP1ActiveImage(currentP1ImageIndex - 1);
}

function nextP1Image() {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;

  if (state.currentAirportFilter && state.currentAirportFilter !== "all") {
    const matchingIndices = [];
    images.forEach((img, idx) => {
      if (isImageInFilter(img, state.currentAirportFilter)) matchingIndices.push(idx);
    });
    if (matchingIndices.length > 0) {
      const currPos = matchingIndices.indexOf(currentP1ImageIndex);
      const nextPos = (currPos + 1) % matchingIndices.length;
      setP1ActiveImage(matchingIndices[nextPos]);
      return;
    }
  }

  setP1ActiveImage(currentP1ImageIndex + 1);
}

function renderP1Thumbnails(filterCategory = "all") {
  const container = document.getElementById("p1-thumbnail-strip");
  if (!container) return;

  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;

  container.innerHTML = "";

  images.forEach((img, idx) => {
    const match = isImageInFilter(img, filterCategory);
    if (!match) return;

    const isActive = idx === currentP1ImageIndex;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.index = idx;
    btn.className = `p1-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl ${
      isActive ? 'border-2 border-blue-400 ring-2 ring-blue-500/40 bg-slate-900' : 'border border-slate-800 bg-slate-950/80 hover:border-blue-500/50 opacity-75 hover:opacity-100'
    } transition shadow text-left p-1.5 space-y-1`;
    btn.onclick = () => setP1ActiveImage(idx);

    const imgSrc = resolveImgSrc(img.src);
    btn.innerHTML = `
      <div class="aspect-[2/1] w-full overflow-hidden rounded bg-slate-950 flex items-center justify-center">
        <img src="${imgSrc}" alt="${escapeHtml(img.title)}" class="h-full w-full object-cover group-hover:scale-105 transition" onerror="this.onerror=null; this.src='../image_data/' + this.src.split('/').pop();" loading="lazy">
      </div>
      <div class="truncate text-[10px] font-mono text-slate-300 font-semibold leading-tight">
        ${idx + 1}. ${escapeHtml(img.badge || img.title)}
      </div>
    `;
    container.appendChild(btn);
  });
}

function filterAirportEvidence(category) {
  state.currentAirportFilter = category;
  const buttons = document.querySelectorAll(".airport-filter-btn");
  buttons.forEach((btn) => {
    if (btn.dataset.filter === category) {
      btn.className = "airport-filter-btn px-2.5 py-1 rounded-lg bg-blue-500 text-slate-950 font-bold transition shadow-sm cursor-pointer";
    } else {
      btn.className = "airport-filter-btn px-2.5 py-1 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-300 border border-slate-800 transition cursor-pointer";
    }
  });

  renderP1Thumbnails(category);

  // Switch active image to the first matching image of that category so the user immediately sees the change!
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (category !== "all") {
    const firstMatchIdx = images.findIndex((img) => isImageInFilter(img, category));
    if (firstMatchIdx !== -1) {
      setP1ActiveImage(firstMatchIdx);
    }
  }
}

// ========================================================
// STEP 2: ACTIVE SEQUENCE & THUMBNAILS (PLAYER 2)
// ========================================================

const p2SequenceSteps = [
  {
    id: "img_01",
    stepNum: "1",
    stepBadge: "Seq Feed 1 • Check-in A",
    stepTime: "Read Feed Timestamp",
    stepTitle: "Check-in Conveyor Dispatch",
    promptHint: "Examine the camera timestamp and initial luggage handling. Direct Agent 2 to place this transaction as the start of the custody timeline."
  },
  {
    id: "img_04",
    stepNum: "2",
    stepBadge: "Seq Feed 2 • Concourse FIDS",
    stepTime: "Read Monitor Timestamp",
    stepTitle: "Gate Boarding Announcement",
    promptHint: "Note the boarding status and time on the flight monitor. Direct Agent 2 to link this event chronologically with passenger gate activity."
  },
  {
    id: "img_05",
    stepNum: "3",
    stepBadge: "Seq Feed 3 • Passenger Chat",
    stepTime: "Read Chat Timestamp",
    stepTitle: "Unattended Baggage Discovery",
    promptHint: "Observe the timestamp when the passenger first reported the bag. Direct Agent 2 to sequence this immediately following the boarding call."
  },
  {
    id: "img_02",
    stepNum: "4",
    stepBadge: "Seq Feed 4 • Corridor B",
    stepTime: "Read Camera Timestamp",
    stepTitle: "Subject Movement near B07",
    promptHint: "Inspect the camera timestamp and observe the subject's movement. Direct Agent 2 to place this departure directly after the bag discovery."
  },
  {
    id: "img_06",
    stepNum: "5",
    stepBadge: "Seq Feed 5 • Security Log",
    stepTime: "Read Report Log Time",
    stepTitle: "Security Incident Response",
    promptHint: "Note when the security officer logged the incident and cordoned the area. Direct Agent 2 to place this as the trigger for security hold procedures."
  },
  {
    id: "img_09",
    stepNum: "6",
    stepBadge: "Seq Feed 6 • Luggage Tag",
    stepTime: "Physical Evidence Match",
    stepTitle: "Baggage Ownership Link",
    promptHint: "Examine the tag recovered from the unattended bag. Direct Agent 2 to link this physical evidence back to the passenger from the initial check-in."
  }
];

function setP2ActiveImage(index) {
  currentP2ImageIndex = (index + p2SequenceSteps.length) % p2SequenceSteps.length;
  const seq = p2SequenceSteps[currentP2ImageIndex];
  if (!seq) return;

  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  const img = images.find((i) => i.id === seq.id || i.filename?.includes(seq.id)) || images[0];

  const numEl = document.getElementById("p2-active-num");
  const badgeEl = document.getElementById("p2-active-badge");
  const titleEl = document.getElementById("p2-active-title");
  const timeEl = document.getElementById("p2-active-time");
  const imgEl = document.getElementById("p2-active-img");
  const hintEl = document.getElementById("p2-active-hint");

  if (numEl) numEl.textContent = seq.stepNum;
  if (badgeEl) badgeEl.textContent = seq.stepBadge;
  if (titleEl) titleEl.textContent = seq.stepTitle;
  if (timeEl) timeEl.textContent = seq.stepTime;
  if (imgEl && img) imgEl.src = resolveImgSrc(img.src);
  if (hintEl) hintEl.textContent = seq.promptHint;

  // Highlight active thumbnail
  const thumbs = document.querySelectorAll(".p2-thumb-btn");
  thumbs.forEach((btn, idx) => {
    const isAct = idx === currentP2ImageIndex;
    if (isAct) {
      btn.className = "p2-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl border-2 border-purple-400 ring-2 ring-purple-500/40 bg-slate-900 transition shadow-lg text-left p-1.5 space-y-1";
    } else {
      btn.className = "p2-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 hover:border-purple-500/50 opacity-75 hover:opacity-100 transition shadow text-left p-1.5 space-y-1";
    }
  });
}

function prevP2Image() {
  setP2ActiveImage(currentP2ImageIndex - 1);
}

function nextP2Image() {
  setP2ActiveImage(currentP2ImageIndex + 1);
}

function renderP2Thumbnails() {
  const container = document.getElementById("p2-thumbnail-strip");
  if (!container) return;
  container.innerHTML = "";

  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;

  p2SequenceSteps.forEach((seq, idx) => {
    const img = images.find((i) => i.id === seq.id || i.filename?.includes(seq.id)) || images[0];
    const imgSrc = img ? resolveImgSrc(img.src) : "";
    const isActive = idx === currentP2ImageIndex;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.index = idx;
    btn.className = `p2-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl ${
      isActive ? 'border-2 border-purple-400 ring-2 ring-purple-500/40 bg-slate-900' : 'border border-slate-800 bg-slate-950/80 hover:border-purple-500/50 opacity-75 hover:opacity-100'
    } transition shadow text-left p-1.5 space-y-1`;
    btn.onclick = () => setP2ActiveImage(idx);

    btn.innerHTML = `
      <div class="aspect-[2/1] w-full overflow-hidden rounded bg-slate-950 flex items-center justify-center">
        <img src="${imgSrc}" alt="${escapeHtml(seq.stepTitle)}" class="h-full w-full object-cover group-hover:scale-105 transition" loading="lazy">
      </div>
      <div class="truncate text-[10px] font-mono text-purple-300 font-bold">
        Step ${seq.stepNum}
      </div>
    `;
    container.appendChild(btn);
  });
}

// ========================================================
// STEP 3: ACTIVE CLUES & THUMBNAILS (PLAYER 3)
// ========================================================

const p3DecisiveClues = [
  {
    id: "img_06",
    clueNum: "1",
    clueTag: "🚨 Blocking Condition",
    clueTitle: "Security Officer Incident Report",
    tagBadge: "Rule SEC-101",
    promptHint: "Review the officer's logged action and pending requirement. Prompt Agent 3 to evaluate what specific safety unit must clear the bag before operations resume."
  },
  {
    id: "img_09",
    clueNum: "2",
    clueTag: "🏷️ Owner Match",
    clueTitle: "Baggage Identification Tag",
    tagBadge: "Passenger Identity",
    promptHint: "Examine the tag on the unattended suitcase. Prompt Agent 3 to identify the passenger and determine whether the owner is accounted for."
  },
  {
    id: "img_04",
    clueNum: "3",
    clueTag: "✈️ Boarding Action",
    clueTitle: "Flight Display Status",
    tagBadge: "Rule OPS-204",
    promptHint: "Review the current boarding status of Flight SW 472. Prompt Agent 3 to determine whether pre-departure clearance must be suspended under Rule OPS-204."
  },
  {
    id: "img_07",
    clueNum: "4",
    clueTag: "🗺️ Concourse Perimeter",
    clueTitle: "Terminal Concourse Layout Map",
    tagBadge: "Rule CLR-305",
    promptHint: "Inspect the concourse isolation perimeter around Gate B07. Prompt Agent 3 to verify cordon boundaries required under Rule SEC-101."
  }
];

function setP3ActiveImage(index) {
  currentP3ImageIndex = (index + p3DecisiveClues.length) % p3DecisiveClues.length;
  const clue = p3DecisiveClues[currentP3ImageIndex];
  if (!clue) return;

  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  const img = images.find((i) => i.id === clue.id || i.filename?.includes(clue.id)) || images[0];

  const numEl = document.getElementById("p3-active-num");
  const badgeEl = document.getElementById("p3-active-badge");
  const titleEl = document.getElementById("p3-active-title");
  const tagEl = document.getElementById("p3-active-tag");
  const imgEl = document.getElementById("p3-active-img");
  const hintEl = document.getElementById("p3-active-hint");

  if (numEl) numEl.textContent = clue.clueNum;
  if (badgeEl) badgeEl.textContent = clue.clueTag;
  if (titleEl) titleEl.textContent = clue.clueTitle;
  if (tagEl) tagEl.textContent = clue.tagBadge;
  if (imgEl && img) imgEl.src = resolveImgSrc(img.src);
  if (hintEl) hintEl.textContent = clue.promptHint;

  // Highlight active thumbnail
  const thumbs = document.querySelectorAll(".p3-thumb-btn");
  thumbs.forEach((btn, idx) => {
    const isAct = idx === currentP3ImageIndex;
    if (isAct) {
      btn.className = "p3-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl border-2 border-emerald-400 ring-2 ring-emerald-500/40 bg-slate-900 transition shadow-lg text-left p-1.5 space-y-1";
    } else {
      btn.className = "p3-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 hover:border-emerald-500/50 opacity-75 hover:opacity-100 transition shadow text-left p-1.5 space-y-1";
    }
  });
}

function prevP3Image() {
  setP3ActiveImage(currentP3ImageIndex - 1);
}

function nextP3Image() {
  setP3ActiveImage(currentP3ImageIndex + 1);
}

function renderP3Thumbnails() {
  const container = document.getElementById("p3-thumbnail-strip");
  if (!container) return;
  container.innerHTML = "";

  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;

  p3DecisiveClues.forEach((clue, idx) => {
    const img = images.find((i) => i.id === clue.id || i.filename?.includes(clue.id)) || images[0];
    const imgSrc = img ? resolveImgSrc(img.src) : "";
    const isActive = idx === currentP3ImageIndex;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.dataset.index = idx;
    btn.className = `p3-thumb-btn group relative cursor-pointer overflow-hidden rounded-xl ${
      isActive ? 'border-2 border-emerald-400 ring-2 ring-emerald-500/40 bg-slate-900' : 'border border-slate-800 bg-slate-950/80 hover:border-emerald-500/50 opacity-75 hover:opacity-100'
    } transition shadow text-left p-1.5 space-y-1`;
    btn.onclick = () => setP3ActiveImage(idx);

    btn.innerHTML = `
      <div class="aspect-[2/1] w-full overflow-hidden rounded bg-slate-950 flex items-center justify-center">
        <img src="${imgSrc}" alt="${escapeHtml(clue.clueTitle)}" class="h-full w-full object-cover group-hover:scale-105 transition" loading="lazy">
      </div>
      <div class="truncate text-[10px] font-mono text-emerald-300 font-bold">
        ${escapeHtml(clue.clueTag)}
      </div>
    `;
    container.appendChild(btn);
  });
}

function openActiveImageViewer(step) {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;

  if (step === 1) {
    openImageViewerByIndex(currentP1ImageIndex);
  } else if (step === 2) {
    const seq = p2SequenceSteps[currentP2ImageIndex];
    const origIdx = images.findIndex((i) => i.id === seq?.id || i.filename?.includes(seq?.id));
    openImageViewerByIndex(origIdx >= 0 ? origIdx : 0);
  } else if (step === 3) {
    const clue = p3DecisiveClues[currentP3ImageIndex];
    const origIdx = images.findIndex((i) => i.id === clue?.id || i.filename?.includes(clue?.id));
    openImageViewerByIndex(origIdx >= 0 ? origIdx : 0);
  }
}

function renderVisualReferenceStrip(images, containerId, stripId, countId) {
  const container = document.getElementById(containerId);
  const strip = document.getElementById(stripId);
  const countEl = document.getElementById(countId);
  if (!container || !strip) return;

  const validImages = (images && images.length > 0) ? images : DEFAULT_AIRPORT_IMAGES;
  if (!validImages || validImages.length === 0) {
    container.classList.add("hidden");
    strip.innerHTML = "";
    return;
  }

  container.classList.remove("hidden");
  if (countEl) countEl.textContent = validImages.length;
  strip.innerHTML = "";

  validImages.forEach((img, idx) => {
    const item = document.createElement("div");
    item.className = "group cursor-pointer overflow-hidden rounded-xl border border-slate-800 bg-slate-950/80 hover:border-purple-400/60 transition p-2 flex flex-col space-y-1.5 shadow-sm";
    item.onclick = () => openImageViewerByIndex(idx);

    item.innerHTML = `
      <div class="aspect-[2/1] w-full overflow-hidden rounded bg-slate-900 relative">
        <img src="${resolveImgSrc(img.src)}" alt="${escapeHtml(img.title)}" class="h-full w-full object-cover transition-transform group-hover:scale-105" loading="lazy">
        <div class="absolute inset-0 bg-purple-500/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
      </div>
      <div class="flex items-center justify-between text-[10px] font-mono text-slate-400">
        <span class="truncate font-semibold text-slate-200">${escapeHtml(img.title)}</span>
        <span class="text-blue-400 shrink-0 ml-1">${escapeHtml(img.badge || img.category || 'Feed')}</span>
      </div>
    `;
    strip.appendChild(item);
  });
}

function openImageViewerByIndex(index) {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;
  currentModalImageIndex = (index + images.length) % images.length;
  renderModalImage();
  const modal = document.getElementById("modal-image-viewer");
  if (modal) modal.classList.remove("hidden");
}

function renderModalImage() {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;
  const img = images[currentModalImageIndex];
  if (!img) return;

  const srcEl = document.getElementById("modal-image-src");
  const titleEl = document.getElementById("modal-image-title");
  const badgeEl = document.getElementById("modal-image-badge");
  const timeEl = document.getElementById("modal-image-time");
  const descEl = document.getElementById("modal-image-desc");
  const metaEl = document.getElementById("modal-image-meta");
  const counterEl = document.getElementById("modal-image-counter");

  if (srcEl) srcEl.src = resolveImgSrc(img.src);
  if (titleEl) titleEl.textContent = img.title || "Visual Evidence";
  if (badgeEl) badgeEl.textContent = img.badge || img.category || "Visual Feed";
  if (timeEl) timeEl.textContent = `Feed ID: ${(img.id || '').toUpperCase()}`;
  if (descEl) descEl.textContent = img.prompt_hint || "Inspect this visual evidence capture closely to extract verified facts.";
  if (metaEl) metaEl.textContent = `Source File: ${img.filename || ''}`;
  if (counterEl) counterEl.textContent = `${currentModalImageIndex + 1} of ${images.length}`;

  renderModalThumbnails();
}

function prevImage() {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;
  currentModalImageIndex = (currentModalImageIndex - 1 + images.length) % images.length;
  renderModalImage();
}

function nextImage() {
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!images || images.length === 0) return;
  currentModalImageIndex = (currentModalImageIndex + 1) % images.length;
  renderModalImage();
}

function closeImageViewer() {
  const modal = document.getElementById("modal-image-viewer");
  if (modal) modal.classList.add("hidden");
}

function renderModalThumbnails() {
  const strip = document.getElementById("modal-thumbnail-strip");
  const images = (state.images && state.images.length > 0) ? state.images : DEFAULT_AIRPORT_IMAGES;
  if (!strip || !images || images.length === 0) return;
  strip.innerHTML = "";

  images.forEach((img, idx) => {
    const thumb = document.createElement("button");
    thumb.type = "button";
    thumb.dataset.index = idx;
    const isActive = idx === currentModalImageIndex;
    thumb.className = `modal-thumb-btn shrink-0 rounded-lg overflow-hidden border-2 transition ${
      isActive ? 'border-blue-400 ring-2 ring-blue-500/40 opacity-100 scale-105' : 'border-slate-800 opacity-60 hover:opacity-100'
    } w-16 h-10 bg-slate-950 cursor-pointer`;
    thumb.onclick = (e) => {
      e.stopPropagation();
      currentModalImageIndex = idx;
      renderModalImage();
    };
    thumb.innerHTML = `<img src="${resolveImgSrc(img.src)}" alt="${escapeHtml(img.title)}" class="w-full h-full object-cover">`;
    strip.appendChild(thumb);
  });
}

// Early window exports for core image viewer & navigation controls
window.setP1ActiveImage = setP1ActiveImage;
window.prevP1Image = prevP1Image;
window.nextP1Image = nextP1Image;
window.setP2ActiveImage = setP2ActiveImage;
window.prevP2Image = prevP2Image;
window.nextP2Image = nextP2Image;
window.setP3ActiveImage = setP3ActiveImage;
window.prevP3Image = prevP3Image;
window.nextP3Image = nextP3Image;
window.openActiveImageViewer = openActiveImageViewer;
window.openImageViewerByIndex = openImageViewerByIndex;
window.prevImage = prevImage;
window.nextImage = nextImage;
window.closeImageViewer = closeImageViewer;
window.renderP1Thumbnails = renderP1Thumbnails;
window.renderP2Thumbnails = renderP2Thumbnails;
window.renderP3Thumbnails = renderP3Thumbnails;

function renderOperationalRules(rules) {
  const container = document.getElementById("step3-rules-container");
  const listEl = document.getElementById("step3-rules-list");
  if (!container || !listEl) return;

  if (!rules || rules.length === 0) {
    container.classList.add("hidden");
    listEl.innerHTML = "";
    return;
  }

  container.classList.remove("hidden");
  listEl.innerHTML = rules.map((r) => `
    <div class="p-2.5 rounded-lg bg-slate-950/70 border border-emerald-500/20 text-xs text-slate-200 font-mono leading-relaxed flex items-start gap-2">
      <span class="text-emerald-400 font-bold shrink-0 mt-0.5">▶</span>
      <span>${escapeHtml(r)}</span>
    </div>
  `).join("");
}

// ========================================================
// WIZARD ACTIONS
// ========================================================

async function handleStartGame() {
  dismissError();
  const teamInput = document.getElementById("team-name-input");
  const caseSelect = document.getElementById("case-select");

  const teamName = teamInput.value.trim();
  if (!teamName) {
    showError("Please enter a team name before starting.");
    teamInput.focus();
    return;
  }

  const selectedCaseId = caseSelect.value || null;

  showLoading("Initializing mission session...");

  try {
    const res = await fetch("/api/game/start", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ team_name: teamName, case_id: selectedCaseId }),
    });

    if (!res.ok) {
      const errorMsg = await getErrorMessage(res);
      throw new Error(errorMsg);
    }

    const data = await res.json();
    state.sessionId = data.session_id;
    state.teamName = data.team_name;
    state.caseId = data.case_id;
    state.caseTitle = data.case_title;
    state.caseFile = data.case_file;
    state.theme = data.theme || "Murder Mystery";
    state.images = data.images || [];
    state.operationalRules = data.operational_rules || [];

    // Update Header
    document.getElementById("active-team-name").textContent = state.teamName;
    document.getElementById("active-case-title").textContent = state.caseTitle;
    document.getElementById("header-match-info").classList.remove("hidden");

    // Dynamic Board Layout based on Theme
    const isImageBased = (state.images && state.images.length > 0) || state.theme === "Airport Crisis" || (state.caseId && state.caseId.includes("airport"));
    const airportBoard = document.getElementById("step1-airport-board");
    const mysteryBoard = document.getElementById("step1-mystery-board");
    const p1Input = document.getElementById("step1-prompt-input");

    if (isImageBased) {
      if (airportBoard) airportBoard.classList.remove("hidden");
      if (mysteryBoard) mysteryBoard.classList.add("hidden");
      
      setP1ActiveImage(0);
      renderP1Thumbnails("all");
      
      if (p1Input) {
        p1Input.placeholder = "e.g. Extract verified facts from the provided visual evidence for Flight SW 472. Identify key people, objects, times, locations, movements, and observations. Distinguish confirmed facts from uncertain information and ignore irrelevant marathon news. Do not infer causes or final actions.";
        p1Input.value = "";
      }
    } else {
      if (airportBoard) airportBoard.classList.add("hidden");
      if (mysteryBoard) mysteryBoard.classList.remove("hidden");
      
      const caseFileEl = document.getElementById("step1-case-file");
      if (caseFileEl) caseFileEl.textContent = state.caseFile;
      
      if (p1Input) {
        p1Input.placeholder = "e.g. Extract all verified facts, movements, and physical evidence chronologically. Include times and alibis, but ignore coffee orders and rumors.";
        p1Input.value = "";
      }
    }

    hideLoading();
    showScreen("screen-step1");
  } catch (err) {
    hideLoading();
    showError(err.message);
  }
}

async function handleSubmitStep1() {
  dismissError();
  const promptInput = document.getElementById("step1-prompt-input");
  const prompt = promptInput.value.trim();

  if (!prompt) {
    showError("Please enter instructions for Agent 1 (Evidence Extractor).");
    promptInput.focus();
    return;
  }

  showLoading("Agent 1 is filtering the case file...");

  try {
    const res = await fetch("/api/game/step1", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, user_1_prompt: prompt }),
    });

    if (!res.ok) {
      const errorMsg = await getErrorMessage(res);
      throw new Error(errorMsg);
    }

    const data = await res.json();
    state.user1Prompt = prompt;
    state.agent1Output = data.agent_1_output;

    hideLoading();
    showModal("modal-handoff1");
  } catch (err) {
    hideLoading();
    showError(err.message);
  }
}

function handleAcknowledgeHandoff1() {
  hideModal("modal-handoff1");
  // Player 2 sees Agent 1's extracted facts
  document.getElementById("step2-agent1-output").textContent = state.agent1Output;
  
  const isImageBased = (state.images && state.images.length > 0) || state.theme === "Airport Crisis" || (state.caseId && state.caseId.includes("airport"));
  const p2Input = document.getElementById("step2-prompt-input");
  const p2AirportBoard = document.getElementById("step2-airport-board");
  const p2MysteryTip = document.getElementById("step2-mystery-tip");

  if (isImageBased) {
    if (p2AirportBoard) p2AirportBoard.classList.remove("hidden");
    if (p2MysteryTip) p2MysteryTip.classList.add("hidden");
    setP2ActiveImage(0);
    renderP2Thumbnails();
    if (p2Input) {
      p2Input.placeholder = "e.g. Using the extracted evidence, reconstruct the Flight SW 472 incident timeline minute-by-minute. Connect passenger movements, gate announcements, and the unattended baggage discovery while separating confirmed dependencies from uncertain ones. Do not declare final operational actions.";
      p2Input.value = "";
    }
  } else {
    if (p2AirportBoard) p2AirportBoard.classList.add("hidden");
    if (p2MysteryTip) p2MysteryTip.classList.remove("hidden");
    if (p2Input) {
      p2Input.placeholder = "e.g. Construct an objective, minute-by-minute timeline from this evidence. Order events strictly by timestamp. Do NOT name any suspect as the murderer.";
      p2Input.value = "";
    }
  }

  showScreen("screen-step2");
}

async function handleSubmitStep2() {
  dismissError();
  const promptInput = document.getElementById("step2-prompt-input");
  const prompt = promptInput.value.trim();

  if (!prompt) {
    showError("Please enter instructions for Agent 2 (Timeline Reconstructor).");
    promptInput.focus();
    return;
  }

  showLoading("Agent 2 is reconstructing the timeline...");

  try {
    const res = await fetch("/api/game/step2", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, user_2_prompt: prompt }),
    });

    if (!res.ok) {
      const errorMsg = await getErrorMessage(res);
      throw new Error(errorMsg);
    }

    const data = await res.json();
    state.user2Prompt = prompt;
    state.agent2Output = data.agent_2_output;

    hideLoading();
    showModal("modal-handoff2");
  } catch (err) {
    hideLoading();
    showError(err.message);
  }
}

function handleAcknowledgeHandoff2() {
  hideModal("modal-handoff2");
  // Player 3 sees Agent 2's reconstructed timeline
  document.getElementById("step3-agent2-output").textContent = state.agent2Output;
  
  const isImageBased = (state.images && state.images.length > 0) || state.theme === "Airport Crisis" || (state.caseId && state.caseId.includes("airport"));
  const p3Input = document.getElementById("step3-prompt-input");
  const p3AirportBoard = document.getElementById("step3-airport-board");

  if (isImageBased) {
    if (p3AirportBoard) p3AirportBoard.classList.remove("hidden");
    setP3ActiveImage(0);
    renderP3Thumbnails();
    renderOperationalRules(state.operationalRules);
    if (p3Input) {
      p3Input.placeholder = "e.g. Using the reconstructed incident sequence and airport operational rules (SEC-101, OPS-204, CLR-305), determine the valid operational action for Flight SW 472. Identify supporting rules, the current blocking condition, and requirements before operations can resume. Output strictly valid JSON with culprit, method, clue.";
      p3Input.value = "";
    }
  } else {
    if (p3AirportBoard) p3AirportBoard.classList.add("hidden");
    renderOperationalRules(state.operationalRules);
    if (p3Input) {
      p3Input.placeholder = "e.g. Based on the timeline, determine who committed the murder, their exact method, and the smoking gun clue. Output strictly valid JSON with keys: culprit, method, clue.";
      p3Input.value = "";
    }
  }

  showScreen("screen-step3");
}

async function handleSubmitStep3() {
  dismissError();
  const promptInput = document.getElementById("step3-prompt-input");
  const prompt = promptInput.value.trim();

  if (!prompt) {
    showError("Please enter instructions for Agent 3 (Final Detective).");
    promptInput.focus();
    return;
  }

  showLoading("Agent 3 is deducing the culprit & running evaluation...");

  try {
    const res = await fetch("/api/game/step3", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: state.sessionId, user_3_prompt: prompt }),
    });

    if (!res.ok) {
      const errorMsg = await getErrorMessage(res);
      throw new Error(errorMsg);
    }

    const data = await res.json();
    state.user3Prompt = prompt;
    state.finalVerdict = data.final_verdict;
    state.evaluation = data.evaluation;

    renderResults(data);
    hideLoading();
    showScreen("screen-results");
  } catch (err) {
    hideLoading();
    showError(err.message);
  }
}

// ========================================================
// RESULTS RENDERING
// ========================================================

function renderResults(data) {
  const evalData = data.evaluation;
  const breakdown = evalData.breakdown || {};

  // Total Score & Grade
  const totalScoreEl = document.getElementById("result-total-score");
  const gradeBadgeEl = document.getElementById("result-grade-badge");
  const summaryEl = document.getElementById("result-summary-text");

  totalScoreEl.textContent = evalData.total_score;
  gradeBadgeEl.textContent = evalData.grade;
  summaryEl.textContent = evalData.summary;

  // Grade color class
  gradeBadgeEl.className = "inline-block mt-1 px-3 py-1 rounded-lg text-sm font-bold font-mono";
  if (evalData.total_score >= 90) {
    gradeBadgeEl.classList.add("grade-s");
  } else if (evalData.total_score >= 75) {
    gradeBadgeEl.classList.add("grade-a");
  } else if (evalData.total_score >= 60) {
    gradeBadgeEl.classList.add("grade-b");
  } else if (evalData.total_score >= 40) {
    gradeBadgeEl.classList.add("grade-c");
  } else {
    gradeBadgeEl.classList.add("grade-f");
  }

  // Actual Deduction vs Expected Solution
  const culpritBD = breakdown.culprit || {};
  const methodBD = breakdown.method || {};
  const clueBD = breakdown.clue || {};
  const formatBD = breakdown.format || {};
  const leakBD = breakdown.leak_penalty || {};

  document.getElementById("res-actual-culprit").textContent = culpritBD.actual || "(None)";
  document.getElementById("res-actual-method").textContent = methodBD.actual || "(None)";
  document.getElementById("res-actual-clue").textContent = clueBD.actual || "(None)";

  document.getElementById("res-expected-culprit").textContent = culpritBD.expected || "(None)";
  document.getElementById("res-expected-method").textContent = methodBD.expected || "(None)";
  document.getElementById("res-expected-clue").textContent = clueBD.expected || "(None)";

  // 3-Player Prompt Engineering Scorecards
  const p1BD = breakdown.player_1 || {};
  const p2BD = breakdown.player_2 || {};
  const p3BD = breakdown.player_3 || {};

  const p1TotalEl = document.getElementById("score-p1-total");
  const p1PromptEl = document.getElementById("score-p1-prompt");
  const p1AgentEl = document.getElementById("score-p1-agent");
  const p1FeedbackEl = document.getElementById("score-p1-feedback");
  if (p1TotalEl) p1TotalEl.textContent = `${p1BD.score ?? "--"} / 20`;
  if (p1PromptEl) p1PromptEl.textContent = `${p1BD.prompt_score ?? "--"} / 12`;
  if (p1AgentEl) p1AgentEl.textContent = `${p1BD.agent_score ?? "--"} / 8`;
  if (p1FeedbackEl) p1FeedbackEl.textContent = p1BD.feedback || "";

  const p2TotalEl = document.getElementById("score-p2-total");
  const p2PromptEl = document.getElementById("score-p2-prompt");
  const p2AgentEl = document.getElementById("score-p2-agent");
  const p2FeedbackEl = document.getElementById("score-p2-feedback");
  if (p2TotalEl) p2TotalEl.textContent = `${p2BD.score ?? "--"} / 20`;
  if (p2PromptEl) p2PromptEl.textContent = `${p2BD.prompt_score ?? "--"} / 12`;
  if (p2AgentEl) p2AgentEl.textContent = `${p2BD.agent_score ?? "--"} / 8`;
  if (p2FeedbackEl) p2FeedbackEl.textContent = p2BD.feedback || "";

  const p3TotalEl = document.getElementById("score-p3-total");
  const p3PromptEl = document.getElementById("score-p3-prompt");
  const p3AgentEl = document.getElementById("score-p3-agent");
  const p3FeedbackEl = document.getElementById("score-p3-feedback");
  if (p3TotalEl) p3TotalEl.textContent = `${p3BD.score ?? "--"} / 20`;
  if (p3PromptEl) p3PromptEl.textContent = `${p3BD.prompt_score ?? "--"} / 12`;
  if (p3AgentEl) p3AgentEl.textContent = `${p3BD.agent_score ?? "--"} / 8`;
  if (p3FeedbackEl) p3FeedbackEl.textContent = p3BD.feedback || "";

  // Rubric Score Cards
  const cMax = culpritBD.max_points ?? 15;
  const mMax = methodBD.max_points ?? 15;
  const kMax = clueBD.max_points ?? 10;
  const fMax = formatBD.max_points ?? 12;

  document.getElementById("score-culprit-pts").textContent = `${culpritBD.points ?? 0} / ${cMax}`;
  document.getElementById("score-culprit-feedback").textContent = culpritBD.feedback || "";

  document.getElementById("score-method-pts").textContent = `${methodBD.points ?? 0} / ${mMax}`;
  document.getElementById("score-method-feedback").textContent = methodBD.feedback || "";

  document.getElementById("score-clue-pts").textContent = `${clueBD.points ?? 0} / ${kMax}`;
  document.getElementById("score-clue-feedback").textContent = clueBD.feedback || "";

  document.getElementById("score-format-pts").textContent = `${formatBD.points ?? 0} / ${fMax}`;
  document.getElementById("score-format-feedback").textContent = formatBD.feedback || "";

  // Hide leak penalty banner (guardrails enforce boundaries without penalty)
  const leakNotice = document.getElementById("leak-penalty-notice");
  if (leakNotice) {
    leakNotice.classList.add("hidden");
  }

  // Populate Relay Review (Telephone Game Breakdown)
  const u1PromptEl = document.getElementById("review-user1-prompt");
  const a1OutputEl = document.getElementById("review-agent1-output");
  const u2PromptEl = document.getElementById("review-user2-prompt");
  const a2OutputEl = document.getElementById("review-agent2-output");
  const u3PromptEl = document.getElementById("review-user3-prompt");
  const a3OutputEl = document.getElementById("review-agent3-output");

  if (u1PromptEl) u1PromptEl.textContent = state.user1Prompt || "(No prompt recorded)";
  if (a1OutputEl) a1OutputEl.textContent = state.agent1Output || "(No output)";
  if (u2PromptEl) u2PromptEl.textContent = state.user2Prompt || "(No prompt recorded)";
  if (a2OutputEl) a2OutputEl.textContent = state.agent2Output || "(No output)";
  if (u3PromptEl) u3PromptEl.textContent = state.user3Prompt || "(No prompt recorded)";
  if (a3OutputEl) a3OutputEl.textContent = JSON.stringify(data.final_verdict || {}, null, 2);
}

function toggleRelayChainReview() {
  const container = document.getElementById("relay-chain-container");
  const btn = document.getElementById("btn-toggle-relay-review");
  if (!container || !btn) return;

  if (container.classList.contains("hidden")) {
    container.classList.remove("hidden");
    btn.textContent = "Hide Relay Chain ▲";
  } else {
    container.classList.add("hidden");
    btn.textContent = "Show Full Relay Chain ▼";
  }
}

function handleResetForNewTeam() {
  state.sessionId = null;
  state.teamName = "";
  state.caseId = "";
  state.caseTitle = "";
  state.caseFile = "";
  state.theme = "Murder Mystery";
  state.images = [...DEFAULT_AIRPORT_IMAGES];
  state.operationalRules = [];
  state.user1Prompt = "";
  state.agent1Output = "";
  state.user2Prompt = "";
  state.agent2Output = "";
  state.user3Prompt = "";
  state.finalVerdict = null;
  state.evaluation = null;

  const airportBoard = document.getElementById("step1-airport-board");
  const mysteryBoard = document.getElementById("step1-mystery-board");
  if (airportBoard) airportBoard.classList.add("hidden");
  if (mysteryBoard) mysteryBoard.classList.remove("hidden");

  currentP1ImageIndex = 0;
  currentP2ImageIndex = 0;
  currentP3ImageIndex = 0;

  setP1ActiveImage(0);
  renderP1Thumbnails("all");
  setP2ActiveImage(0);
  renderP2Thumbnails();
  setP3ActiveImage(0);
  renderP3Thumbnails();

  renderOperationalRules([]);

  const container = document.getElementById("relay-chain-container");
  const btn = document.getElementById("btn-toggle-relay-review");
  if (container) container.classList.add("hidden");
  if (btn) btn.textContent = "Show Full Relay Chain ▼";

  document.getElementById("team-name-input").value = "";
  document.getElementById("header-match-info").classList.add("hidden");
  selectStoryMode("image");
  dismissError();
  showScreen("screen-welcome");
}

// ========================================================
// LEADERBOARD MANAGEMENT
// ========================================================

function openLeaderboard() {
  showModal("modal-leaderboard");
  fetchLeaderboard();
}

function closeLeaderboard() {
  hideModal("modal-leaderboard");
}

async function fetchLeaderboard() {
  const tbody = document.getElementById("leaderboard-tbody");
  const emptyEl = document.getElementById("leaderboard-empty");
  if (!tbody) return;

  tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-slate-500 font-mono">Loading standings...</td></tr>`;
  if (emptyEl) emptyEl.classList.add("hidden");

  try {
    const res = await fetch("/api/game/leaderboard");
    if (!res.ok) throw new Error("Failed to load leaderboard");
    const data = await res.json();
    const list = data.leaderboard || [];

    if (list.length === 0) {
      tbody.innerHTML = "";
      if (emptyEl) emptyEl.classList.remove("hidden");
      return;
    }

    tbody.innerHTML = list
      .map((entry) => {
        let rankBadge = `#${entry.rank}`;
        if (entry.rank === 1) rankBadge = "🥇 1";
        else if (entry.rank === 2) rankBadge = "🥈 2";
        else if (entry.rank === 3) rankBadge = "🥉 3";

        let gradeClass = "grade-f";
        if (entry.total_score >= 90) gradeClass = "grade-s";
        else if (entry.total_score >= 75) gradeClass = "grade-a";
        else if (entry.total_score >= 60) gradeClass = "grade-b";
        else if (entry.total_score >= 40) gradeClass = "grade-c";

        let dateStr = "";
        try {
          const d = new Date(entry.completed_at);
          dateStr = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        } catch {
          dateStr = entry.completed_at;
        }

        return `
          <tr class="hover:bg-slate-800/40 transition">
            <td class="py-3 px-3 font-bold text-amber-400 font-mono">${rankBadge}</td>
            <td class="py-3 px-3 font-semibold text-slate-100 font-sans">${escapeHtml(entry.team_name)}</td>
            <td class="py-3 px-3 text-slate-400 font-sans truncate max-w-[140px]">${escapeHtml(entry.case_title)}</td>
            <td class="py-3 px-3 font-bold text-slate-100 font-mono">${entry.total_score} <span class="text-slate-500 font-normal text-[10px]">/ 100</span></td>
            <td class="py-3 px-3"><span class="px-2 py-0.5 rounded text-[11px] font-bold font-mono ${gradeClass}">${escapeHtml(entry.grade.split(" ")[0])}</span></td>
            <td class="py-3 px-3 text-slate-500 text-[11px] font-mono">${dateStr}</td>
          </tr>
        `;
      })
      .join("");
  } catch (err) {
    console.error("Leaderboard fetch error:", err);
    tbody.innerHTML = `<tr><td colspan="6" class="py-6 text-center text-red-400 font-mono">Error loading leaderboard.</td></tr>`;
  }
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// ========================================================
// ORGANIZER CONTROL CENTER
// ========================================================

function openAdminModal() {
  showModal("modal-admin");
  fetchAdminData();
}

function closeAdminModal() {
  hideModal("modal-admin");
  closeInspector();
}

async function fetchAdminData() {
  try {
    // 1. Fetch Stats
    const statsRes = await fetch("/api/admin/stats");
    if (statsRes.ok) {
      const stats = await statsRes.json();
      const mEl = document.getElementById("admin-stat-matches");
      const aEl = document.getElementById("admin-stat-avg");
      const hEl = document.getElementById("admin-stat-high");
      const sEl = document.getElementById("admin-stat-solve-rate");

      if (mEl) mEl.textContent = stats.total_matches;
      if (aEl) aEl.textContent = stats.average_score.toFixed(1);
      if (hEl) hEl.textContent = stats.highest_score;
      if (sEl) sEl.textContent = `${stats.culprit_solve_rate}%`;
    }

    // 2. Fetch Matches
    const matchesRes = await fetch("/api/admin/matches");
    if (!matchesRes.ok) throw new Error("Failed to load match records");
    const matches = await matchesRes.json();

    const tbody = document.getElementById("admin-matches-tbody");
    const emptyEl = document.getElementById("admin-matches-empty");
    if (!tbody) return;

    if (matches.length === 0) {
      tbody.innerHTML = "";
      if (emptyEl) emptyEl.classList.remove("hidden");
      return;
    }

    if (emptyEl) emptyEl.classList.add("hidden");

    tbody.innerHTML = matches
      .map((m) => {
        let dateStr = "";
        try {
          const d = new Date(m.completed_at);
          dateStr = d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
        } catch {
          dateStr = m.completed_at;
        }

        return `
          <tr class="hover:bg-slate-900/60 transition">
            <td class="py-2.5 px-3 font-semibold text-slate-100 font-sans">${escapeHtml(m.team_name)}</td>
            <td class="py-2.5 px-3 text-slate-400 font-sans truncate max-w-[120px]">${escapeHtml(m.case_title)}</td>
            <td class="py-2.5 px-3 font-bold text-slate-100 font-mono">${m.total_score}</td>
            <td class="py-2.5 px-3"><span class="px-2 py-0.5 rounded text-[10px] font-bold font-mono">${escapeHtml(m.grade.split(" ")[0])}</span></td>
            <td class="py-2.5 px-3 text-slate-500 text-[11px] font-mono">${dateStr}</td>
            <td class="py-2.5 px-3 text-right space-x-2">
              <button 
                onclick="inspectMatch('${m.session_id}')" 
                class="px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-amber-400 font-mono text-[11px] font-semibold transition"
              >
                Inspect
              </button>
              <button 
                onclick="handleDeleteMatch('${m.session_id}', '${escapeHtml(m.team_name)}')" 
                class="px-2 py-1 rounded bg-red-950/40 hover:bg-red-900/60 border border-red-500/30 text-red-400 font-mono text-[11px] transition"
              >
                Delete
              </button>
            </td>
          </tr>
        `;
      })
      .join("");
  } catch (err) {
    console.error("Failed to load admin data:", err);
  }
}

async function inspectMatch(sessionId) {
  try {
    const res = await fetch(`/api/admin/matches/${sessionId}`);
    if (!res.ok) throw new Error("Failed to load match details");
    const m = await res.json();

    const inspector = document.getElementById("admin-inspector-container");
    if (!inspector) return;

    document.getElementById("inspector-team-name").textContent = `${m.team_name} (${m.case_title}) - Score: ${m.total_score}`;
    document.getElementById("inspector-p1").textContent = m.user_1_prompt || "(No prompt)";
    document.getElementById("inspector-a1").textContent = m.agent_1_output || "(No output)";
    document.getElementById("inspector-p2").textContent = m.user_2_prompt || "(No prompt)";
    document.getElementById("inspector-a2").textContent = m.agent_2_output || "(No output)";
    document.getElementById("inspector-p3").textContent = m.user_3_prompt || "(No prompt)";
    document.getElementById("inspector-verdict").textContent = JSON.stringify(m.final_verdict || {}, null, 2);

    inspector.classList.remove("hidden");
    inspector.scrollIntoView({ behavior: "smooth" });
  } catch (err) {
    alert("Error loading match: " + err.message);
  }
}

function closeInspector() {
  const inspector = document.getElementById("admin-inspector-container");
  if (inspector) inspector.classList.add("hidden");
}

async function handleDeleteMatch(sessionId, teamName) {
  if (!confirm(`Are you sure you want to delete the match record for team "${teamName}"?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/admin/matches/${sessionId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Delete failed");
    closeInspector();
    await fetchAdminData();
    fetchLeaderboard();
  } catch (err) {
    alert("Failed to delete match: " + err.message);
  }
}

async function handleAdminResetTournament() {
  if (!confirm("⚠️ DANGER: Are you sure you want to RESET the entire tournament?\nAll match records and leaderboard scores will be permanently deleted.")) {
    return;
  }
  try {
    const res = await fetch("/api/admin/reset", { method: "POST" });
    if (!res.ok) throw new Error("Reset failed");
    closeInspector();
    await fetchAdminData();
    fetchLeaderboard();
    alert("Tournament reset successfully.");
  } catch (err) {
    alert("Failed to reset tournament: " + err.message);
  }
}

function exportCSV() {
  window.open("/api/admin/export/csv", "_blank");
}

function exportJSON() {
  window.open("/api/admin/export/json", "_blank");
}

// ========================================================
// ORGANIZER TAB NAVIGATION & LLM/CASE MANAGEMENT
// ========================================================

function switchAdminTab(tab) {
  const tabs = ["matches", "llm", "cases"];
  tabs.forEach((t) => {
    const btn = document.getElementById(`admin-tab-btn-${t}`);
    const view = document.getElementById(`admin-view-${t}`);
    if (t === tab) {
      if (btn) {
        btn.classList.add("border-amber-400", "text-amber-400", "font-bold");
        btn.classList.remove("border-transparent", "text-slate-400");
      }
      if (view) view.classList.remove("hidden");
    } else {
      if (btn) {
        btn.classList.remove("border-amber-400", "text-amber-400", "font-bold");
        btn.classList.add("border-transparent", "text-slate-400");
      }
      if (view) view.classList.add("hidden");
    }
  });

  if (tab === "matches") fetchAdminData();
  else if (tab === "llm") fetchLLMStatus();
  else if (tab === "cases") fetchAdminCases();
}

async function fetchLLMStatus() {
  try {
    const res = await fetch("/api/admin/llm/status");
    if (!res.ok) return;
    const data = await res.json();

    const provEl = document.getElementById("llm-current-provider");
    const modEl = document.getElementById("llm-current-model");
    const msgEl = document.getElementById("llm-status-message");
    const latEl = document.getElementById("llm-latency-badge");
    const dotEl = document.getElementById("llm-status-dot");

    if (provEl) provEl.textContent = data.provider;
    if (modEl) modEl.textContent = data.model_name;
    if (msgEl) msgEl.textContent = data.message || "Ready";
    if (latEl) latEl.textContent = data.latency_ms !== null ? `${data.latency_ms} ms` : "-- ms";

    if (dotEl) {
      if (data.status === "connected") {
        dotEl.className = "w-3 h-3 rounded-full bg-emerald-400 animate-pulse";
      } else {
        dotEl.className = "w-3 h-3 rounded-full bg-red-400";
      }
    }

    const selProv = document.getElementById("llm-config-provider");
    const inpMod = document.getElementById("llm-config-model");
    const chkFall = document.getElementById("llm-config-fallback");

    if (selProv) selProv.value = data.provider;
    if (inpMod) inpMod.value = data.model_name;
    if (chkFall) chkFall.checked = data.fallback_to_offline;
  } catch (err) {
    console.error("Failed to load LLM status:", err);
  }
}

async function handleTestLLMConnection() {
  const latEl = document.getElementById("llm-latency-badge");
  const msgEl = document.getElementById("llm-status-message");
  if (latEl) latEl.textContent = "Testing...";
  if (msgEl) msgEl.textContent = "Pinging configured LLM...";
  await fetchLLMStatus();
}

async function handleSaveLLMConfig() {
  const provider = document.getElementById("llm-config-provider").value;
  const modelName = document.getElementById("llm-config-model").value.trim();
  const fallback = document.getElementById("llm-config-fallback").checked;

  try {
    const res = await fetch("/api/admin/llm/configure", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        provider: provider,
        model_name: modelName || undefined,
        fallback_to_offline: fallback,
      }),
    });
    if (!res.ok) throw new Error("Failed to configure LLM");
    alert("LLM Engine configuration updated successfully!");
    await fetchLLMStatus();
  } catch (err) {
    alert("Error updating LLM config: " + err.message);
  }
}

async function fetchAdminCases() {
  const container = document.getElementById("admin-cases-list");
  if (!container) return;
  container.innerHTML = `<div class="py-4 text-center text-slate-500">Loading cases...</div>`;

  try {
    const res = await fetch("/api/admin/cases");
    if (!res.ok) throw new Error("Failed to fetch cases");
    const cases = await res.json();

    const builtinIds = ["case_01_blackwood_manor", "case_02_neon_nexus", "case_03_velvet_vault"];

    container.innerHTML = cases
      .map((c) => {
        const isBuiltin = builtinIds.includes(c.case_id);
        const badge = isBuiltin
          ? `<span class="px-2 py-0.5 rounded bg-blue-500/20 text-blue-300 text-[10px] font-bold">Built-in Seed</span>`
          : `<span class="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 text-[10px] font-bold">Custom Case</span>`;

        const deleteBtn = isBuiltin
          ? ""
          : `<button onclick="handleDeleteCase('${c.case_id}')" class="px-2 py-1 rounded bg-red-950/40 hover:bg-red-900/60 border border-red-500/30 text-red-400 text-[11px] transition">Delete</button>`;

        return `
          <div class="p-3 rounded-lg bg-slate-900 border border-slate-800 flex items-center justify-between">
            <div class="space-y-1 max-w-[70%]">
              <div class="flex items-center gap-2">
                <span class="font-bold text-slate-100">${escapeHtml(c.title)}</span>
                <span class="text-slate-500 font-mono text-[10px]">(${c.difficulty})</span>
                ${badge}
              </div>
              <p class="text-slate-400 text-[11px] truncate">${escapeHtml(c.synopsis)}</p>
              <p class="text-slate-500 text-[10px]">Culprit: <strong class="text-slate-300">${escapeHtml(c.ground_truth.culprit)}</strong></p>
            </div>
            <div class="flex items-center gap-2">
              ${deleteBtn}
            </div>
          </div>
        `;
      })
      .join("");
  } catch (err) {
    container.innerHTML = `<div class="py-4 text-center text-red-400">Failed to load cases.</div>`;
  }
}

function toggleCaseCreatorForm() {
  const form = document.getElementById("admin-case-creator-form");
  const btn = document.getElementById("btn-toggle-case-creator");
  if (!form) return;
  if (form.classList.contains("hidden")) {
    form.classList.remove("hidden");
    if (btn) btn.textContent = "✕ Close Form";
  } else {
    form.classList.add("hidden");
    if (btn) btn.textContent = "➕ Author New Mystery";
  }
}

async function handleCreateCustomCase() {
  const caseId = document.getElementById("create-case-id").value.trim();
  const title = document.getElementById("create-case-title").value.trim();
  const difficulty = document.getElementById("create-case-difficulty").value;
  const synopsis = document.getElementById("create-case-synopsis").value.trim();
  const story = document.getElementById("create-case-story").value.trim();
  const culprit = document.getElementById("create-case-culprit").value.trim();
  const method = document.getElementById("create-case-method").value.trim();
  const clue = document.getElementById("create-case-clue").value.trim();
  const motive = document.getElementById("create-case-motive").value.trim();
  const suspectsStr = document.getElementById("create-case-suspects").value.trim();
  const keywordsStr = document.getElementById("create-case-keywords").value.trim();

  if (!caseId || !title || !synopsis || !story || !culprit || !method || !clue) {
    alert("Please fill in all required fields (Case ID, Title, Synopsis, Case File, Culprit, Method, Clue).");
    return;
  }

  const payload = {
    case_id: caseId,
    title: title,
    difficulty: difficulty,
    synopsis: synopsis,
    noisy_case_file: story,
    ground_truth: {
      culprit: culprit,
      weapon_or_method: method,
      key_clue: clue,
      motive: motive || "Unspecified motive",
      suspects: suspectsStr ? suspectsStr.split(",").map((s) => s.trim()) : [culprit],
    },
    leak_keywords: keywordsStr ? keywordsStr.split(",").map((s) => s.trim()) : [culprit],
  };

  try {
    const res = await fetch("/api/admin/cases", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || "Failed to create case");
    }
    alert(`Case "${title}" deployed successfully! It is now playable on the station.`);
    toggleCaseCreatorForm();
    await fetchAdminCases();
    await loadCases(); // Refresh main game dropdown
  } catch (err) {
    alert("Error creating case: " + err.message);
  }
}

async function handleDeleteCase(caseId) {
  if (!confirm(`Are you sure you want to delete custom case "${caseId}"?`)) return;
  try {
    const res = await fetch(`/api/admin/cases/${caseId}`, { method: "DELETE" });
    if (!res.ok) throw new Error("Delete failed");
    await fetchAdminCases();
    await loadCases();
  } catch (err) {
    alert("Failed to delete case: " + err.message);
  }
}

// ========================================================
// GLOBAL WINDOW BINDINGS (ENSURES INLINE ONCLICK RELIABILITY)
// ========================================================
window.selectStoryMode = selectStoryMode;
window.syncMysteryCase = syncMysteryCase;
window.handleStartGame = handleStartGame;
window.handleSubmitStep1 = handleSubmitStep1;
window.handleAcknowledgeHandoff1 = handleAcknowledgeHandoff1;
window.handleSubmitStep2 = handleSubmitStep2;
window.handleAcknowledgeHandoff2 = handleAcknowledgeHandoff2;
window.handleSubmitStep3 = handleSubmitStep3;
window.handleResetForNewTeam = handleResetForNewTeam;
window.openLeaderboard = openLeaderboard;
window.closeLeaderboard = closeLeaderboard;
window.toggleRelayChainReview = toggleRelayChainReview;
window.insertExamplePrompt = insertExamplePrompt;

// Step 1 Controls
window.setP1ActiveImage = setP1ActiveImage;
window.prevP1Image = prevP1Image;
window.nextP1Image = nextP1Image;
window.filterAirportEvidence = filterAirportEvidence;

// Step 2 Controls
window.setP2ActiveImage = setP2ActiveImage;
window.prevP2Image = prevP2Image;
window.nextP2Image = nextP2Image;

// Step 3 Controls
window.setP3ActiveImage = setP3ActiveImage;
window.prevP3Image = prevP3Image;
window.nextP3Image = nextP3Image;

// Modal & Inspection Controls
window.openActiveImageViewer = openActiveImageViewer;
window.openImageViewerByIndex = openImageViewerByIndex;
window.prevImage = prevImage;
window.nextImage = nextImage;
window.closeImageViewer = closeImageViewer;

// Admin & Modal Controls
window.openAdminModal = openAdminModal;
window.closeAdminModal = closeAdminModal;
window.switchAdminTab = switchAdminTab;
window.exportCSV = exportCSV;
window.exportJSON = exportJSON;
window.fetchAdminData = fetchAdminData;
window.handleAdminResetTournament = handleAdminResetTournament;
window.closeInspector = closeInspector;
window.handleTestLLMConnection = handleTestLLMConnection;
window.handleSaveLLMConfig = handleSaveLLMConfig;
window.toggleCaseCreatorForm = toggleCaseCreatorForm;
window.handleCreateCustomCase = handleCreateCustomCase;
window.handleDeleteCase = handleDeleteCase;
window.dismissError = dismissError;

// ========================================================
// STATION UI INITIALIZATION
// ========================================================
function initStationUI() {
  setupKeyboardShortcuts();
  setupEvidenceControls();
  selectStoryMode("image");
  setP1ActiveImage(0);
  renderP1Thumbnails("all");
  setP2ActiveImage(0);
  renderP2Thumbnails();
  setP3ActiveImage(0);
  renderP3Thumbnails();
  loadCases().catch((err) => console.warn("Failed to load initial cases:", err));
}

window.initStationUI = initStationUI;

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initStationUI);
} else {
  initStationUI();
}

