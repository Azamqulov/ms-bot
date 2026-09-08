// ================= GLOBAL STATE & AUTH =================
    const telegramInitData = window.Telegram?.WebApp?.initData || '';
    const currentTelegramId = window.Telegram?.WebApp?.initDataUnsafe?.user?.id || (new URLSearchParams(window.location.search).get('admin_id')) || null;

    function getAdminAuthHeaders(extraHeaders = {}) {
      const headers = { ...extraHeaders };
      if (telegramInitData) {
        headers['X-Telegram-Init-Data'] = telegramInitData;
      }
      return headers;
    }

    const answers1to35 = {}; // {1: 'A', 2: 'B', ...}
    const questionsMeta = {}; // {1: {text: '', image: '', options: {A:'', B:'', C:'', D:''}}}
    const openQuestionsData = {}; // {36: {a: [''], b: ['']}, ...}
    const openQuestionsMeta = {}; // {36: {text: '', image: ''}}
    const groupContextData = { text: '', image: '', options: { A: '', B: '', C: '', D: '', E: '', F: '' } };

    let currentActiveInput = null;
    // (API konfiguratsiyasi va apiFetch js/config.js faylidan yuklanadi)

    let currentKbTab = 'greek';
    let isGreekShiftActive = false;
    let activeUploadTarget = null; // {type: 'q1to35'|'openQ', qNum: 1}
    let autosaveTimer = null;
    let lastCreatedTestCode = '';

    const checkboxStates = {
      autoCheck: true,
      hideAnswers: false,
      reqSub: false
    };

    let selectedAccessType = 'closed'; // 'open' | 'closed'
    let selectedAnswerMode = 'write';  // 'write' | 'photo'

    // Undo / Redo history map
    const inputHistory = new Map(); // inputElement -> { history: [], pointer: -1 }

    function trackInputHistory(inp) {
      if (!inp) return;
      if (!inputHistory.has(inp)) {
        inputHistory.set(inp, { history: [inp.value], pointer: 0 });
      }
      const data = inputHistory.get(inp);
      if (data.history[data.pointer] !== inp.value) {
        data.history = data.history.slice(0, data.pointer + 1);
        data.history.push(inp.value);
        data.pointer = data.history.length - 1;
      }
    }

    // ================= TABS LOGIC =================
    function switchAdminTab(tab) {
      const createBtn = document.getElementById('navCreateTab');
      const listBtn = document.getElementById('navListTab');
      const createForm = document.getElementById('createTestForm');
      const listTab = document.getElementById('testsListTab');
      const headerTitle = document.getElementById('pageHeaderTitle');

      if (tab === 'create') {
        createBtn.classList.add('active');
        listBtn.classList.remove('active');
        createForm.style.display = 'flex';
        listTab.style.display = 'none';
        headerTitle.innerText = "Test qo'shish";
        if (editingTestId) {
          resetCreateForm(true);
        }
      } else {
        createBtn.classList.remove('active');
        listBtn.classList.add('active');
        createForm.style.display = 'none';
        listTab.style.display = 'flex';
        headerTitle.innerText = "Mening testlarim";
        loadMyTests();
      }
    }

    // ================= 1–32 SAVOLLAR (KLASSIK VARIANTLI TESTLAR) =================
    function initQuestions1to32() {
      const container = document.getElementById('keysList1to32');
      if (!container) return;
      container.innerHTML = '';

      for (let i = 1; i <= 32; i++) {
        if (!answers1to35[i]) answers1to35[i] = 'A';
        if (!questionsMeta[i]) questionsMeta[i] = { text: '', image: '', options: { A: '', B: '', C: '', D: '' } };

        const row = document.createElement('div');
        row.className = 'key-row';
        row.id = `keyRow_${i}`;

        const hasMeta = Boolean(questionsMeta[i].text || questionsMeta[i].image);

        row.innerHTML = `
          <div class="key-row-header">
            <span class="key-row-label">
              ${i}-savol
              <span class="key-has-meta-badge" id="badge_q_${i}" style="display:${hasMeta ? 'inline-block' : 'none'};">Savol matni kiritilgan</span>
            </span>
            <button type="button" class="key-attach-btn" onclick="toggleDetailsDrawer(${i})">
              <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
              Rasm / Matn qo'shish
            </button>
          </div>
          <div class="key-options-grid">
            ${['A', 'B', 'C', 'D'].map(opt => `
              <button type="button" class="key-option-btn ${answers1to35[i] === opt ? 'selected' : ''}" onclick="selectKeyOption(${i}, '${opt}')">${opt}</button>
            `).join('')}
          </div>
          <div class="key-details-drawer" id="detailsDrawer_${i}">
            <div style="font-size:12px; font-weight:600; color:var(--text-sub);">Savol matni (KaTeX formulalar qo'llab-quvvatlanadi):</div>
            <div class="answer-field-wrap">
              <input type="text" class="form-input" id="qTextInput_${i}" style="height:38px; font-size:13px;" placeholder="${i}-savol matni yoki formulasi (ixtiyoriy)..." value="${escapeHtml(questionsMeta[i].text || '')}" onfocus="registerActiveInput(this)" oninput="saveQuestionText(${i}, this.value)">
              <div class="answer-tools">
                <button type="button" class="tool-icon-btn" onclick="openKeyboardForSpecificInput('qTextInput_${i}', 'symbols')" title="Formula">Σ</button>
                <button type="button" class="tool-icon-btn" onclick="openKeyboardForSpecificInput('qTextInput_${i}', 'greek')" title="Klaviatura"><svg class="icon icon-sm" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6.01" y2="8"></line><line x1="10" y1="8" x2="10.01" y2="8"></line><line x1="14" y1="8" x2="14.01" y2="8"></line><line x1="18" y1="8" x2="18.01" y2="8"></line><line x1="6" y1="12" x2="6.01" y2="12"></line><line x1="10" y1="12" x2="10.01" y2="12"></line><line x1="14" y1="12" x2="14.01" y2="12"></line><line x1="18" y1="12" x2="18.01" y2="12"></line><line x1="7" y1="16" x2="17" y2="16"></line></svg></button>
              </div>
            </div>
            <div class="katex-preview" id="katexPreview_q_${i}">
              ${renderKatexString(questionsMeta[i].text || "Formula ko'rinishi shu yerda chiqadi...")}
            </div>

            <div style="font-size:12px; font-weight:600; color:var(--text-sub); margin-top:4px;">Savol rasmi (chizma yoki grafik):</div>
            <div class="upload-action-row">
              <button type="button" class="btn-upload" onclick="triggerFileUpload('q1to35', ${i})">
                <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                Fayl yuklash
              </button>
              <input type="text" class="form-input" id="qImgUrlInput_${i}" style="flex:1; height:34px; font-size:12px;" placeholder="Yoki rasm URL havolasi..." value="${escapeHtml(questionsMeta[i].image || '')}" oninput="saveQuestionImage(${i}, this.value)">
            </div>
            <div id="imgPreviewBox_q_${i}" style="display:${questionsMeta[i].image ? 'block' : 'none'};">
              <div class="img-preview-wrap">
                <img class="image-preview-thumbnail" id="imgThumb_q_${i}" src="${questionsMeta[i].image || ''}" alt="Savol rasmi">
                <span style="font-size:12px; flex:1; color:var(--text-sub); word-break:break-all;" id="imgName_q_${i}">${questionsMeta[i].image || ''}</span>
                <button type="button" class="del-btn" onclick="removeQuestionImage(${i})" title="Rasmni o'chirish">
                  <svg class="icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
              </div>
            </div>
          </div>
        `;
        container.appendChild(row);
      }
    }

    // ================= 33–35 SAVOLLAR (GURUHLANGAN TESTLAR — A dan F gacha) =================
    function initGroupedQuestions33to35() {
      const container = document.getElementById('keysList33to35');
      if (!container) return;
      container.innerHTML = '';

      for (let i = 33; i <= 35; i++) {
        if (!answers1to35[i]) answers1to35[i] = 'A';

        const row = document.createElement('div');
        row.className = 'key-row';
        row.id = `keyRow_${i}`;

        row.innerHTML = `
          <div class="key-row-header">
            <span class="key-row-label">${i}-savol:</span>
          </div>
          <div class="key-options-grid six-options">
            ${['A', 'B', 'C', 'D', 'E', 'F'].map(opt => `
              <button type="button" class="key-option-btn ${answers1to35[i] === opt ? 'selected' : ''}" onclick="selectKeyOption(${i}, '${opt}')">${opt}</button>
            `).join('')}
          </div>
        `;
        container.appendChild(row);
      }
    }

    function toggleGroupMetaDetails() {
      const wrap = document.getElementById('groupMetaDetailsWrap');
      const text = document.getElementById('toggleGroupDetailsText');
      if (!wrap) return;
      const isOpen = (wrap.style.display !== 'none');
      wrap.style.display = isOpen ? 'none' : 'flex';
      if (text) {
        text.innerText = isOpen 
          ? "+ Kontekst matni yoki chizma qo'shish (ixtiyoriy)" 
          : "— Yopish: Kontekst matni va chizma";
      }
    }

    function initQuestions1to35() {
      initQuestions1to32();
      initGroupedQuestions33to35();
    }

    function saveGroupContextText(val) {
      groupContextData.text = val;
      const prev = document.getElementById('katexPreview_groupContext');
      if (prev) {
        prev.innerHTML = renderKatexString(val || "Formula ko'rinishi shu yerda chiqadi...");
      }
      scheduleAutosave();
    }

    function saveGroupImage(val) {
      groupContextData.image = val.trim();
      const pBox = document.getElementById('imgPreviewBox_group');
      const thumb = document.getElementById('imgThumb_group');
      const nameElem = document.getElementById('imgName_group');
      if (val.trim()) {
        pBox.style.display = 'block';
        thumb.src = val.trim();
        nameElem.innerText = val.trim();
      } else {
        pBox.style.display = 'none';
      }
      scheduleAutosave();
    }

    function removeGroupImage() {
      const inp = document.getElementById('groupImgUrlInput');
      if (inp) inp.value = '';
      saveGroupImage('');
    }

    function saveSharedOption(letter, val) {
      if (!groupContextData.options) groupContextData.options = {};
      groupContextData.options[letter] = val.trim();
      scheduleAutosave();
    }

    function selectKeyOption(qNum, opt) {
      answers1to35[qNum] = opt;
      const row = document.getElementById(`keyRow_${qNum}`);
      if (row) {
        const btns = row.querySelectorAll('.key-option-btn');
        btns.forEach(btn => {
          if (btn.innerText.trim() === opt) {
            btn.classList.add('selected');
          } else {
            btn.classList.remove('selected');
          }
        });
      }
      scheduleAutosave();
    }

    function toggleDetailsDrawer(qNum) {
      const drawer = document.getElementById(`detailsDrawer_${qNum}`);
      if (drawer) {
        drawer.classList.toggle('open');
      }
    }

    function saveQuestionText(qNum, val) {
      if (!questionsMeta[qNum]) questionsMeta[qNum] = {};
      questionsMeta[qNum].text = val;
      const prev = document.getElementById(`katexPreview_q_${qNum}`);
      if (prev) {
        prev.innerHTML = renderKatexString(val || "Formula ko'rinishi shu yerda chiqadi...");
      }
      updateMetaBadge(qNum);
      scheduleAutosave();
    }

    function saveQuestionImage(qNum, val) {
      if (!questionsMeta[qNum]) questionsMeta[qNum] = {};
      questionsMeta[qNum].image = val.trim();
      const pBox = document.getElementById(`imgPreviewBox_q_${qNum}`);
      const thumb = document.getElementById(`imgThumb_q_${qNum}`);
      const nameElem = document.getElementById(`imgName_q_${qNum}`);
      if (val.trim()) {
        pBox.style.display = 'block';
        thumb.src = val.trim();
        nameElem.innerText = val.trim();
      } else {
        pBox.style.display = 'none';
      }
      updateMetaBadge(qNum);
      scheduleAutosave();
    }

    function removeQuestionImage(qNum) {
      saveQuestionImage(qNum, '');
      const inp = document.getElementById(`qImgUrlInput_${qNum}`);
      if (inp) inp.value = '';
    }

    function updateMetaBadge(qNum) {
      const badge = document.getElementById(`badge_q_${qNum}`);
      if (badge) {
        const has = Boolean(questionsMeta[qNum]?.text || questionsMeta[qNum]?.image);
        badge.style.display = has ? 'inline-block' : 'none';
      }
    }

    // ================= 36–45 OCHIQ SAVOLLARNI GENERATSIYA QILISH =================
    function initOpenQuestions() {
      const container = document.getElementById('openQuestionsContainer');
      container.innerHTML = '';

      for (let i = 36; i <= 45; i++) {
        if (!openQuestionsData[i]) {
          openQuestionsData[i] = { a: [''], b: [''] };
        }
        if (!openQuestionsMeta[i]) {
          openQuestionsMeta[i] = { text: '', image: '' };
        }

        const subKeys = Object.keys(openQuestionsData[i]);
        const card = document.createElement('div');
        card.className = 'open-question-card';
        card.id = `openCard_${i}`;

        card.innerHTML = `
          <div class="open-q-header">
            <div class="open-q-title">${i}-savol</div>
            <div style="display:flex; align-items:center; gap:12px;">
              <button type="button" class="key-attach-btn" onclick="toggleOpenQuestionMeta(${i})">
                <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect><circle cx="8.5" cy="8.5" r="1.5"></circle><polyline points="21 15 16 10 5 21"></polyline></svg>
                Shart / Rasm qo'shish
              </button>
              <div class="count-stepper">
                <span>Javoblar soni:</span>
                <button type="button" class="step-btn" onclick="stepCount(${i}, -1)">–</button>
                <span class="step-val" id="stepVal_${i}">${subKeys.length}</span>
                <button type="button" class="step-btn" onclick="stepCount(${i}, 1)">+</button>
              </div>
            </div>
          </div>

          <div class="key-details-drawer" id="openMetaDrawer_${i}">
            <div style="font-size:12px; font-weight:600; color:var(--text-sub);">Savol sharti yoki matni:</div>
            <div class="answer-field-wrap">
              <input type="text" class="form-input" id="openTextInput_${i}" style="height:38px; font-size:13px;" placeholder="${i}-savol matni yoki formulasi..." value="${escapeHtml(openQuestionsMeta[i].text || '')}" onfocus="registerActiveInput(this)" oninput="saveOpenQuestionText(${i}, this.value)">
              <div class="answer-tools">
                <button type="button" class="tool-icon-btn" onclick="openKeyboardForSpecificInput('openTextInput_${i}', 'symbols')" title="Formula">Σ</button>
                <button type="button" class="tool-icon-btn" onclick="openKeyboardForSpecificInput('openTextInput_${i}', 'greek')" title="Klaviatura"><svg class="icon icon-sm" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6.01" y2="8"></line><line x1="10" y1="8" x2="10.01" y2="8"></line><line x1="14" y1="8" x2="14.01" y2="8"></line><line x1="18" y1="8" x2="18.01" y2="8"></line><line x1="6" y1="12" x2="6.01" y2="12"></line><line x1="10" y1="12" x2="10.01" y2="12"></line><line x1="14" y1="12" x2="14.01" y2="12"></line><line x1="18" y1="12" x2="18.01" y2="12"></line><line x1="7" y1="16" x2="17" y2="16"></line></svg></button>
              </div>
            </div>
            <div class="katex-preview" id="katexPreview_open_${i}">
              ${renderKatexString(openQuestionsMeta[i].text || "Formula ko'rinishi shu yerda chiqadi...")}
            </div>

            <div style="font-size:12px; font-weight:600; color:var(--text-sub); margin-top:4px;">Chizma yoki masala rasmi:</div>
            <div class="upload-action-row">
              <button type="button" class="btn-upload" onclick="triggerFileUpload('openQ', ${i})">
                <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="17 8 12 3 7 8"></polyline><line x1="12" y1="3" x2="12" y2="15"></line></svg>
                Fayl yuklash
              </button>
              <input type="text" class="form-input" id="openImgUrlInput_${i}" style="flex:1; height:34px; font-size:12px;" placeholder="Yoki rasm URL..." value="${escapeHtml(openQuestionsMeta[i].image || '')}" oninput="saveOpenQuestionImage(${i}, this.value)">
            </div>
            <div id="imgPreviewBox_open_${i}" style="display:${openQuestionsMeta[i].image ? 'block' : 'none'};">
              <div class="img-preview-wrap">
                <img class="image-preview-thumbnail" id="imgThumb_open_${i}" src="${openQuestionsMeta[i].image || ''}" alt="Savol rasmi">
                <span style="font-size:12px; flex:1; color:var(--text-sub); word-break:break-all;" id="imgName_open_${i}">${openQuestionsMeta[i].image || ''}</span>
                <button type="button" class="del-btn" onclick="removeOpenQuestionImage(${i})" title="O'chirish">
                  <svg class="icon" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
                </button>
              </div>
            </div>
          </div>

          <div style="font-size:12px; font-weight:600; color:var(--text-sub);" id="subLetters_${i}">
            ${subKeys.join(' , ')}
          </div>

          <div class="sub-variants-box">
            <div class="sub-variants-header">Har bir variant uchun ehtimoliy to'g'ri javoblarni kiriting:</div>
            <div id="subVariantsList_${i}">
              ${renderSubVariantsRows(i)}
            </div>
          </div>
        `;
        container.appendChild(card);
      }
    }

    function toggleOpenQuestionMeta(qNum) {
      const drawer = document.getElementById(`openMetaDrawer_${qNum}`);
      if (drawer) drawer.classList.toggle('open');
    }

    function saveOpenQuestionText(qNum, val) {
      if (!openQuestionsMeta[qNum]) openQuestionsMeta[qNum] = {};
      openQuestionsMeta[qNum].text = val;
      const prev = document.getElementById(`katexPreview_open_${qNum}`);
      if (prev) {
        prev.innerHTML = renderKatexString(val || "Formula ko'rinishi shu yerda chiqadi...");
      }
      scheduleAutosave();
    }

    function saveOpenQuestionImage(qNum, val) {
      if (!openQuestionsMeta[qNum]) openQuestionsMeta[qNum] = {};
      openQuestionsMeta[qNum].image = val.trim();
      const pBox = document.getElementById(`imgPreviewBox_open_${qNum}`);
      const thumb = document.getElementById(`imgThumb_open_${qNum}`);
      const nameElem = document.getElementById(`imgName_open_${qNum}`);
      if (val.trim()) {
        pBox.style.display = 'block';
        thumb.src = val.trim();
        nameElem.innerText = val.trim();
      } else {
        pBox.style.display = 'none';
      }
      scheduleAutosave();
    }

    function removeOpenQuestionImage(qNum) {
      saveOpenQuestionImage(qNum, '');
      const inp = document.getElementById(`openImgUrlInput_${qNum}`);
      if (inp) inp.value = '';
    }

    function renderSubVariantsRows(qNum) {
      const data = openQuestionsData[qNum] || { a: [''] };
      const keys = Object.keys(data);

      return keys.map(variant => `
        <div class="variant-group" id="variantGroup_${qNum}_${variant}">
          <div class="variant-label">${variant}) variant uchun:</div>
          <div id="ansList_${qNum}_${variant}">
            ${(data[variant] || ['']).map((ans, idx) => renderAnswerInputHtml(qNum, variant, idx, ans)).join('')}
          </div>
          <button type="button" class="add-ans-btn" onclick="addAnswerRow(${qNum}, '${variant}')">
            <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24"><line x1="12" y1="5" x2="12" y2="19"></line><line x1="5" y1="12" x2="19" y2="12"></line></svg>
            Javob qo'shish
          </button>
        </div>
      `).join('');
    }

    function renderAnswerInputHtml(qNum, variant, idx, val) {
      const fieldId = `openAns_${qNum}_${variant}_${idx}`;
      return `
        <div class="answer-input-row" id="row_${qNum}_${variant}_${idx}">
          <div class="answer-field-wrap">
            <input type="text" class="answer-input" id="${fieldId}" value="${escapeHtml(val || '')}" 
                   placeholder="${variant}) to'g'ri javob (masalan: 12 yoki 0.5)..." 
                   onfocus="registerActiveInput(this)" 
                   oninput="updateOpenAns(${qNum}, '${variant}', ${idx}, this.value)">
            <div class="answer-tools">
              <button type="button" class="tool-icon-btn" onclick="openKeyboardForSpecificInput('${fieldId}', 'symbols')" title="Formula">Σ</button>
              <button type="button" class="tool-icon-btn" onclick="openKeyboardForSpecificInput('${fieldId}', 'greek')" title="Klaviatura"><svg class="icon icon-sm" viewBox="0 0 24 24"><rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect><line x1="6" y1="8" x2="6.01" y2="8"></line><line x1="10" y1="8" x2="10.01" y2="8"></line><line x1="14" y1="8" x2="14.01" y2="8"></line><line x1="18" y1="8" x2="18.01" y2="8"></line><line x1="6" y1="12" x2="6.01" y2="12"></line><line x1="10" y1="12" x2="10.01" y2="12"></line><line x1="14" y1="12" x2="14.01" y2="12"></line><line x1="18" y1="12" x2="18.01" y2="12"></line><line x1="7" y1="16" x2="17" y2="16"></line></svg></button>
            </div>
          </div>
          <button type="button" class="del-btn" onclick="removeAnswerRow(${qNum}, '${variant}', ${idx})" title="O'chirish">
            <svg class="icon" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
          </button>
        </div>
      `;
    }

    function updateOpenAns(qNum, variant, idx, val) {
      if (!openQuestionsData[qNum]) openQuestionsData[qNum] = { a: [''] };
      if (!openQuestionsData[qNum][variant]) openQuestionsData[qNum][variant] = [''];
      openQuestionsData[qNum][variant][idx] = val;
      trackInputHistory(document.getElementById(`openAns_${qNum}_${variant}_${idx}`));
      scheduleAutosave();
    }

    function addAnswerRow(qNum, variant) {
      if (!openQuestionsData[qNum][variant]) openQuestionsData[qNum][variant] = [];
      openQuestionsData[qNum][variant].push('');
      const container = document.getElementById(`ansList_${qNum}_${variant}`);
      const newIdx = openQuestionsData[qNum][variant].length - 1;
      const div = document.createElement('div');
      div.innerHTML = renderAnswerInputHtml(qNum, variant, newIdx, '');
      container.appendChild(div.firstElementChild);
      scheduleAutosave();
    }

    function removeAnswerRow(qNum, variant, idx) {
      if (openQuestionsData[qNum][variant].length <= 1) {
        showToast("Kamida 1 ta javob maydoni qolishi kerak!", true);
        return;
      }
      openQuestionsData[qNum][variant].splice(idx, 1);
      const container = document.getElementById(`ansList_${qNum}_${variant}`);
      container.innerHTML = openQuestionsData[qNum][variant].map((ans, i) => renderAnswerInputHtml(qNum, variant, i, ans)).join('');
      scheduleAutosave();
    }

    function stepCount(qNum, change) {
      const stepElem = document.getElementById(`stepVal_${qNum}`);
      const lettersElem = document.getElementById(`subLetters_${qNum}`);
      const listElem = document.getElementById(`subVariantsList_${qNum}`);

      const possibleLetters = ['a', 'b', 'c', 'd'];
      let curCount = Object.keys(openQuestionsData[qNum]).length;
      let newCount = curCount + change;
      if (newCount < 1) newCount = 1;
      if (newCount > 4) newCount = 4;
      if (newCount === curCount) return;

      const newData = {};
      for (let i = 0; i < newCount; i++) {
        const letter = possibleLetters[i];
        newData[letter] = openQuestionsData[qNum][letter] || [''];
      }
      openQuestionsData[qNum] = newData;

      stepElem.innerText = newCount;
      lettersElem.innerText = Object.keys(newData).join(' , ');
      listElem.innerHTML = renderSubVariantsRows(qNum);
      scheduleAutosave();
    }

    // ================= IMAGE UPLOAD HANDLING =================
    function triggerFileUpload(type, qNum) {
      activeUploadTarget = { type, qNum };
      const fileInp = document.getElementById('globalImageFileInput');
      fileInp.value = '';
      fileInp.click();
    }

    async function handleFileSelected(input) {
      if (!input.files || !input.files[0] || !activeUploadTarget) return;
      const file = input.files[0];
      const formData = new FormData();
      formData.append('file', file);

      showToast("Rasm yuklanmoqda...");

      if (!API_BASE && window.location.hostname.includes('github.io')) {
        openApiConfigModal();
        showToast("Server manzili kiritilmagan! Iltimos, serverni sozlang.", true);
        activeUploadTarget = null;
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/api/admin/upload-image`, {
          method: 'POST',
          headers: getAdminAuthHeaders(),
          body: formData
        });
        const data = await res.json();
        if (res.ok && data.url) {
          showToast("Rasm muvaffaqiyatli yuklandi!");
          if (activeUploadTarget.type === 'groupContext') {
            const urlInp = document.getElementById('groupImgUrlInput');
            if (urlInp) urlInp.value = data.url;
            saveGroupImage(data.url);
          } else if (activeUploadTarget.type === 'q1to35') {
            const qNum = activeUploadTarget.qNum;
            const urlInp = document.getElementById(`qImgUrlInput_${qNum}`);
            if (urlInp) urlInp.value = data.url;
            saveQuestionImage(qNum, data.url);
          } else {
            const qNum = activeUploadTarget.qNum;
            const urlInp = document.getElementById(`openImgUrlInput_${qNum}`);
            if (urlInp) urlInp.value = data.url;
            saveOpenQuestionImage(qNum, data.url);
          }
        } else {
          showToast("Rasmni yuklab bo'lmadi: " + (data.detail || "Noma'lum xatolik"), true);
        }
      } catch (err) {
        if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
          showToast("Server bilan ulanish yo'q! Bot va tunnel ishlab turganini tekshiring.", true);
          openApiConfigModal();
        } else {
          showToast("Rasm yuklashda xatolik: " + err.message, true);
        }
      } finally {
        activeUploadTarget = null;
      }
    }

    // ================= QUICK MASS KEYS MODAL =================
    function openQuickKeysModal() {
      document.getElementById('quickKeysModal').classList.add('active');
      const input = document.getElementById('quickKeysInput');
      // mavjud kalitlarni yig'ish
      let cur = [];
      for (let i = 1; i <= 35; i++) cur.push(answers1to35[i] || 'A');
      input.value = cur.join('');
      input.focus();
    }

    function applyQuickKeys() {
      const raw = document.getElementById('quickKeysInput').value.toUpperCase();
      // 1-32 uchun A-D, 33-35 uchun A-F qabul qilinadi
      const matched = raw.match(/[A-F]/g);
      if (!matched || matched.length === 0) {
        showToast("Hech qanday A–F harfi topilmadi!", true);
        return;
      }

      const count = Math.min(35, matched.length);
      for (let i = 1; i <= count; i++) {
        let key = matched[i - 1];
        if (i <= 32 && !['A', 'B', 'C', 'D'].includes(key)) {
          key = 'A';
        }
        selectKeyOption(i, key);
      }

      closeModal('quickKeysModal');
      showToast(`${count} ta savol kalitlari muvaffaqiyatli o'rnatildi!`);
      scheduleAutosave();
    }

    // ================= VIRTUAL MATEMATIKA KLAVIATURASI =================
    const greekLower = [
      [
        { key: 'φ', sub: 'phi' }, { key: 'σ', sub: 'sigma' }, { key: 'ϵ', sub: 'epsilon' },
        { key: 'ρ', sub: 'rho' }, { key: 'τ', sub: 'tau' }, { key: 'υ', sub: 'upsilon' },
        { key: 'θ', sub: 'theta' }, { key: 'ι', sub: 'iota' }, { key: 'ο', sub: 'omicron' }, { key: 'π', sub: 'pi' }
      ],
      [
        { key: 'α', sub: 'alpha' }, { key: 'δ', sub: 'delta' },
        { key: 'ϕ', sub: 'phi var' }, { key: 'γ', sub: 'gamma' }, { key: 'η', sub: 'eta' },
        { key: 'ξ', sub: 'xi' }, { key: 'κ', sub: 'kappa' }, { key: 'λ', sub: 'lambda' }
      ],
      [
        { key: '⇧', action: 'shift', special: true },
        { key: 'ζ', sub: 'zeta' }, { key: 'χ', sub: 'chi' }, { key: 'ψ', sub: 'psi' },
        { key: 'ω', sub: 'omega' }, { key: 'β', sub: 'beta' }, { key: 'ν', sub: 'nu' },
        { key: 'μ', sub: 'mu' },
        { key: '⌫', action: 'backspace', special: true }
      ],
      [
        { key: 'ε' }, { key: 'ϑ' }, { key: 'ϰ' }, { key: 'ϖ' }, { key: 'ϱ' },
        { key: '◀', action: 'left', special: true },
        { key: '▶', action: 'right', special: true },
        { key: '↵', action: 'enter', special: true }
      ]
    ];

    const greekUpper = [
      [
        { key: 'Φ', sub: 'Phi' }, { key: 'Σ', sub: 'Sigma' }, { key: 'Ε', sub: 'Epsilon' },
        { key: 'Ρ', sub: 'Rho' }, { key: 'Τ', sub: 'Tau' }, { key: 'Υ', sub: 'Upsilon' },
        { key: 'Θ', sub: 'Theta' }, { key: 'Ι', sub: 'Iota' }, { key: 'Ο', sub: 'Omicron' }, { key: 'Π', sub: 'Pi' }
      ],
      [
        { key: 'Α', sub: 'Alpha' }, { key: 'Δ', sub: 'Delta' },
        { key: 'Γ', sub: 'Gamma' }, { key: 'Η', sub: 'Eta' },
        { key: 'Ξ', sub: 'Xi' }, { key: 'Κ', sub: 'Kappa' }, { key: 'Λ', sub: 'Lambda' }
      ],
      [
        { key: '⇧', action: 'shift', special: true },
        { key: 'Ζ', sub: 'Zeta' }, { key: 'Χ', sub: 'Chi' }, { key: 'Ψ', sub: 'Psi' },
        { key: 'Ω', sub: 'Omega' }, { key: 'Β', sub: 'Beta' }, { key: 'Ν', sub: 'Nu' },
        { key: 'Μ', sub: 'Mu' },
        { key: '⌫', action: 'backspace', special: true }
      ],
      [
        { key: '◀', action: 'left', special: true },
        { key: '▶', action: 'right', special: true },
        { key: '↵', action: 'enter', special: true }
      ]
    ];

    const numKeysLayout = [
      [{ key: '7' }, { key: '8' }, { key: '9' }, { key: '÷' }, { key: '(' }, { key: ')' }],
      [{ key: '4' }, { key: '5' }, { key: '6' }, { key: '×' }, { key: '[' }, { key: ']' }],
      [{ key: '1' }, { key: '2' }, { key: '3' }, { key: '-' }, { key: 'x²' }, { key: '√' }],
      [{ key: '0' }, { key: '.' }, { key: '=' }, { key: '+' }, { key: '^' }, { key: '⌫', action: 'backspace', special: true }]
    ];

    const symbolKeysLayout = [
      [{ key: '∞' }, { key: '≠' }, { key: '≤' }, { key: '≥' }, { key: '∈' }, { key: '∉' }, { key: '⊂' }, { key: '⊃' }],
      [{ key: '∪' }, { key: '∩' }, { key: '±' }, { key: '∓' }, { key: '⊥' }, { key: '∥' }, { key: '∠' }, { key: '°' }],
      [{ key: '√' }, { key: '∛' }, { key: '∫' }, { key: '∑' }, { key: '∏' }, { key: '≈' }, { key: '≡' }, { key: '⌫', action: 'backspace', special: true }],
      [{ key: 'sin' }, { key: 'cos' }, { key: 'tan' }, { key: 'cot' }, { key: 'log' }, { key: 'ln' }, { key: 'lim' }, { key: '↵', action: 'enter', special: true }]
    ];

    const abcKeysLayout = [
      [{ key: 'q' }, { key: 'w' }, { key: 'e' }, { key: 'r' }, { key: 't' }, { key: 'y' }, { key: 'u' }, { key: 'i' }, { key: 'o' }, { key: 'p' }],
      [{ key: 'a' }, { key: 's' }, { key: 'd' }, { key: 'f' }, { key: 'g' }, { key: 'h' }, { key: 'j' }, { key: 'k' }, { key: 'l' }],
      [{ key: 'z' }, { key: 'x' }, { key: 'c' }, { key: 'v' }, { key: 'b' }, { key: 'n' }, { key: 'm' }, { key: '⌫', action: 'backspace', special: true }],
      [{ key: ' ', sub: 'bo\'shliq', special: true }, { key: '↵', action: 'enter', special: true }]
    ];

    function renderKeyboard(tabName) {
      currentKbTab = tabName;
      const container = document.getElementById('kbKeysBody');
      container.innerHTML = '';

      let layout = isGreekShiftActive ? greekUpper : greekLower;
      if (tabName === '123') layout = numKeysLayout;
      else if (tabName === 'symbols') layout = symbolKeysLayout;
      else if (tabName === 'abc') layout = abcKeysLayout;

      layout.forEach(row => {
        const rowDiv = document.createElement('div');
        rowDiv.className = 'kb-row';
        row.forEach(item => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = `kb-key ${item.special ? 'kb-key-special' : ''}`;

          if (item.action) {
            btn.innerHTML = `<span>${item.key}</span>`;
            btn.onmousedown = (e) => { e.preventDefault(); handleKbAction(item.action); };
          } else {
            btn.innerHTML = `
              <span>${item.key}</span>
              ${item.sub ? `<span class="kb-key-sub">${item.sub}</span>` : ''}
            `;
            btn.onmousedown = (e) => { e.preventDefault(); insertCharIntoInput(item.key); };
          }
          rowDiv.appendChild(btn);
        });
        container.appendChild(rowDiv);
      });
    }

    function switchKbTab(tabName) {
      document.querySelectorAll('.kb-tab').forEach(t => {
        if (t.getAttribute('data-tab') === tabName) {
          t.classList.add('active');
        } else {
          t.classList.remove('active');
        }
      });
      renderKeyboard(tabName);
    }

    function registerActiveInput(inp) {
      if (currentActiveInput && currentActiveInput !== inp) {
        currentActiveInput.classList.remove('active-input-focus');
      }
      currentActiveInput = inp;
      if (inp) inp.classList.add('active-input-focus');
      trackInputHistory(inp);
    }

    function openKeyboardForSpecificInput(inputId, tab) {
      const inp = document.getElementById(inputId);
      if (inp) {
        registerActiveInput(inp);
        inp.focus();
      }
      const kb = document.getElementById('mathKeyboard');
      kb.classList.add('active');
      if (tab) switchKbTab(tab);
    }

    function closeKeyboard() {
      document.getElementById('mathKeyboard').classList.remove('active');
      if (currentActiveInput) currentActiveInput.classList.remove('active-input-focus');
    }

    function insertCharIntoInput(char) {
      if (!currentActiveInput) {
        const any = document.querySelector('.answer-input, #testTitle');
        if (any) registerActiveInput(any);
      }
      if (!currentActiveInput) return;

      const start = currentActiveInput.selectionStart ?? currentActiveInput.value.length;
      const end = currentActiveInput.selectionEnd ?? currentActiveInput.value.length;
      const oldVal = currentActiveInput.value;

      currentActiveInput.value = oldVal.substring(0, start) + char + oldVal.substring(end);
      const newPos = start + char.length;
      currentActiveInput.setSelectionRange(newPos, newPos);
      currentActiveInput.focus();
      currentActiveInput.dispatchEvent(new Event('input', { bubbles: true }));
      trackInputHistory(currentActiveInput);
    }

    function handleKbAction(act) {
      if (act === 'shift') {
        isGreekShiftActive = !isGreekShiftActive;
        renderKeyboard(currentKbTab);
        return;
      }
      if (!currentActiveInput) return;

      const start = currentActiveInput.selectionStart;
      const end = currentActiveInput.selectionEnd;
      const oldVal = currentActiveInput.value;

      if (act === 'backspace') {
        if (start === end && start > 0) {
          currentActiveInput.value = oldVal.substring(0, start - 1) + oldVal.substring(end);
          currentActiveInput.setSelectionRange(start - 1, start - 1);
        } else if (start !== end) {
          currentActiveInput.value = oldVal.substring(0, start) + oldVal.substring(end);
          currentActiveInput.setSelectionRange(start, start);
        }
        currentActiveInput.dispatchEvent(new Event('input', { bubbles: true }));
        trackInputHistory(currentActiveInput);
      } else if (act === 'left') {
        if (start > 0) currentActiveInput.setSelectionRange(start - 1, start - 1);
      } else if (act === 'right') {
        if (end < oldVal.length) currentActiveInput.setSelectionRange(end + 1, end + 1);
      } else if (act === 'enter') {
        closeKeyboard();
      }
      currentActiveInput.focus();
    }

    function kbUndo() {
      if (!currentActiveInput || !inputHistory.has(currentActiveInput)) return;
      const data = inputHistory.get(currentActiveInput);
      if (data.pointer > 0) {
        data.pointer--;
        currentActiveInput.value = data.history[data.pointer];
        currentActiveInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }

    function kbRedo() {
      if (!currentActiveInput || !inputHistory.has(currentActiveInput)) return;
      const data = inputHistory.get(currentActiveInput);
      if (data.pointer < data.history.length - 1) {
        data.pointer++;
        currentActiveInput.value = data.history[data.pointer];
        currentActiveInput.dispatchEvent(new Event('input', { bubbles: true }));
      }
    }

    function kbCopy() {
      if (currentActiveInput && currentActiveInput.value) {
        navigator.clipboard.writeText(currentActiveInput.value);
        showToast("Matn nusxalandi!");
      }
    }

    // ================= CHECKBOX VA TOGGLELAR =================
    function toggleCheckbox(name) {
      checkboxStates[name] = !checkboxStates[name];
      const elem = document.getElementById(`cb_${name}`);
      if (elem) {
        if (checkboxStates[name]) {
          elem.classList.add('checked');
        } else {
          elem.classList.remove('checked');
        }
      }
      if (name === 'reqSub') {
        const wrap = document.getElementById('channelInputWrap');
        if (wrap) wrap.classList.toggle('open', checkboxStates.reqSub);
      }
      scheduleAutosave();
    }

    function setAccessType(type) {
      selectedAccessType = type || 'closed';
      scheduleAutosave();
    }

    function setAnswerMode(mode) {
      selectedAnswerMode = mode;
      const writeBtn = document.getElementById('tabModeWrite');
      const photoBtn = document.getElementById('tabModePhoto');
      const hint = document.getElementById('answerModeHint');

      if (mode === 'write') {
        writeBtn?.classList.add('active');
        photoBtn?.classList.remove('active');
        if (hint) hint.innerText = "O'quvchi har bir savol uchun javobni matn/formula orqali yozib jo'natadi";
      } else {
        writeBtn?.classList.remove('active');
        photoBtn?.classList.add('active');
        if (hint) hint.innerText = "O'quvchi yechim varaqasini rasmga olib jo'natadi va o'qituvchi tekshiradi";
      }
      scheduleAutosave();
    }

    function generateRandomCode() {
      const letters = "ABCDEFGHJKLMNPQRSTUVWXYZ";
      const randomLetter = letters[Math.floor(Math.random() * letters.length)];
      const randomNum = Math.floor(1000 + Math.random() * 9000);
      const code = `MS-${randomNum}-${randomLetter}`;
      document.getElementById('testCode').value = code;
      showToast(`Yangi test kodi: ${code}`);
      scheduleAutosave();
    }

    // ================= CUSTOM SELECT LOGIKASI =================
    function initSelect(id) {
      const wrap = document.getElementById(id);
      if (!wrap) return;
      const display = wrap.querySelector('.custom-select-display');
      const options = wrap.querySelector('.custom-select-options');
      const opts = wrap.querySelectorAll('.custom-option');

      display.addEventListener('click', (e) => {
        e.stopPropagation();
        document.querySelectorAll('.custom-select-options').forEach(o => {
          if (o !== options) o.classList.remove('open');
        });
        options.classList.toggle('open');
      });

      opts.forEach(opt => {
        opt.addEventListener('click', (e) => {
          e.stopPropagation();
          opts.forEach(o => o.classList.remove('selected'));
          opt.classList.add('selected');
          display.querySelector('.selected-text').innerText = opt.innerText;
          options.classList.remove('open');

          if (id === 'selectTestType') {
            handleTestTypeChange(opt.getAttribute('data-value'));
          }

          scheduleAutosave();
        });
      });
    }

    function handleTestTypeChange(type) {
      const timedWrap = document.getElementById('timedSettingsWrap');
      if (!timedWrap) return;
      if (type === 'timed') {
        timedWrap.style.display = 'flex';
      } else {
        timedWrap.style.display = 'none';
      }
    }

    document.addEventListener('click', () => {
      document.querySelectorAll('.custom-select-options').forEach(o => o.classList.remove('open'));
    });

    // ================= MAVZU ALMASHTIRISH (DARK/LIGHT) =================
    function updateThemeIcon(theme) {
      const icon = document.getElementById('themeIcon');
      if (!icon) return;
      if (theme === 'dark') {
        // Moon icon
        icon.innerHTML = `<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>`;
      } else {
        // Sun icon
        icon.innerHTML = `<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>`;
      }
    }

    const themeBtn = document.getElementById('themeToggle');
    themeBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('admin_theme', next);
      updateThemeIcon(next);
    });

    const savedTheme = localStorage.getItem('admin_theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    updateThemeIcon(savedTheme);

    function handleExitAdmin() {
      if (window.Telegram?.WebApp?.close) {
        window.Telegram.WebApp.close();
      } else if (window.history.length > 1) {
        window.history.back();
      } else {
        const dest = window.location.protocol === 'file:' ? 'index.html' : (window.location.pathname.includes('/web/') ? 'index.html' : (window.location.hostname.includes('github.io') ? 'index.html' : '/'));
        window.location.href = dest + window.location.search;
      }
    }

    // ================= TOAST VA MODALLAR =================
    let toastTimeoutId = null;
    function showToast(text, isError = false) {
      const t = document.getElementById('toastMsg');
      if (!t) return;
      if (toastTimeoutId) clearTimeout(toastTimeoutId);

      const iconSvg = isError
        ? '<svg class="icon" style="width:18px;height:18px;color:#ffffff;flex-shrink:0;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>'
        : '<svg class="icon" style="width:18px;height:18px;color:#ffffff;flex-shrink:0;" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';

      t.innerHTML = `${iconSvg}<span>${text}</span>`;
      t.className = 'toast' + (isError ? ' error' : '');
      t.classList.add('show');
      toastTimeoutId = setTimeout(() => {
        t.classList.remove('show');
      }, 4000);
    }

    function showAlertModal(title, message, isError = true, onAction = null) {
      const titleEl = document.getElementById('alertModalTitle');
      const bodyEl = document.getElementById('alertModalBody');
      const iconEl = document.getElementById('alertModalIcon');
      const btnEl = document.getElementById('btnAlertModalAction');

      if (titleEl) titleEl.innerText = title;
      if (bodyEl) bodyEl.innerText = message;
      if (iconEl) {
        if (isError) {
          iconEl.style.background = 'rgba(239, 68, 68, 0.12)';
          iconEl.style.color = 'var(--danger)';
          iconEl.innerHTML = '<svg class="icon" style="width:32px;height:32px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>';
        } else {
          iconEl.style.background = 'var(--success-light)';
          iconEl.style.color = 'var(--success)';
          iconEl.innerHTML = '<svg class="icon" style="width:32px;height:32px;" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>';
        }
      }

      if (btnEl) {
        btnEl.onclick = () => {
          closeModal('alertModal');
          if (typeof onAction === 'function') onAction();
        };
      }

      if (window.Telegram?.WebApp?.HapticFeedback) {
        try {
          window.Telegram.WebApp.HapticFeedback.notificationOccurred(isError ? 'error' : 'success');
        } catch (e) {}
      }

      openModal('alertModal');
    }

    function highlightInputError(inputId) {
      const el = document.getElementById(inputId);
      if (!el) return;
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      try { el.focus(); } catch (e) {}
      el.classList.add('input-error-highlight');
      setTimeout(() => {
        el.classList.remove('input-error-highlight');
      }, 3000);
    }

    function openModal(id) {
      const m = document.getElementById(id);
      if (m) m.classList.add('active');
    }

    function closeModal(id) {
      const m = document.getElementById(id);
      if (m) m.classList.remove('active');
    }

    function openConfirmModal(title, bodyText, onConfirm) {
      document.getElementById('confirmModalTitle').innerText = title;
      document.getElementById('confirmModalBody').innerText = bodyText;
      const btn = document.getElementById('btnConfirmAction');
      btn.onclick = () => {
        closeModal('confirmModal');
        onConfirm();
      };
      document.getElementById('confirmModal').classList.add('active');
    }

    // ================= AUTOSAVE & RESTORE =================
    function scheduleAutosave() {
      if (editingTestId) return; // Tahrirlash rejimida qoralama (draft) ga yozmaymiz
      clearTimeout(autosaveTimer);
      autosaveTimer = setTimeout(() => {
        try {
          const testType = document.querySelector('#selectTestType .custom-option.selected')?.getAttribute('data-value') || 'permanent';
          const draft = {
            title: document.getElementById('testTitle')?.value || '',
            testType: testType,
            code: document.getElementById('testCode')?.value || '',
            timeLimit: document.getElementById('testTimeLimit')?.value || '150',
            startTime: document.getElementById('startTime')?.value || '',
            endTime: document.getElementById('endTime')?.value || '',
            accessType: selectedAccessType,
            answerMode: selectedAnswerMode,
            checkboxStates,
            channelInput: document.getElementById('requiredChannelInput')?.value || '',
            answers1to35,
            groupContextData,
            questionsMeta,
            openQuestionsData,
            openQuestionsMeta
          };
          localStorage.setItem('admin_draft_test', JSON.stringify(draft));
        } catch (e) {
          // ignore localStorage error
        }
      }, 500);
    }

    function openApiConfigModal() {
      const current = localStorage.getItem('MS_API_BASE_URL') || API_BASE || '';
      const newUrl = prompt("Backend Server (yoki Cloudflare Tunnel) URL manzilini kiriting:\nMasalan: https://xxx.trycloudflare.com", current);
      if (newUrl !== null) {
        const clean = newUrl.trim().replace(/\/+$/, '');
        if (clean) {
          localStorage.setItem('MS_API_BASE_URL', clean);
          API_BASE = clean;
          showToast("Server manzili saqlandi! Sahifa yangilanmoqda...");
          setTimeout(() => window.location.reload(), 800);
        }
      }
    }

    function restoreDraft() {
      try {
        const raw = localStorage.getItem('admin_draft_test');
        if (!raw) {
          handleTestTypeChange('permanent');
          setAccessType('closed');
          return;
        }
        const draft = JSON.parse(raw);

        if (draft.title && document.getElementById('testTitle')) document.getElementById('testTitle').value = draft.title;
        if (draft.code && document.getElementById('testCode')) document.getElementById('testCode').value = draft.code;
        if (draft.timeLimit && document.getElementById('testTimeLimit')) document.getElementById('testTimeLimit').value = draft.timeLimit;
        if (draft.startTime && document.getElementById('startTime')) document.getElementById('startTime').value = draft.startTime;
        if (draft.endTime && document.getElementById('endTime')) document.getElementById('endTime').value = draft.endTime;

        if (draft.testType) {
          const opt = document.querySelector(`#selectTestType .custom-option[data-value="${draft.testType}"]`);
          if (opt) {
            document.querySelectorAll('#selectTestType .custom-option').forEach(o => o.classList.remove('selected'));
            opt.classList.add('selected');
            const selText = document.querySelector('#selectTestType .selected-text');
            if (selText) selText.innerText = opt.innerText;
            handleTestTypeChange(draft.testType);
          }
        } else {
          handleTestTypeChange('permanent');
        }

        setAccessType(draft.accessType || 'closed');
        if (draft.answerMode) setAnswerMode(draft.answerMode);

        if (draft.checkboxStates) {
          Object.assign(checkboxStates, draft.checkboxStates);
          ['autoCheck', 'hideAnswers', 'reqSub'].forEach(key => {
            const elem = document.getElementById(`cb_${key}`);
            if (elem) {
              if (checkboxStates[key]) elem.classList.add('checked');
              else elem.classList.remove('checked');
            }
          });
          if (checkboxStates.reqSub) {
            document.getElementById('channelInputWrap')?.classList.add('open');
          }
        }
        if (draft.channelInput) {
          const chanInp = document.getElementById('requiredChannelInput');
          if (chanInp) chanInp.value = draft.channelInput;
        }

        if (draft.answers1to35) Object.assign(answers1to35, draft.answers1to35);
        if (draft.groupContextData) {
          Object.assign(groupContextData, draft.groupContextData);
          if (groupContextData.text) {
            const el = document.getElementById('groupContextTextInput');
            if (el) el.value = groupContextData.text;
            saveGroupContextText(groupContextData.text);
          }
          if (groupContextData.image) {
            const el = document.getElementById('groupImgUrlInput');
            if (el) el.value = groupContextData.image;
            saveGroupImage(groupContextData.image);
          }
          if (groupContextData.options) {
            ['A', 'B', 'C', 'D', 'E', 'F'].forEach(letter => {
              const el = document.getElementById(`sharedOpt_${letter}`);
              if (el) el.value = groupContextData.options[letter] || '';
            });
          }
        }
        if (draft.questionsMeta) Object.assign(questionsMeta, draft.questionsMeta);
        if (draft.openQuestionsData) Object.assign(openQuestionsData, draft.openQuestionsData);
        if (draft.openQuestionsMeta) Object.assign(openQuestionsMeta, draft.openQuestionsMeta);

        initQuestions1to35();
        initOpenQuestions();
      } catch (e) {
        // ignore
      }
    }

    function resetCreateForm(forceNewCode = true) {
      editingTestId = null;
      const banner = document.getElementById('editModeBanner');
      if (banner) banner.style.display = 'none';

      // Test nomi
      const titleInput = document.getElementById('testTitle');
      if (titleInput) titleInput.value = '';

      // Test kodi
      const codeInput = document.getElementById('testCode');
      if (codeInput) {
        codeInput.disabled = false;
        if (forceNewCode) {
          const letters = "ABCDEFGHJKLMNPQRSTUVWXYZ";
          const randomLetter = letters[Math.floor(Math.random() * letters.length)];
          const randomNum = Math.floor(1000 + Math.random() * 9000);
          codeInput.value = `MS-${randomNum}-${randomLetter}`;
        } else {
          codeInput.value = '';
        }
      }

      // Vaqt va sanalar
      const timeInput = document.getElementById('testTimeLimit');
      if (timeInput) timeInput.value = '150';
      const startInput = document.getElementById('startTime');
      if (startInput) startInput.value = '';
      const endInput = document.getElementById('endTime');
      if (endInput) endInput.value = '';
      const channelInput = document.getElementById('requiredChannelInput');
      if (channelInput) channelInput.value = '';

      // Checkboxlar
      checkboxStates.autoCheck = true;
      checkboxStates.hideAnswers = false;
      checkboxStates.reqSub = false;
      ['autoCheck', 'hideAnswers', 'reqSub'].forEach(name => {
        const elem = document.getElementById(`cb_${name}`);
        if (elem) {
          if (checkboxStates[name]) elem.classList.add('checked');
          else elem.classList.remove('checked');
        }
      });
      const chanWrap = document.getElementById('channelInputWrap');
      if (chanWrap) chanWrap.classList.remove('open');

      // Savollar keshini tozalash
      for (let k in answers1to35) delete answers1to35[k];
      for (let k in questionsMeta) delete questionsMeta[k];
      for (let k in openQuestionsData) delete openQuestionsData[k];
      for (let k in openQuestionsMeta) delete openQuestionsMeta[k];

      groupContextData.text = '';
      groupContextData.image = '';
      groupContextData.options = { A: '', B: '', C: '', D: '', E: '', F: '' };
      const grpText = document.getElementById('groupContextTextInput');
      if (grpText) grpText.value = '';
      const grpPreview = document.getElementById('katexPreview_groupContext');
      if (grpPreview) grpPreview.innerHTML = "Formula ko'rinishi shu yerda chiqadi...";

      // Chiqarish tugmasini asliga qaytarish
      const publishBtn = document.getElementById('btnPublishTest');
      if (publishBtn) {
        publishBtn.innerHTML = `
          <svg class="icon" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          TESTNI CHIQARISH VA SAQLASH
        `;
        publishBtn.style.background = '';
      }

      // Lokal qoralamani tozalaymiz
      localStorage.removeItem('admin_draft_test');

      // Qayta initsializatsiya
      initQuestions1to32();
      initQuestions1to35();
      initOpenQuestions();
    }

    function confirmResetDraft() {
      openConfirmModal(
        "Formani tozalash",
        "Haqiqatan ham kiritilgan barcha ma'lumotlarni tozalab, yangitdan boshlamoqchimisiz?",
        () => {
          resetCreateForm(true);
          showToast("Forma muvaffaqiyatli tozalandi!");
        }
      );
    }

    // ================= TESTNI CHIQARISH VA SAQLASH (PUBLISH) =================
    async function publishFullTest() {
      const title = document.getElementById('testTitle').value.trim();
      let code = document.getElementById('testCode').value.trim().toUpperCase();
      const rawTime = parseInt(document.getElementById('testTimeLimit').value);
      if (isNaN(rawTime) || rawTime <= 0) {
        showAlertModal("Noto'g'ri vaqt", "Vaqt chegarasi musbat butun son (kamida 1 daqiqa) bo'lishi kerak!", true, () => {
          highlightInputError('testTimeLimit');
        });
        showToast("Vaqt chegarasi kamida 1 daqiqa bo'lishi kerak!", true);
        highlightInputError('testTimeLimit');
        return;
      }
      const timeLimit = Math.max(1, rawTime);
      const subject = "Matematika";
      const testType = document.querySelector('#selectTestType .custom-option.selected')?.getAttribute('data-value') || 'permanent';
      const actualAccessType = 'closed';
      const startTime = (testType === 'timed') ? document.getElementById('startTime').value.trim() : null;
      const endTime = (testType === 'timed') ? document.getElementById('endTime').value.trim() : null;
      const reqChannel = document.getElementById('requiredChannelInput')?.value?.trim() || '';

      if (!title) {
        showAlertModal("Test nomi kiritilmagan", "Iltimos, test nomini kiriting!", true, () => {
          highlightInputError('testTitle');
        });
        showToast("Iltimos, Test nomini kiriting!", true);
        highlightInputError('testTitle');
        return;
      }
      if (!code) {
        showAlertModal("Test kodi kiritilmagan", "Iltimos, o'quvchilar testga kirishi uchun Test kodini (kupon) kiriting yoki 'Tasodifiy kod' tugmasini bosing!", true, () => {
          highlightInputError('testCode');
        });
        showToast("Iltimos, Test kodini kiriting!", true);
        highlightInputError('testCode');
        return;
      }

      // Takroriy kod tekshiruvi (yangi test yaratishda)
      if (!editingTestId && window.myTestsCache && Array.isArray(window.myTestsCache)) {
        const isDuplicate = window.myTestsCache.some(t => (t.code || '').trim().toUpperCase() === code);
        if (isDuplicate) {
          showAlertModal(
            "Test kodi allaqachon mavjud!",
            `"${code}" kodli test bazangizda allaqachon mavjud!\n\nIltimos, boshqa kod kiriting yoki 'Tasodifiy kod' tugmasi orqali yangi kod oling.`,
            true,
            () => {
              highlightInputError('testCode');
            }
          );
          showToast(`"${code}" kodi allaqachon mavjud!`, true);
          highlightInputError('testCode');
          return;
        }
      }

      const publishBtn = document.getElementById('btnPublishTest');
      publishBtn.disabled = true;
      publishBtn.innerHTML = `Yuklanmoqda...`;

      // 45 ta savol massivini yig'amiz:
      const questionsPayload = [];

      // 1-32 Variantli klassik testlar:
      for (let i = 1; i <= 32; i++) {
        const correct = answers1to35[i] || 'A';
        const meta = questionsMeta[i] || {};
        questionsPayload.push({
          order_no: i,
          type: "Y-1",
          section: subject,
          difficulty_b: (i <= 10) ? -1.0 : (i <= 25) ? 0.0 : 1.0,
          text: meta.text || `${i}-savol: To'g'ri javob variantini tanlang.`,
          image_url: meta.image || null,
          options: { "A": "A", "B": "B", "C": "C", "D": "D" },
          correct_answer: correct
        });
      }

      // 33-35 Kontekstli / Guruhlangan testlar (6 ta variant A–F):
      const sharedOpts = {};
      ['A', 'B', 'C', 'D', 'E', 'F'].forEach(lettr => {
        sharedOpts[lettr] = (groupContextData.options && groupContextData.options[lettr]) || lettr;
      });

      for (let i = 33; i <= 35; i++) {
        const correct = answers1to35[i] || 'A';
        const meta = questionsMeta[i] || {};
        questionsPayload.push({
          order_no: i,
          type: "GROUPED",
          section: subject,
          difficulty_b: 1.0 + ((i - 32) * 0.3),
          text: meta.text || `${i}-savol: Mos to'g'ri javobni tanlang.`,
          image_url: meta.image || null,
          options: sharedOpts,
          correct_answer: correct
        });
      }

      // 36-45 Ochiq/Yozma testlar:
      for (let i = 36; i <= 45; i++) {
        const data = openQuestionsData[i] || { a: [''], b: [''] };
        const meta = openQuestionsMeta[i] || {};

        const subParts = [];
        const keys = Object.keys(data);
        keys.forEach((letter, idx) => {
          const ansList = (data[letter] || []).map(s => s.trim()).filter(Boolean);
          const firstAns = ansList.length > 0 ? ansList[0] : String(idx + 1);
          subParts.push({
            label: letter,
            correct_answer: firstAns,
            alternative_answers: ansList,
            difficulty_b: 1.0 + (idx * 0.4)
          });
        });

        questionsPayload.push({
          order_no: i,
          type: "O",
          section: subject,
          difficulty_b: 1.5,
          text: meta.text || `${i}-savol: Har bir band uchun to'g'ri natijani kiriting.`,
          image_url: meta.image || null,
          sub_parts: subParts
        });
      }

      if (!API_BASE && window.location.hostname.includes('github.io')) {
        publishBtn.disabled = false;
        publishBtn.innerHTML = `
          <svg class="icon" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          TESTNI CHIQARISH VA SAQLASH
        `;
        showAlertModal(
          "Server manzili kiritilmagan!",
          "Backend server URL si aniqlanmadi. Bot va tunnel ishlab turganini tekshiring, so'ng sahifani qayta yuklang.",
          true
        );
        showToast("Backend Server URL kiritilmagan!", true);
        return;
      }

      // Agar tahrirlash rejimida bo'lsa:
      if (editingTestId) {
        try {
          const res = await fetch(`${API_BASE}/api/admin/tests/${editingTestId}/update`, {
            method: 'POST',
            headers: getAdminAuthHeaders({ 'Content-Type': 'application/json' }),
            body: JSON.stringify({
              title: title,
              time_limit_min: timeLimit,
              hide_answers: checkboxStates.hideAnswers,
              questions: questionsPayload,
              grouped_context: {
                shared_context_text: groupContextData.text || "33–35-savollar uchun umumiy shart:",
                shared_image_url: groupContextData.image || null,
                shared_options: sharedOpts
              }
            })
          });
          const data = await res.json().catch(() => ({}));
          if (res.ok && data.success) {
            showToast("Test va javob kalitlari muvaffaqiyatli saqlandi!");
            showAlertModal(
              "Muvaffaqiyatli saqlandi!",
              `"${title}" testi va barcha javob kalitlari muvaffaqiyatli yangilandi.`,
              false,
              () => {
                cancelEditMode();
                switchAdminTab('list');
              }
            );
          } else {
            const errDetail = (data && (data.detail || data.message)) || "Saqlab bo'lmadi";
            showAlertModal("Saqlashda xatolik", errDetail, true);
            showToast("Xatolik: " + errDetail, true);
          }
        } catch (err) {
          showAlertModal("Xatolik yuz berdi", "Saqlashda xatolik: " + err.message, true);
          showToast("Xatolik: " + err.message, true);
        } finally {
          publishBtn.disabled = false;
          if (editingTestId) {
            publishBtn.innerHTML = `
              <svg class="icon" viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
              O'ZGARISHLARNI SAQLASH
            `;
          } else {
            publishBtn.innerHTML = `
              <svg class="icon" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
              TESTNI CHIQARISH VA SAQLASH
            `;
          }
        }
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/api/admin/create-test`, {
          method: 'POST',
          headers: getAdminAuthHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({
            creator_telegram_id: currentTelegramId,
            code: code,
            title: title,
            description: `${subject} bo'yicha test (1-32 yopiq, 33-35 guruhlangan, 36-45 ochiq).`,
            time_limit_min: timeLimit,
            test_type: testType,
            access_type: actualAccessType,
            start_time: startTime,
            end_time: endTime,
            auto_check: checkboxStates.autoCheck,
            hide_answers: checkboxStates.hideAnswers,
            required_channel: checkboxStates.reqSub ? reqChannel : null,
            questions: questionsPayload,
            grouped_context: {
              shared_context_text: groupContextData.text || "33–35-savollar uchun umumiy shart:",
              shared_image_url: groupContextData.image || null,
              shared_options: sharedOpts
            }
          })
        });

        let data = null;
        const cType = res.headers.get("content-type") || "";
        if (cType.includes("application/json")) {
          data = await res.json();
        } else {
          const rawText = await res.text();
          if (rawText.trim().startsWith("<") && window.location.hostname.includes("github.io")) {
            throw new Error("GitHub Pages faqat statik sayt, unda backend server ishlamaydi. Iltimos, server manzilini to'g'ri kiriting!");
          }
          throw new Error(`Server xatosi (${res.status})`);
        }

        if (res.ok && data.success) {
          lastCreatedTestCode = data.code;
          resetCreateForm(true); // Yangi test uchun formani to'liq tozalab qo'yamiz

          document.getElementById('successModalCode').innerText = data.code;
          document.getElementById('successModalDesc').innerText = `"${title}" testi muvaffaqiyatli saqlandi va Telegram botingizga (@ms_matematikabot) xabar yuborildi. O'quvchilar ushbu kod orqali testda qatnashishlari mumkin!`;
          document.getElementById('successModal').classList.add('active');

          showToast(`Test saqlandi! Kod: ${data.code}`);
          loadMyTests();
        } else {
          const errDetail = (data && (data.detail || data.message)) || "Yuklab bo'lmadi";
          const isDup = errDetail.toLowerCase().includes('allaqachon mavjud') || errDetail.toLowerCase().includes('mavjud') || errDetail.toLowerCase().includes('kod');
          if (isDup) {
            showAlertModal(
              "Test kodi band!",
              `"${code}" kodli test bazada allaqachon mavjud!\n\nIltimos, boshqa kod kiriting yoki 'Tasodifiy kod' tugmasi orqali yangi kod oling.`,
              true,
              () => {
                highlightInputError('testCode');
              }
            );
            highlightInputError('testCode');
          } else {
            showAlertModal("Testni saqlashda xatolik", errDetail, true);
          }
          showToast("Xatolik: " + errDetail, true);
        }
      } catch (err) {
        if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
          showAlertModal(
            "Server bilan aloqa yo'q!",
            "Server yoki bot bilan ulanish uzildi. Iltimos, bot va server ishlab turganini tekshiring yoki yuqoridagi 'Server sozlamasi' orqali manzilni yangilang.",
            true,
            () => {
              openApiConfigModal();
            }
          );
          showToast("Server bilan ulanish uzildi!", true);
          // Server offline — foydalanuvchiga toast orqali xabar berildi
        } else {
          showAlertModal("Xatolik yuz berdi", "Server bilan ulanishda xatolik: " + err.message, true);
          showToast("Server bilan ulanishda xatolik: " + err.message, true);
        }
      } finally {
        publishBtn.disabled = false;
        publishBtn.innerHTML = `
          <svg class="icon" viewBox="0 0 24 24"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
          TESTNI CHIQARISH VA SAQLASH
        `;
      }
    }

    function copySuccessTestCode() {
      if (!lastCreatedTestCode) return;
      const text = `🎯 Milliy Sertifikat Test Sinovi\n\n📝 Test kodi: ${lastCreatedTestCode}\n🤖 Test topshirish boti: @ms_matematikabot\n🔗 Havola: https://t.me/ms_matematikabot?start=${encodeURIComponent(lastCreatedTestCode)}\n\n💡 O'quvchilar botga kirib yoki havolani bosib, testda qatnashishlari mumkin!`;
      navigator.clipboard.writeText(text);
      showToast("Kod va bot manzili nusxalandi!");
    }

    function viewCreatedTest() {
      if (!lastCreatedTestCode) return;
      const base = window.location.pathname.includes('/web/') ? 'index.html' : (window.location.hostname.includes('github.io') ? 'index.html' : '/');
      const apiParam = API_BASE ? `&api=${encodeURIComponent(API_BASE)}` : '';
      window.location.href = `${base}?code=${encodeURIComponent(lastCreatedTestCode)}${apiParam}`;
    }

    // ================= MENING TESTLARIM (TAB 2) =================
    async function loadMyTests() {
      const container = document.getElementById('testsListContainer');
      container.innerHTML = '<div style="text-align:center; padding:30px 10px; color:var(--text-sub);">Testlar yuklanmoqda...</div>';

      if (!API_BASE && window.location.hostname.includes('github.io')) {
        container.innerHTML = `
          <div style="text-align:center; padding:30px 16px; color:var(--danger);">
            <p style="font-weight:600; margin-bottom:8px;">Server manzili ulanmagan!</p>
            <p style="font-size:12px; color:var(--text-sub); margin-bottom:12px;">Testlar ro'yxatini yuklash uchun server manzilini kiriting.</p>
            <button type="button" class="btn-action-small" style="background:var(--primary); color:#fff; border-color:var(--primary);" onclick="openApiConfigModal()">
              <span style="display:inline-flex; align-items:center; gap:6px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg> Server sozlamasi</span>
            </button>
          </div>
        `;
        return;
      }

      try {
        const res = await fetch(`${API_BASE}/api/admin/tests/${currentTelegramId || 0}`, {
          headers: getAdminAuthHeaders()
        });
        let data = { tests: [] };
        const cType = res.headers.get("content-type") || "";
        if (cType.includes("application/json")) {
          data = await res.json();
        } else {
          throw new Error("Server noto'g'ri format qaytardi");
        }

        if (res.ok && Array.isArray(data.tests)) {
          window.myTestsCache = data.tests;
          document.getElementById('myTestsCount').innerText = data.tests.length;

          if (data.tests.length === 0) {
            container.innerHTML = `
              <div style="text-align:center; padding:40px 16px; color:var(--text-sub);">
                <div style="margin-bottom:12px; display:flex; justify-content:center;">
                  <svg class="icon" style="width:36px; height:36px; color:var(--text-sub);" viewBox="0 0 24 24"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>
                </div>
                <div style="font-weight:600; margin-bottom:4px; color:var(--text);">Hozircha testlar yo'q</div>
                <p style="font-size:12px;">Birinchi testingizni "Yangi test yaratish" bo'limida yarating!</p>
                <button type="button" class="btn-action-small" style="margin-top:12px; background:var(--primary); color:#fff; border-color:var(--primary);" onclick="switchAdminTab('create')">
                  + Yangi test yaratish
                </button>
              </div>
            `;
            return;
          }

          container.innerHTML = data.tests.map(t => `
            <div class="test-card" id="testCard_${t.id}">
              <div class="test-card-header">
                <span class="test-card-code">${escapeHtml(t.code)}</span>
                <span class="test-card-status ${t.is_active ? 'active' : 'inactive'}" id="statusBadge_${t.id}">
                  ${t.is_active ? 'Faol' : 'To\'xtatilgan'}
                </span>
              </div>
              <div class="test-card-title">${escapeHtml(t.title)}</div>
              <div class="test-card-meta">
                <span>Savollar: <b>${t.question_count} ta</b></span>
                <span>Vaqt: <b>${t.time_limit_min} daqiqa</b></span>
                <span>Qatnashuvchilar: <b>${t.attempts_count} ta</b></span>
                <span>O'rtacha ball: <b>${t.avg_score}</b></span>
              </div>
              <div class="test-card-actions">
                <button type="button" class="btn-action-small" onclick="copyCodeText('${escapeHtml(t.code)}')">
                  <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
                  Kodni nusxalash
                </button>
                <button type="button" class="btn-action-small" onclick="openTestStatsModal(${t.id})" style="color:#059669; font-weight:600; border-color:#a7f3d0;">
                  <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>
                  Statistika
                </button>
                <button type="button" class="btn-action-small" onclick="openEditTest(${t.id})" style="color:var(--primary); font-weight:600; border-color:var(--primary-border);">
                  <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>
                  Tahrirlash
                </button>
                <button type="button" class="btn-action-small" onclick="window.open((window.location.pathname.includes('/web/') ? 'index.html' : (window.location.hostname.includes('github.io') ? 'index.html' : '/')) + '?code=' + encodeURIComponent('${escapeHtml(t.code)}') + (API_BASE ? '&api=' + encodeURIComponent(API_BASE) : ''), '_blank')">
                  <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>
                  Ko'rish
                </button>
                <button type="button" class="btn-action-small" onclick="toggleTestStatus(${t.id})">
                  ${t.is_active ? 'To\'xtatish' : 'Faollashtirish'}
                </button>
                ${t.code !== 'STANDART' ? `
                  <button type="button" class="btn-action-small danger" onclick="confirmDeleteTest(${t.id}, '${escapeHtml(t.code)}')">
                    <svg class="icon" style="width:13px; height:13px;" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    O'chirish
                  </button>
                ` : ''}
              </div>
            </div>
          `).join('');
        }
      } catch (err) {
        if (err.message && (err.message.includes('Failed to fetch') || err.message.includes('NetworkError'))) {
          container.innerHTML = `
            <div style="text-align:center; padding:30px 16px; color:var(--danger);">
              <p style="font-weight:600; margin-bottom:8px;">Server bilan aloqa uzildi!</p>
              <p style="font-size:12px; color:var(--text-sub); margin-bottom:12px;">Bot va tunnel ishlab turganini tekshiring.</p>
              <button type="button" class="btn-action-small" style="background:var(--primary); color:#fff; border-color:var(--primary);" onclick="openApiConfigModal()">
                <span style="display:inline-flex; align-items:center; gap:6px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg> Server sozlamasi</span>
              </button>
            </div>
          `;
        } else {
          container.innerHTML = `<div style="color:var(--danger); padding:20px; text-align:center;">Yuklashda xatolik: ${err.message}</div>`;
        }
      }
    }

    function copyCodeText(code) {
      navigator.clipboard.writeText(code);
      showToast(`Test kodi nusxalandi: ${code}`);
    }

    let currentTestStatsData = null;

    async function openTestStatsModal(testId) {
      try {
        showToast("Statistika yuklanmoqda...");
        const res = await fetch(`${API_BASE}/api/admin/tests/${testId}/stats`, {
          headers: getAdminAuthHeaders()
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Statistikani yuklab bo'lmadi");
        }
        const data = await res.json();
        currentTestStatsData = data;

        // Sarlavha va meta
        const titleElem = document.getElementById('statsModalTitle');
        if (titleElem) titleElem.innerText = `${data.test_code} — Natijalar va statistika`;

        const subElem = document.getElementById('statsModalSubtitle');
        if (subElem) subElem.innerText = `${data.test_title} (${data.question_count} ta savol, ${data.time_limit_min} daqiqa)`;

        // KPIlar
        const partElem = document.getElementById('kpiParticipants');
        if (partElem) partElem.innerText = `${data.total_participants} ta`;

        const avgElem = document.getElementById('kpiAvgScore');
        if (avgElem) avgElem.innerText = `${data.avg_score}`;

        const highElem = document.getElementById('kpiHighestScore');
        if (highElem) highElem.innerText = `${data.highest_score}`;

        const certPercent = data.total_participants > 0 ? Math.round((data.certified_count / data.total_participants) * 100) : 0;
        const certElem = document.getElementById('kpiCertified');
        if (certElem) certElem.innerText = `${data.certified_count} ta (${certPercent}%)`;

        // Inputni tozalash va ro'yxatni chizish
        const searchInput = document.getElementById('statsSearchInput');
        if (searchInput) searchInput.value = '';

        renderStatsParticipants(data.participants);

        openModal('testStatsModal');
      } catch (err) {
        showToast("Xatolik: " + err.message, true);
      }
    }

    function renderStatsParticipants(participants) {
      const container = document.getElementById('statsTableContainer');
      const footerInfo = document.getElementById('statsFooterInfo');
      if (!container) return;

      if (!participants || participants.length === 0) {
        container.innerHTML = `
          <div style="text-align:center; padding:30px 16px; color:var(--text-sub);">
            <p style="font-size:13px; font-weight:600;">Hozircha hech kim ushbu testni topshirmagan.</p>
            <p style="font-size:11px; margin-top:4px;">Test kodi o'quvchilarga ulashilgach, natijalar shu yerda ko'rinadi.</p>
          </div>
        `;
        if (footerInfo) footerInfo.innerText = "Jami: 0 ta natija";
        return;
      }

      if (footerInfo) footerInfo.innerText = `Jami: ${participants.length} ta natija`;

      container.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:8px;">
          ${participants.map((p, idx) => {
            const isCert = Boolean(p.is_certified);
            const gradeBg = isCert ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.08)';
            const gradeColor = isCert ? '#059669' : '#dc2626';
            const gradeBorder = isCert ? 'rgba(16, 185, 129, 0.25)' : 'rgba(239, 68, 68, 0.2)';
            const gradeLabel = isCert ? (p.grade || 'Sertifikat') : 'Sertifikatsiz';

            return `
              <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:10px 14px; display:flex; align-items:center; justify-content:space-between; gap:12px; cursor:pointer; transition:all 0.15s ease;"
                   onclick="openAttemptDetailsModal(${p.attempt_id})"
                   onmouseover="this.style.borderColor='var(--primary)'; this.style.transform='translateY(-1px)';"
                   onmouseout="this.style.borderColor='var(--border)'; this.style.transform='none';">
                <div style="display:flex; align-items:center; gap:12px; min-width:0;">
                  <div style="width:30px; height:30px; border-radius:50%; background:${idx === 0 ? '#fef3c7' : (idx === 1 ? '#f1f5f9' : (idx === 2 ? '#ffedd5' : 'var(--border)'))}; color:${idx === 0 ? '#b45309' : (idx === 1 ? '#475569' : (idx === 2 ? '#c2410c' : 'var(--text-sub)'))}; display:flex; align-items:center; justify-content:center; font-size:12px; font-weight:800; flex-shrink:0; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
                    ${p.rank || idx + 1}
                  </div>
                  <div style="min-width:0;">
                    <div style="font-size:13px; font-weight:700; color:var(--text); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                      ${escapeHtml(p.full_name)}
                    </div>
                    <div style="font-size:11px; color:var(--text-sub); display:flex; align-items:center; gap:8px; margin-top:3px; flex-wrap:wrap;">
                      ${p.phone_number ? `<span style="display:inline-flex; align-items:center; gap:3px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>${escapeHtml(p.phone_number)}</span>` : ''}
                      ${p.username ? `<span style="display:inline-flex; align-items:center; gap:2px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"></circle><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path></svg>${escapeHtml(p.username)}</span>` : ''}
                      <span style="display:inline-flex; align-items:center; gap:3px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>${p.finished_at || p.started_at}</span>
                    </div>
                  </div>
                </div>

                <div style="text-align:right; flex-shrink:0; display:flex; flex-direction:column; align-items:flex-end; gap:3px;">
                  <div style="display:flex; align-items:center; gap:6px;">
                    <span style="font-size:10px; font-weight:700; padding:2px 6px; border-radius:5px; background:${gradeBg}; color:${gradeColor}; border:1px solid ${gradeBorder};">
                      ${gradeLabel}
                    </span>
                    <span style="font-size:16px; font-weight:800; color:var(--primary); line-height:1;">
                      ${p.final_score} <span style="font-size:11px; font-weight:500; color:var(--text-sub);">ball</span>
                    </span>
                  </div>
                  <div style="display:flex; align-items:center; gap:6px; margin-top:2px;">
                    <span style="font-size:11px; color:var(--text-sub); font-weight:500;">
                      (${p.raw_score} ta to'g'ri)
                    </span>
                    <span style="font-size:10px; font-weight:700; color:var(--primary); background:var(--primary-light); border:1px solid var(--primary-border); padding:2px 6px; border-radius:4px; display:inline-flex; align-items:center; gap:3px;">
                      <span>Tahlil</span>
                      <svg class="icon icon-xs" viewBox="0 0 24 24"><polyline points="9 18 15 12 9 6"></polyline></svg>
                    </span>
                    <button type="button" class="btn-participant-delete"
                            onclick="event.stopPropagation(); deleteAttempt(${p.attempt_id}, '${escapeHtml(p.full_name)}')"
                            title="Talabgor natijasini o'chirish">
                      <svg class="icon icon-xs" viewBox="0 0 24 24"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
                    </button>
                  </div>
                </div>
              </div>
            `;
          }).join('')}
        </div>
      `;
    }

    function filterStatsList(query) {
      if (!currentTestStatsData || !currentTestStatsData.participants) return;
      const q = query.trim().toLowerCase();
      if (!q) {
        renderStatsParticipants(currentTestStatsData.participants);
        return;
      }
      const filtered = currentTestStatsData.participants.filter(p => {
        return (p.full_name && p.full_name.toLowerCase().includes(q)) ||
               (p.phone_number && p.phone_number.toLowerCase().includes(q)) ||
               (p.username && p.username.toLowerCase().includes(q));
      });
      renderStatsParticipants(filtered);
    }

    // ================= SUPER ADMIN TIZIM STATISTIKASI =================
    const SUPER_ADMIN_ID = 1685356708;

    function checkAndShowSuperAdminUi() {
      const superBtn = document.getElementById('navSuperStatsBtn');
      if (!superBtn) return;
      if (Number(currentTelegramId) === SUPER_ADMIN_ID) {
        superBtn.style.display = 'inline-flex';
      }
    }

    async function openSuperStatsModal() {
      const modal = document.getElementById('superStatsModal');
      const body = document.getElementById('superStatsModalBody');
      if (!modal || !body) return;

      openModal('superStatsModal');
      body.innerHTML = `
        <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; padding:40px 20px; color:var(--text-sub);">
          <svg class="icon" style="width:32px; height:32px; animation:spin 1s linear infinite; margin-bottom:12px;" viewBox="0 0 24 24"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
          <div style="font-size:13px; font-weight:500;">Tizim statistikasi tahlil qilinmoqda...</div>
        </div>
      `;

      try {
        const res = await fetch(`${API_BASE}/api/admin/super-stats`, {
          headers: getAdminAuthHeaders()
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Statistikani yuklab bo'lmadi (Ruxsat faqat Super Adminga)");
        }
        const data = await res.json();
        const stats = data.stats;
        if (!stats) throw new Error("Statistika ma'lumotlari bo'sh qaytdi");

        renderSuperStatsContent(stats);
      } catch (err) {
        body.innerHTML = `
          <div style="padding:24px; text-align:center; color:var(--danger); background:var(--card-sub); border:1px solid var(--border); border-radius:10px;">
            <svg class="icon" style="width:32px; height:32px; margin-bottom:10px;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            <div style="font-weight:700; font-size:15px; margin-bottom:6px;">Yuklashda xatolik yuz berdi</div>
            <div style="font-size:13px; color:var(--text-sub); line-height:1.5;">${escapeHtml(err.message)}</div>
          </div>
        `;
      }
    }

    function renderSuperStatsContent(stats) {
      const body = document.getElementById('superStatsModalBody');
      if (!body) return;

      const activePct = stats.total_users > 0 ? Math.round((stats.active_takers / stats.total_users) * 100) : 0;
      const inactivePct = Math.max(0, 100 - activePct);

      body.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:16px;">
          <!-- FOYDALANUVCHILAR VA O'SISH -->
          <div>
            <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-sub); margin-bottom:8px; display:flex; align-items:center; gap:6px;">
              <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path></svg>
              Foydalanuvchilar va O'sish dinamikasi
            </div>
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px;">
              <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:var(--text-sub);">Jami bot a'zolari</div>
                <div style="font-size:22px; font-weight:800; color:var(--primary); margin-top:2px;">${stats.total_users}</div>
                <div style="font-size:10px; color:var(--text-sub); margin-top:2px;">ro'yxatdan o'tgan</div>
              </div>
              <div style="background:var(--card-sub); border:1px solid rgba(16, 185, 129, 0.35); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:#10b981; font-weight:600;">Oxirgi 7 kun</div>
                <div style="font-size:22px; font-weight:800; color:#10b981; margin-top:2px;">+${stats.users_week}</div>
                <div style="font-size:10px; color:var(--text-sub); margin-top:2px;">haftalik yangi o'sish</div>
              </div>
              <div style="background:var(--card-sub); border:1px solid rgba(59, 130, 246, 0.35); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:#3b82f6; font-weight:600;">Bugun (24 soat)</div>
                <div style="font-size:22px; font-weight:800; color:#3b82f6; margin-top:2px;">+${stats.users_today}</div>
                <div style="font-size:10px; color:var(--text-sub); margin-top:2px;">kunlik yangi o'sish</div>
              </div>
              <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:var(--text-sub);">Telefon kiritilgan</div>
                <div style="font-size:22px; font-weight:800; color:var(--text); margin-top:2px;">${stats.users_with_phone}</div>
                <div style="font-size:10px; color:var(--text-sub); margin-top:2px;">kontakt tasdiqlangan</div>
              </div>
            </div>
          </div>

          <!-- FOYDALANUVCHILAR FAOLLIK STRUKTURASI -->
          <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:12px 14px;">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:8px;">
              <span style="font-size:12px; font-weight:700; color:var(--text);">Foydalanuvchilar faollik strukturasi</span>
              <span style="font-size:11px; color:var(--text-sub); font-weight:500;">Faollik: ${activePct}%</span>
            </div>
            <div style="display:flex; justify-content:space-between; font-size:11px; margin-bottom:6px;">
              <span>Test topshirgan faollar: <b style="color:#10b981;">${stats.active_takers} ta (${activePct}%)</b></span>
              <span>Hali test topshirmaganlar: <b style="color:var(--text-sub);">${stats.inactive_users} ta (${inactivePct}%)</b></span>
            </div>
            <div style="height:8px; border-radius:4px; background:var(--border); overflow:hidden; display:flex;">
              <div style="width:${activePct}%; background:#10b981;"></div>
              <div style="width:${inactivePct}%; background:rgba(156, 163, 175, 0.4);"></div>
            </div>
          </div>

          <!-- TESTLAR VA NATIJALAR -->
          <div>
            <div style="font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; color:var(--text-sub); margin-bottom:8px; display:flex; align-items:center; gap:6px;">
              <svg class="icon" style="width:14px; height:14px;" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
              Testlar, Urinishlar va Natijalar
            </div>
            <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(130px, 1fr)); gap:10px;">
              <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:var(--text-sub);">Yaratilgan testlar</div>
                <div style="font-size:22px; font-weight:800; color:var(--text); margin-top:2px;">${stats.total_tests}</div>
                <div style="font-size:10px; color:#10b981; margin-top:2px;">shundan ${stats.active_tests} ta faol</div>
              </div>
              <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:var(--text-sub);">Jami urinishlar</div>
                <div style="font-size:22px; font-weight:800; color:var(--text); margin-top:2px;">${stats.total_attempts}</div>
                <div style="font-size:10px; color:var(--text-sub); margin-top:2px;">${stats.completed_attempts} ta yakunlangan</div>
              </div>
              <div style="background:var(--card-sub); border:1px solid rgba(245, 158, 11, 0.35); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:#f59e0b; font-weight:600;">Sertifikatlar</div>
                <div style="font-size:22px; font-weight:800; color:#f59e0b; margin-top:2px;">${stats.certified_attempts}</div>
                <div style="font-size:10px; color:var(--text-sub); margin-top:2px;">${stats.cert_percent}% muvaffaqiyat</div>
              </div>
              <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:12px; text-align:center;">
                <div style="font-size:11px; color:var(--text-sub);">O'rtacha ball</div>
                <div style="font-size:22px; font-weight:800; color:var(--primary); margin-top:2px;">${stats.avg_score}</div>
                <div style="font-size:10px; color:var(--text-sub); margin-top:2px;">70 ballik tizimda</div>
              </div>
            </div>
          </div>

          <!-- BOSHQARUV TIZIMI -->
          <div style="background:var(--card-sub); border:1px solid var(--border); border-radius:10px; padding:12px 14px; display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:10px;">
            <div style="display:flex; align-items:center; gap:8px;">
              <div style="width:30px; height:30px; border-radius:6px; background:rgba(245, 158, 11, 0.15); color:#f59e0b; display:flex; align-items:center; justify-content:center;">
                <svg class="icon" style="width:16px; height:16px;" viewBox="0 0 24 24"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon></svg>
              </div>
              <div>
                <div style="font-size:12px; font-weight:700; color:var(--text);">Adminlar tarkibi</div>
                <div style="font-size:11px; color:var(--text-sub);">Tizimda jami <b>${stats.total_admins} ta</b> tayinlangan admin mavjud</div>
              </div>
            </div>
            <div style="font-size:11px; color:var(--text-sub); text-align:right;">
              Yangilangan vaqt:<br><b style="color:var(--text);">${escapeHtml(stats.generated_at || '')}</b>
            </div>
          </div>
        </div>
      `;
    }

    window.openSuperStatsModal = openSuperStatsModal;

    // ================= TELEGRAMGA BIR BOSISHDA POST YUBORISH =================

    async function sendStatsDirectlyToTelegram() {
      if (!currentTestStatsData || !currentTestStatsData.test_id) {
        showToast("Statistika ma'lumotlari mavjud emas!", true);
        return;
      }

      const btn = document.getElementById('btnSendStatsTelegram');
      const origHtml = btn ? btn.innerHTML : '';
      if (btn) {
        btn.disabled = true;
        btn.innerHTML = `
          <svg class="icon spin" style="width:14px; height:14px;" viewBox="0 0 24 24"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg>
          <span>Yuborilmoqda...</span>
        `;
      }

      try {
        const res = await fetch(`${API_BASE}/api/admin/tests/${currentTestStatsData.test_id}/send-telegram-post`, {
          method: 'POST',
          headers: getAdminAuthHeaders({ 'Content-Type': 'application/json' }),
          body: JSON.stringify({}) // bo'sh bo'lsa server to'g'ridan-to'g'ri adminning o'ziga yuboradi
        });

        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error(data.detail || "Telegramga yuborib bo'lmadi");
        }

        // Shuningdek matnni clipboardga nusxalab qo'yamiz (ixtiyoriy foydalanish uchun)
        if (data.post_text) {
          try {
            await navigator.clipboard.writeText(data.post_text);
          } catch (e) {}
        }

        showToast("Natijalar Telegram profilingizga yuborildi!");
      } catch (err) {
        showToast("Xatolik: " + err.message, true);
      } finally {
        if (btn) {
          btn.disabled = false;
          btn.innerHTML = origHtml;
        }
      }
    }

    // ================= O'QUVCHINING HAR BIR SAVOLINI TAHLIL QILISH MODALI =================
    let currentAttemptDetails = null;
    let currentAttemptFilter = 'all';

    function setAttemptFilter(filter) {
      currentAttemptFilter = filter;
      ['all', 'correct', 'wrong', 'unanswered'].forEach(f => {
        const btn = document.getElementById(`btnFilter${f.charAt(0).toUpperCase() + f.slice(1)}`);
        if (btn) btn.classList.toggle('active', f === filter);
      });
      renderAttemptAnswersList();
    }

    function jumpToQuestion(orderNo) {
      if (currentAttemptDetails && currentAttemptDetails.breakdown) {
        const q = currentAttemptDetails.breakdown.find(x => x.order_no === orderNo);
        if (q) {
          const qStatus = (q.status === 'partially_correct') ? 'wrong' : q.status;
          if (currentAttemptFilter !== 'all' && currentAttemptFilter !== qStatus) {
            setAttemptFilter('all');
          }
        }
      }

      setTimeout(() => {
        const elem = document.getElementById(`analysisCard_${orderNo}`);
        if (elem) {
          elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
          elem.classList.add('highlight');
          setTimeout(() => elem.classList.remove('highlight'), 1800);
        }
      }, 60);
    }

    function renderAttemptAnswersList() {
      const container = document.getElementById('attemptAnswersList');
      if (!container || !currentAttemptDetails) return;

      const breakdown = currentAttemptDetails.breakdown || [];
      let filtered = breakdown;
      if (currentAttemptFilter === 'correct') {
        filtered = breakdown.filter(q => q.status === 'correct');
      } else if (currentAttemptFilter === 'wrong') {
        filtered = breakdown.filter(q => q.status === 'wrong' || q.status === 'partially_correct');
      } else if (currentAttemptFilter === 'unanswered') {
        filtered = breakdown.filter(q => q.status === 'unanswered');
      }

      if (filtered.length === 0) {
        container.innerHTML = `
          <div style="text-align:center; padding:30px 16px; color:var(--text-sub); background:var(--card-sub); border:1px dashed var(--border); border-radius:10px;">
            <div style="font-size:13px; font-weight:700; color:var(--text); margin-bottom:4px;">Ushbu toifada savollar mavjud emas</div>
            <div style="font-size:11px;">Barcha savollarni ko'rish uchun yuqoridagi "Barchasi" filtrini bosing.</div>
          </div>
        `;
        return;
      }

      container.innerHTML = filtered.map(q => {
        if (q.sub_parts && Array.isArray(q.sub_parts) && q.sub_parts.length > 0) {
          // Ochiq savol (36-45)
          const isAllCorr = q.status === 'correct';
          const isPartCorr = q.status === 'partially_correct';
          const isWrong = q.status === 'wrong';
          const badgeBg = isAllCorr ? 'rgba(16, 185, 129, 0.15)' : (isPartCorr ? 'rgba(245, 158, 11, 0.15)' : (isWrong ? 'rgba(239, 68, 68, 0.15)' : 'rgba(148, 163, 184, 0.15)'));
          const badgeColor = isAllCorr ? '#059669' : (isPartCorr ? '#d97706' : (isWrong ? '#dc2626' : '#64748b'));
          const badgeIcon = isAllCorr 
            ? `<svg class="icon icon-xs" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>` 
            : (isPartCorr 
                ? `<svg class="icon icon-xs" viewBox="0 0 24 24"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>` 
                : (isWrong 
                    ? `<svg class="icon icon-xs" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>` 
                    : `<svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><line x1="9" y1="12" x2="15" y2="12"></line></svg>`));
          const badgeText = isAllCorr ? "To'liq to'g'ri" : (isPartCorr ? "Qisman to'g'ri" : (isWrong ? "Noto'g'ri" : "Yechilmagan"));

          return `
            <div class="question-analysis-card" id="analysisCard_${q.order_no}">
              <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span class="q-order-badge open">#${q.order_no}-savol</span>
                  <span style="font-size:11px; color:var(--text-sub); font-weight:500;">Ochiq (yozma) savol</span>
                </div>
                <span style="font-size:11px; font-weight:700; padding:2px 8px; border-radius:6px; background:${badgeBg}; color:${badgeColor}; border:1px solid ${badgeColor}30; display:inline-flex; align-items:center; gap:4px;">
                  ${badgeIcon}
                  <span>${badgeText}</span>
                </span>
              </div>

              <div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:8px; margin-top:2px;">
                ${q.sub_parts.map(p => {
                  const pCorr = p.is_correct;
                  const pAns = p.user_answer ? escapeHtml(p.user_answer) : "(bo'sh)";
                  const pStatusColor = pCorr ? '#059669' : (p.user_answer ? '#dc2626' : '#64748b');
                  const pIcon = pCorr 
                    ? `<svg class="icon icon-xs" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>` 
                    : (p.user_answer 
                        ? `<svg class="icon icon-xs" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>` 
                        : `<svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><line x1="9" y1="12" x2="15" y2="12"></line></svg>`);
                  const pStatusLabel = pCorr ? "To'g'ri" : (p.user_answer ? "Xato" : "Yechilmagan");
                  return `
                    <div style="background:var(--card-bg); border:1px solid var(--border); border-radius:8px; padding:8px 12px; display:flex; flex-direction:column; gap:4px;">
                      <div style="display:flex; align-items:center; justify-content:space-between; font-size:11px; font-weight:700; color:var(--text);">
                        <span>${p.label.toUpperCase()}) band</span>
                        <span style="color:${pStatusColor}; font-size:11px; display:inline-flex; align-items:center; gap:4px;">
                          ${pIcon}
                          <span>${pStatusLabel}</span>
                        </span>
                      </div>
                      <div style="font-size:11px; color:var(--text-sub); display:flex; align-items:center; justify-content:space-between;">
                        <span>Yozilgan javob:</span>
                        <b style="color:${pStatusColor};">${pAns}</b>
                      </div>
                      <div style="font-size:11px; color:var(--text-sub); display:flex; align-items:center; justify-content:space-between;">
                        <span>To'g'ri kalit:</span>
                        <b style="color:var(--success);">${escapeHtml(p.correct_answer || '-')}</b>
                      </div>
                    </div>
                  `;
                }).join('')}
              </div>
            </div>
          `;
        } else {
          // Variantli savol (1-35)
          const isCorr = q.status === 'correct';
          const isWrong = q.status === 'wrong';
          const statusBg = isCorr ? 'rgba(16, 185, 129, 0.15)' : (isWrong ? 'rgba(239, 68, 68, 0.15)' : 'rgba(148, 163, 184, 0.15)');
          const statusColor = isCorr ? '#059669' : (isWrong ? '#dc2626' : '#64748b');
          const statusIcon = isCorr 
            ? `<svg class="icon icon-xs" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"></polyline></svg>` 
            : (isWrong 
                ? `<svg class="icon icon-xs" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>` 
                : `<svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"></circle><line x1="9" y1="12" x2="15" y2="12"></line></svg>`);
          const statusText = isCorr ? "To'g'ri" : (isWrong ? "Noto'g'ri" : "Yechilmagan");
          const userAnsText = q.user_answer ? escapeHtml(q.user_answer) : "Belgilanmagan";
          const userAnsClass = isCorr ? 'correct' : (q.user_answer ? 'wrong' : 'empty');

          return `
            <div class="question-analysis-card" id="analysisCard_${q.order_no}">
              <div style="display:flex; align-items:center; justify-content:space-between; gap:8px;">
                <div style="display:flex; align-items:center; gap:8px;">
                  <span class="q-order-badge">#${q.order_no}-savol</span>
                  <span style="font-size:11px; color:var(--text-sub); font-weight:500;">
                    ${q.order_no <= 32 ? 'Variantli test' : 'Kontekstli test'}
                  </span>
                </div>
                <span style="font-size:11px; font-weight:700; padding:2px 8px; border-radius:6px; background:${statusBg}; color:${statusColor}; border:1px solid ${statusColor}30; display:inline-flex; align-items:center; gap:4px;">
                  ${statusIcon}
                  <span>${statusText}</span>
                </span>
              </div>

              <div style="display:flex; align-items:center; justify-content:space-between; gap:10px; background:var(--card-bg); border:1px solid var(--border); border-radius:8px; padding:8px 12px; flex-wrap:wrap;">
                <div style="font-size:12px; display:flex; align-items:center; gap:8px;">
                  <span style="color:var(--text-sub);">Belgilangan javob:</span>
                  <span class="ans-pill ${userAnsClass}">${userAnsText}</span>
                </div>
                <div style="font-size:12px; display:flex; align-items:center; gap:8px;">
                  <span style="color:var(--text-sub);">To'g'ri kalit:</span>
                  <span class="ans-pill key">${escapeHtml(q.correct_answer || '-')}</span>
                </div>
              </div>
            </div>
          `;
        }
      }).join('');
    }

    async function openAttemptDetailsModal(attemptId) {
      if (!attemptId) return;
      try {
        showToast("Savollar tahlili yuklanmoqda...");
        const res = await fetch(`${API_BASE}/api/admin/attempts/${attemptId}/details`, {
          headers: getAdminAuthHeaders()
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Savollar tahlilini yuklab bo'lmadi");
        }
        const data = await res.json();
        currentAttemptDetails = data;
        currentAttemptFilter = 'all';

        // Modal sarlavhalari
        const titleElem = document.getElementById('attemptDetailsTitle');
        if (titleElem) titleElem.innerText = `${data.full_name || 'Talabgor'} — Natija tahlili`;

        const subElem = document.getElementById('attemptDetailsSubtitle');
        if (subElem) subElem.innerText = `${data.test_title || ''} (#${data.test_code || ''})`;

        // Hero Summary Card
        const heroElem = document.getElementById('attemptHeroCard');
        if (heroElem) {
          const initial = (data.full_name || 'T').trim().charAt(0).toUpperCase();
          const pct = Math.min(100, Math.max(0, Math.round((Number(data.final_score || 0) / 75) * 100)));
          const gradeClass = data.is_certified ? 'certified' : 'uncertified';
          const gradeText = data.is_certified 
            ? `<span style="display:inline-flex; align-items:center; gap:4px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="8" r="7"></circle><polyline points="8.21 13.89 7 23 12 20 17 23 15.79 13.88"></polyline></svg> <span>${escapeHtml(data.grade || 'Sertifikat')} (Sertifikat berildi)</span></span>` 
            : `<span style="display:inline-flex; align-items:center; gap:4px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg> <span>Sertifikat berilmadi</span></span>`;
          const barColor = data.is_certified ? 'linear-gradient(90deg, #10b981, #059669)' : 'linear-gradient(90deg, #ef4444, #f59e0b)';

          heroElem.innerHTML = `
            <div class="attempt-hero-top">
              <div class="attempt-user-meta">
                <div class="attempt-avatar">${initial}</div>
                <div>
                  <div class="attempt-user-name">${escapeHtml(data.full_name || 'Noma\'lum')}</div>
                  <div class="attempt-user-sub">
                    ${data.phone_number ? `<span style="display:inline-flex; align-items:center; gap:3px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>${escapeHtml(data.phone_number)}</span>` : ''}
                    ${data.username ? `<span style="display:inline-flex; align-items:center; gap:2px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"></circle><path d="M16 8v5a3 3 0 0 0 6 0v-1a10 10 0 1 0-3.92 7.94"></path></svg>${escapeHtml(data.username)}</span>` : ''}
                    <span style="display:inline-flex; align-items:center; gap:3px;"><svg class="icon icon-xs" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>${data.finished_at || 'Yakunlangan'}</span>
                  </div>
                </div>
              </div>

              <div class="attempt-score-badge">
                <div class="attempt-score-val">${data.final_score} <span style="font-size:12px; font-weight:600; color:var(--text-sub);">/ 75 ball</span></div>
                <span class="attempt-grade-pill ${gradeClass}">
                  ${gradeText}
                </span>
              </div>
            </div>

            <div style="display:flex; flex-direction:column; gap:4px; margin-top:4px;">
              <div style="display:flex; justify-content:space-between; font-size:11px; color:var(--text-sub);">
                <span>Natija ko'rsatkichi: <b>${pct}%</b></span>
                <span>Jami: <b>${data.raw_score || 0} ta to'g'ri</b></span>
              </div>
              <div class="attempt-progress-wrap">
                <div class="attempt-progress-bar" style="width:${pct}%; background:${barColor};"></div>
              </div>
            </div>
          `;
        }

        // Filtr hisoblagichlari
        const cAll = document.getElementById('cntFilterAll');
        if (cAll) cAll.innerText = data.total_items || 45;

        const cCorr = document.getElementById('cntFilterCorrect');
        if (cCorr) cCorr.innerText = data.correct_count || 0;

        const cWrong = document.getElementById('cntFilterWrong');
        if (cWrong) cWrong.innerText = data.wrong_count || 0;

        const cUnans = document.getElementById('cntFilterUnanswered');
        if (cUnans) cUnans.innerText = data.unanswered_count || 0;

        // Reset filter buttons state
        ['all', 'correct', 'wrong', 'unanswered'].forEach(f => {
          const btn = document.getElementById(`btnFilter${f.charAt(0).toUpperCase() + f.slice(1)}`);
          if (btn) btn.classList.toggle('active', f === 'all');
        });

        // 45-Savol Xaritasi (Quick Navigation Matrix)
        const matrixElem = document.getElementById('attemptMatrixGrid');
        if (matrixElem) {
          const breakdown = data.breakdown || [];
          matrixElem.innerHTML = breakdown.map(q => {
            let dotClass = 'unanswered';
            let dotTitle = `${q.order_no}-savol: Javob berilmagan`;
            if (q.status === 'correct') {
              dotClass = 'correct';
              dotTitle = `${q.order_no}-savol: To'g'ri`;
            } else if (q.status === 'wrong' || q.status === 'partially_correct') {
              dotClass = 'wrong';
              dotTitle = `${q.order_no}-savol: Xato`;
            }
            return `
              <div class="matrix-bubble ${dotClass}" title="${dotTitle}" onclick="jumpToQuestion(${q.order_no})">
                ${q.order_no}
              </div>
            `;
          }).join('');
        }

        // Savollar ro'yxatini render qilish
        renderAttemptAnswersList();

        const footerElem = document.getElementById('attemptFooterSummary');
        if (footerElem) footerElem.innerText = `Jami: ${data.total_items || 45} ta savol (${data.correct_count || 0} ta to'g'ri, ${data.wrong_count || 0} ta xato)`;

        openModal('attemptDetailsModal');
      } catch (err) {
        showToast("Xatolik: " + err.message, true);
      }
    }

    async function deleteAttempt(attemptId, studentName) {
      if (!attemptId) return;
      const targetName = studentName ? `"${studentName}"` : "ushbu talabgor";
      if (!confirm(`Haqiqatan ham ${targetName} natijasini o'chirib tashlamoqchimisiz?\n\nBu amal ortga qaytarilmaydi: talabgorning barcha javoblari va to'plagan bali to'liq o'chiriladi.`)) {
        return;
      }

      try {
        showToast("Natija o'chirilmoqda...");
        const res = await fetch(`${API_BASE}/api/admin/attempts/${attemptId}`, {
          method: 'DELETE',
          headers: getAdminAuthHeaders()
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || "Natijani o'chirib bo'lmadi");
        }
        showToast("Natija muvaffaqiyatli o'chirildi!");

        // Agar o'sha natija tahlil oynasida ochiq bo'lsa, uni yopamiz
        if (currentAttemptDetails && currentAttemptDetails.attempt_id === attemptId) {
          closeModal('attemptDetailsModal');
        }

        // Joriy test statistikasini qayta yuklaymiz
        if (currentTestStatsData && currentTestStatsData.test_id) {
          await openTestStatsModal(currentTestStatsData.test_id);
        }

        // Testlar ro'yxatidagi hisoblagichlarni ham yangilash
        loadMyTests();
      } catch (err) {
        showToast("Xatolik: " + err.message, true);
      }
    }

    async function deleteCurrentAttemptFromModal() {
      if (!currentAttemptDetails || !currentAttemptDetails.attempt_id) return;
      await deleteAttempt(currentAttemptDetails.attempt_id, currentAttemptDetails.full_name);
    }

    function buildStatsPostTextClient(data) {
      if (!data) return "";
      const totalPart = data.total_participants || 0;
      const completedCnt = data.completed_count || 0;
      const certCnt = data.certified_count || 0;
      const certPct = completedCnt > 0 ? Math.round((certCnt / completedCnt) * 100) : 0;

      let post = `📊 <b>TEST NATIJALARI VA STATISTIKASI</b>\n\n`;
      post += `🏷 <b>Test:</b> ${data.test_title || ''}\n`;
      post += `🔑 <b>Test kodi:</b> <code>#${data.test_code || ''}</code>\n`;
      post += `❓ <b>Savollar soni:</b> ${data.question_count || 45} ta | ⏱ <b>Vaqt:</b> ${data.time_limit_min || 150} daqiqa\n\n`;
      post += `━━━━━━━━━━━━━━━━━━━━\n`;
      post += `👥 <b>Qatnashuvchilar:</b> ${totalPart} ta\n`;
      post += `📈 <b>O'rtacha ball:</b> ${data.avg_score || 0} / 75 ball\n`;
      post += `🏆 <b>Eng yuqori ball:</b> ${data.highest_score || 0} ball\n`;
      post += `📜 <b>Sertifikat olganlar:</b> ${certCnt} ta (${certPct}%)\n`;
      post += `━━━━━━━━━━━━━━━━━━━━\n\n`;
      post += `🏆 <b>TALABGORLAR VA NATIJALAR:</b>\n\n`;

      const participants = data.participants || [];
      if (participants.length === 0) {
        post += `ℹ️ <i>Ushbu testni hali birorta ham talabgor topshirmagan.</i>\n`;
      } else {
        participants.forEach((p, idx) => {
          const rank = p.rank || (idx + 1);
          const name = p.full_name || "Noma'lum";
          const raw = p.raw_score || 0;
          const score = (p.final_score !== undefined && p.final_score !== null) ? Number(p.final_score).toFixed(1) : "0.0";
          const certBadge = p.is_certified ? `${p.grade || ''} (✅ Sertifikat berildi)`.trim() : `❌ Sertifikat berilmadi`;
          post += `<b>${rank}. ${name}</b> ------ 🎯 ${raw} ta to'g'ri, ⭐️ ${score} ball, ${certBadge}\n`;
        });
      }
      return post;
    }

    let editingTestId = null;

    async function openEditTest(testId) {
      try {
        showToast("Test ma'lumotlari yuklanmoqda...");
        const res = await fetch(`${API_BASE}/api/admin/test-details/${testId}`, {
          headers: getAdminAuthHeaders()
        });
        if (!res.ok) {
          const err = await res.json().catch(() => ({}));
          throw new Error(err.detail || `Yuklab bo'lmadi (${res.status})`);
        }
        const data = await res.json();
        const test = data.test;
        if (!test) throw new Error("Test topilmadi");

        editingTestId = test.id;

        // Formaga qiymatlarni to'ldirish
        const titleInput = document.getElementById('testTitle');
        if (titleInput) titleInput.value = test.title || '';

        const codeInput = document.getElementById('testCode');
        if (codeInput) {
          codeInput.value = test.code || '';
          codeInput.disabled = true;
        }

        const timeInput = document.getElementById('testTimeLimit');
        if (timeInput) timeInput.value = test.time_limit_min || 150;
        if (test.hide_answers !== undefined) {
          checkboxStates.hideAnswers = !!test.hide_answers;
          const cb = document.getElementById('cb_hideAnswers');
          if (cb) cb.classList.toggle('checked', checkboxStates.hideAnswers);
        }

        // 1-35 savollar
        if (test.questions && Array.isArray(test.questions)) {
          test.questions.forEach(q => {
            if (q.order_no >= 1 && q.order_no <= 35) {
              if (q.correct_answer) {
                answers1to35[q.order_no] = q.correct_answer;
                selectKeyOption(q.order_no, q.correct_answer);
              }
              if (q.text || q.image_url) {
                questionsMeta[q.order_no] = {
                  text: q.text || '',
                  image: q.image_url || '',
                  options: q.options || { A: '', B: '', C: '', D: '' }
                };
                const badge = document.getElementById(`badge_q_${q.order_no}`);
                if (badge) badge.style.display = (q.text || q.image_url) ? 'inline-block' : 'none';
              }
            } else if (q.order_no >= 36 && q.order_no <= 45) {
              // Ochiq savollar
              if (!openQuestionsData[q.order_no]) openQuestionsData[q.order_no] = {};
              if (q.sub_parts && Array.isArray(q.sub_parts) && q.sub_parts.length > 0) {
                openQuestionsData[q.order_no] = {};
                q.sub_parts.forEach(part => {
                  const answers = (part.alternative_answers && part.alternative_answers.length > 0)
                    ? part.alternative_answers
                    : [part.correct_answer || ''];
                  openQuestionsData[q.order_no][part.label] = answers;
                });
              }
              if (q.text || q.image_url) {
                openQuestionsMeta[q.order_no] = {
                  text: q.text || '',
                  image: q.image_url || ''
                };
              }
            }
          });
        }

        // Barcha savollarni yuklangan ma'lumotlar bilan qayta chizish
        initQuestions1to35();
        initOpenQuestions();

        // Banner va tugmalar matnini yangilash
        const banner = document.getElementById('editModeBanner');
        if (banner) banner.style.display = 'flex';

        const bannerText = document.getElementById('editModeText');
        if (bannerText) bannerText.innerText = `"${test.title}" (#${test.code}) javoblarini tahrirlash`;

        const publishBtn = document.getElementById('btnPublishTest');
        if (publishBtn) {
          publishBtn.innerHTML = `
            <svg class="icon" viewBox="0 0 24 24"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>
            O'ZGARISHLARNI SAQLASH
          `;
          publishBtn.style.background = 'var(--success)';
        }

        // Konstruktor oynasiga o'tish
        switchAdminTab('create');
        showToast("Test yuklandi. Kerakli javoblarni o'zgartirib, 'O'zgarishlarni saqlash' tugmasini bosing.");
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } catch (err) {
        showToast("Yuklashda xatolik: " + err.message, true);
      }
    }

    function cancelEditMode() {
      resetCreateForm(true);
      showToast("Yangi test yaratish rejimiga o'tildi");
    }

    async function toggleTestStatus(testId) {
      try {
        const res = await fetch(`${API_BASE}/api/admin/tests/${testId}/toggle`, {
          method: 'POST',
          headers: getAdminAuthHeaders()
        });
        const data = await res.json();
        if (res.ok && data.success) {
          showToast(data.message);
          loadMyTests();
        } else {
          showToast("Xatolik: " + (data.detail || "Holat o'zgarmadi"), true);
        }
      } catch (e) {
        showToast("Xatolik: " + e.message, true);
      }
    }

    function confirmDeleteTest(testId, code) {
      openConfirmModal(
        "Testni o'chirish",
        `Haqiqatan ham '${code}' testini butunlay o'chirib tashlamoqchimisiz?`,
        async () => {
          try {
            const res = await fetch(`${API_BASE}/api/admin/tests/${testId}`, {
              method: 'DELETE',
              headers: getAdminAuthHeaders()
            });
            const data = await res.json();
            if (res.ok && data.success) {
              showToast("Test o'chirildi!");
              loadMyTests();
            } else {
              showToast("Xatolik: " + (data.detail || "O'chirib bo'lmadi"), true);
            }
          } catch (e) {
            showToast("Xatolik: " + e.message, true);
          }
        }
      );
    }

    // ================= HELPERS: KATEX VA HTML =================
    function escapeHtml(str) {
      return (str || '')
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
    }

    function renderKatexString(str) {
      if (!str) return '';
      if (!window.katex) return escapeHtml(str);

      // Agar $...$ bo'lsa yoki KaTeX sintaksisi bo'lsa
      try {
        const tempDiv = document.createElement('div');
        tempDiv.textContent = str;
        if (window.renderMathInElement) {
          window.renderMathInElement(tempDiv, {
            delimiters: [
              { left: '$$', right: '$$', display: true },
              { left: '$', right: '$', display: false },
              { left: '\\(', right: '\\)', display: false },
              { left: '\\[', right: '\\]', display: true }
            ],
            throwOnError: false
          });
        }
        return tempDiv.innerHTML;
      } catch (e) {
        return escapeHtml(str);
      }
    }

    // ================= INITIALIZATION =================
    document.addEventListener('DOMContentLoaded', async () => {
      initSelect('selectTestType');
      initQuestions1to35();
      initOpenQuestions();
      renderKeyboard('greek');

      // Flatpickr Sanalar uchun
      if (window.flatpickr) {
        const fpStart = flatpickr("#startTime", {
          enableTime: true,
          dateFormat: "d.m.Y H:i",
          time_24hr: true,
          defaultDate: "07.09.2026 09:00",
          onChange: () => scheduleAutosave()
        });
        const fpEnd = flatpickr("#endTime", {
          enableTime: true,
          dateFormat: "d.m.Y H:i",
          time_24hr: true,
          defaultDate: "09.09.2026 23:59",
          onChange: () => scheduleAutosave()
        });

        document.getElementById('calIconStart')?.addEventListener('click', () => fpStart.open());
        document.getElementById('calIconEnd')?.addEventListener('click', () => fpEnd.open());
      }

      // Adminlik huquqini tekshirish
      const isAllowed = await verifyAdminAccess();
      if (!isAllowed) return;

      // Restore saved draft
      restoreDraft();

      // Super Admin bo'lsa tizim statistikasi tugmasini ko'rsatish
      checkAndShowSuperAdminUi();

      // Dastlabki testlar sonini bilish
      fetch(`${API_BASE}/api/admin/tests/${currentTelegramId || 0}`, {
        headers: getAdminAuthHeaders()
      })
        .then(r => r.json())
        .then(data => {
          if (data && Array.isArray(data.tests)) {
            document.getElementById('myTestsCount').innerText = data.tests.length;
          }
        })
        .catch(() => {});
    });

    async function verifyAdminAccess() {
      // 1. Agar Telegram initData mavjud bo'lmasa (brauzerda to'g'ridan-to'g'ri ochilsa)
      if (!telegramInitData) {
        document.body.innerHTML = `
          <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; padding:30px; text-align:center; font-family:Inter,sans-serif; background:var(--bg); color:var(--text);">
            <div style="width:60px; height:60px; border-radius:50%; background:var(--danger-light); display:flex; align-items:center; justify-content:center; margin-bottom:16px;">
              <svg class="icon" style="width:32px; height:32px; color:var(--danger);" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
            </div>
            <h2 style="font-size:20px; font-weight:700; margin-bottom:8px;">Kirish cheklangan</h2>
            <p style="color:var(--text-sub); font-size:14px; max-width:340px; line-height:1.6; margin-bottom:24px;">
              Bu sahifa faqat Telegram bot ichida ochiladi.
            </p>
          </div>
        `;
        return false;
      }

      // 2. Adminlik huquqini tekshirish
      const user = window.Telegram?.WebApp?.initDataUnsafe?.user;
      if (user && user.id) {
        try {
          const res = await fetch(`${API_BASE}/api/user/${user.id}`);
          if (res.ok) {
            const data = await res.json();
            if (!data.is_admin) {
              document.body.innerHTML = `
                <div style="display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:100vh; padding:30px 20px; text-align:center; font-family:Inter,sans-serif; background:var(--bg); color:var(--text);">
                  <div style="width:68px; height:68px; border-radius:50%; background:var(--danger-light, rgba(239, 68, 68, 0.1)); display:flex; align-items:center; justify-content:center; margin-bottom:18px;">
                    <svg class="icon" style="width:36px; height:36px; color:var(--danger, #ef4444); fill:none; stroke:currentColor;" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
                  </div>
                  <h2 style="font-size:22px; font-weight:700; margin-bottom:8px; color:var(--text);">Admin huquqi talab qilinadi</h2>
                  <p style="color:var(--text-sub); font-size:14px; max-width:400px; line-height:1.6; margin-bottom:20px;">
                    Kechirasiz, test javoblarini yaratish va boshqaruv paneli faqat tasdiqlangan administratorlar (ustozlar va repetitorlar) uchun ochiq.
                  </p>

                  <div style="background:var(--card-bg, rgba(0,0,0,0.03)); border:1px solid var(--border); border-radius:12px; padding:16px 20px; margin-bottom:24px; max-width:400px; text-align:left; box-shadow:0 2px 8px rgba(0,0,0,0.04);">
                    <div style="font-weight:700; font-size:14px; margin-bottom:6px; color:var(--text);">
                      👨‍🏫 Ustozlar va o'qituvchilar diqqatiga:
                    </div>
                    <p style="font-size:13px; color:var(--text-sub); margin:0; line-height:1.6;">
                      O'z o'quvchilaringiz uchun milliy sertifikat mock testlarini yaratish yoki administratorlik huquqini olish uchun bosh adminga murojaat qiling:
                      <br><a href="https://t.me/ITCenter_01" target="_blank" onclick="if(window.Telegram?.WebApp?.openTelegramLink){window.Telegram.WebApp.openTelegramLink('https://t.me/ITCenter_01');return false;}" style="color:var(--primary, #3b82f6); font-weight:700; text-decoration:none; font-size:14px; display:inline-flex; align-items:center; gap:4px; margin-top:6px;">
                        👉 @ITCenter_01
                      </a>
                    </p>
                  </div>

                  <div style="display:flex; gap:12px; flex-wrap:wrap; justify-content:center;">
                    <a href="https://t.me/ITCenter_01" target="_blank" onclick="if(window.Telegram?.WebApp?.openTelegramLink){window.Telegram.WebApp.openTelegramLink('https://t.me/ITCenter_01');return false;}" style="display:inline-flex; align-items:center; gap:8px; padding:11px 22px; background:#2AABEE; color:#fff; border-radius:10px; font-weight:600; text-decoration:none; font-size:14px; box-shadow:0 4px 12px rgba(42,171,238,0.28);">
                      <svg class="icon" style="width:18px; height:18px; stroke:currentColor; fill:none;" viewBox="0 0 24 24"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
                      Adminga murojaat qilish (@ITCenter_01)
                    </a>
                    <a href="/" style="display:inline-flex; align-items:center; gap:8px; padding:11px 22px; background:var(--primary); color:#fff; border-radius:10px; font-weight:600; text-decoration:none; font-size:14px;">
                      Bosh sahifaga qaytish
                    </a>
                  </div>
                </div>
              `;
              return false;
            }
            if (data.role === 'super_admin' || Number(user.id) === SUPER_ADMIN_ID) {
              const superBtn = document.getElementById('navSuperStatsBtn');
              if (superBtn) superBtn.style.display = 'inline-flex';
            }
          }
        } catch (e) {
          console.warn("Admin access check:", e);
        }
      }
      return true;
    }
