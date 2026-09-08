// Theme Management (Light / Dark) - Default: Light
    let currentTheme = localStorage.getItem('ms_theme_v2') || 'light';

    function applyTheme(theme) {
      currentTheme = theme;
      document.documentElement.setAttribute('data-theme', theme);
      localStorage.setItem('ms_theme_v2', theme);
      localStorage.setItem('theme', theme);

      const icon = document.getElementById('themeIcon');
      if (icon) {
        if (theme === 'light') {
          icon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
        } else {
          icon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
        }
      }
    }

    function toggleTheme() {
      applyTheme(currentTheme === 'light' ? 'dark' : 'light');
    }

    applyTheme(currentTheme);

    // Custom Toast function
    function showToast(msg, isError = false) {
      const container = document.getElementById('toastContainer');
      const toast = document.createElement('div');
      toast.className = 'toast' + (isError ? ' toast-error' : '');
      toast.innerHTML = `
        <svg class="icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
        <span>${msg}</span>
      `;
      container.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => toast.remove(), 300);
      }, 3500);
    }

    // Telegram WebApp Initialization
    const tg = window.Telegram?.WebApp;
    if (tg) {
      tg.ready();
      tg.expand();
      const saved = localStorage.getItem('ms_theme_v2');
      if (saved) {
        applyTheme(saved);
      }
    }

    // (API konfiguratsiyasi va apiFetch js/config.js faylidan yuklanadi) 


    let currentTest = null;
    let questions = [];
    let answers = {};
    let timerInterval = null;
    let sessionStartTime = null;
    let remainingSeconds = 150 * 60;
    const SESSION_KEY = 'msbot_active_test_session';

    let studentTelegramId = null;
    let studentUsername = '';
    let studentFullName = '';
    let studentPhone = '';

    // Telegram foydalanuvchisini xavfsiz aniqlash (initDataUnsafe yoki initData satridan)
    function getTelegramUser() {
      if (tg?.initDataUnsafe?.user) {
        return tg.initDataUnsafe.user;
      }
      if (tg?.initData) {
        try {
          const params = new URLSearchParams(tg.initData);
          const userStr = params.get('user');
          if (userStr) {
            return JSON.parse(userStr);
          }
        } catch (e) {}
      }
      return null;
    }

    // Telegramsiz tashqi brauzerda test qilinganda admin ID si bilan chalkashmasligi uchun
    function getGuestBrowserId() {
      let gid = localStorage.getItem('ms_guest_id');
      if (!gid || isNaN(parseInt(gid))) {
        gid = Math.floor(100000000 + Math.random() * 800000000);
        localStorage.setItem('ms_guest_id', gid);
      }
      return parseInt(gid);
    }

    // ================= TALABGOR PROFILI VA ISMINI ANIQLASH =================
    function isValidPersonName(n) {
      if (!n || typeof n !== 'string') return false;
      const lower = n.trim().toLowerCase();
      if (['talabgor', '.', '-', 'none', 'null', 'undefined'].includes(lower)) return false;
      const clean = n.replace(/[^a-zA-Zа-яА-ЯўқғҳЎҚҒҲ\s\']/g, '').trim();
      return clean.length >= 3;
    }

    async function fetchUserProfile() {
      const urlParams = new URLSearchParams(window.location.search);
      const qName = urlParams.get('name');
      const qPhone = urlParams.get('phone');
      const qTgId = urlParams.get('tg_id');
      const qUsername = urlParams.get('username');

      const tgUser = getTelegramUser();

      // 1. Telegram ID ni aniqlash (URL parametri > Telegram SDK > localStorage)
      if (qTgId && !isNaN(parseInt(qTgId))) {
        studentTelegramId = parseInt(qTgId);
        localStorage.setItem('ms_telegram_id', studentTelegramId);
      } else if (tgUser?.id) {
        studentTelegramId = tgUser.id;
        localStorage.setItem('ms_telegram_id', studentTelegramId);
      } else {
        const savedTgId = localStorage.getItem('ms_telegram_id');
        if (savedTgId && !isNaN(parseInt(savedTgId))) {
          studentTelegramId = parseInt(savedTgId);
        }
      }

      // 2. Username ni aniqlash
      if (qUsername) {
        studentUsername = qUsername.replace(/^@/, '');
        localStorage.setItem('ms_student_username', studentUsername);
      } else if (tgUser?.username) {
        studentUsername = tgUser.username;
        localStorage.setItem('ms_student_username', studentUsername);
      } else {
        studentUsername = localStorage.getItem('ms_student_username') || '';
      }

      // 3. Telefon raqamini aniqlash
      if (qPhone) {
        studentPhone = decodeURIComponent(qPhone).trim();
        localStorage.setItem('ms_student_phone', studentPhone);
      } else {
        studentPhone = localStorage.getItem('ms_student_phone') || '';
      }

      // 4. Ism-familiyani URL dan olish
      if (qName) {
        const decoded = decodeURIComponent(qName).trim();
        if (isValidPersonName(decoded)) {
          studentFullName = decoded;
          localStorage.setItem('ms_student_name', studentFullName);
        }
      }

      // 5. Agar studentTelegramId bo'lsa, backend bazasidan to'liq ma'lumotlarni tekshirish
      if (studentTelegramId) {
        try {
          const res = await apiFetch(`/api/user/${studentTelegramId}`);
          if (res.ok) {
            const data = await res.json();
            if (data.phone_number && !studentPhone) {
              studentPhone = data.phone_number;
              localStorage.setItem('ms_student_phone', studentPhone);
            }
            if (data.full_name && isValidPersonName(data.full_name) && !studentFullName) {
              studentFullName = data.full_name;
              localStorage.setItem('ms_student_name', studentFullName);
            }
            if (data.username && !studentUsername) {
              studentUsername = data.username;
              localStorage.setItem('ms_student_username', studentUsername);
            }
            if (data.is_admin) {
              const wrap = document.getElementById('adminPanelLinkWrap');
              if (wrap) wrap.style.display = 'flex';
              updateAdminLink();
            }
          }
        } catch (e) {
          console.warn("User fetch error:", e);
        }
      }

      // 6. Agar ism hali ham bo'sh bo'lsa, localStorage yoki Telegram SDK dan olish
      if (!studentFullName) {
        const savedName = localStorage.getItem('ms_student_name');
        if (savedName && isValidPersonName(savedName)) {
          studentFullName = savedName;
        } else if (tgUser) {
          const full = `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim();
          if (isValidPersonName(full)) {
            studentFullName = full;
            localStorage.setItem('ms_student_name', studentFullName);
          }
        }
      }

      updateUserDisplay();
    }

    function updateUserDisplay() {
      const el = document.getElementById('userDisplayName');
      if (!el) return;
      if (studentFullName && isValidPersonName(studentFullName)) {
        el.innerText = studentFullName;
      } else {
        el.innerHTML = '<span style="display:inline-flex; align-items:center; gap:4px; color:var(--primary); font-weight:600; text-decoration:underline; cursor:pointer;" onclick="editStudentName()"><span>Ism-familiyangizni kiriting</span><svg class="icon icon-xs" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg></span>';
      }
    }

    function editStudentName() {
      const inputEl = document.getElementById('nameModalInput');
      if (inputEl) inputEl.value = (studentFullName && isValidPersonName(studentFullName)) ? studentFullName : '';
      document.getElementById('nameModal').classList.add('open');
      setTimeout(() => { if (inputEl) inputEl.focus(); }, 120);
    }

    function closeNameModal() {
      document.getElementById('nameModal').classList.remove('open');
    }

    async function saveNameFromModal() {
      const inputEl = document.getElementById('nameModalInput');
      const clean = (inputEl?.value || '').trim();
      if (!isValidPersonName(clean)) {
        showToast("Iltimos, ism va familiyangizni to'liq kiriting (kamida 3 ta harf)!", true);
        return;
      }
      studentFullName = clean;
      localStorage.setItem('ms_student_name', studentFullName);
      updateUserDisplay();
      closeNameModal();
      showToast("Ismingiz muvaffaqiyatli saqlandi!");

      // Serverda ham foydalanuvchi profilini yangilash
      const tgId = (new URLSearchParams(window.location.search)).get('tg_id') || tg?.initDataUnsafe?.user?.id;
      if (tgId) {
        try {
          await apiFetch('/api/user/update-profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              telegram_id: parseInt(tgId),
              full_name: clean,
              phone_number: studentPhone || null
            })
          });
        } catch (e) {
          console.warn("Profilni serverda yangilashda ogohlantirish:", e);
        }
      }
    }

    // Session Management
    function saveActiveSession() {
      if (!currentTest || !sessionStartTime) return;
      try {
        const sessionData = {
          test: currentTest,
          startTime: sessionStartTime,
          timeLimitSeconds: (currentTest.time_limit_min || 150) * 60,
          answers: answers
        };
        localStorage.setItem(SESSION_KEY, JSON.stringify(sessionData));
      } catch (err) {
        console.warn("Sessiyani saqlashda xatolik:", err);
      }
    }

    function clearActiveSession() {
      try {
        localStorage.removeItem(SESSION_KEY);
      } catch (err) {}
    }

    function checkAndRestoreSession() {
      try {
        const saved = localStorage.getItem(SESSION_KEY);
        if (!saved) return false;

        const session = JSON.parse(saved);
        if (!session || !session.test || !session.startTime) {
          clearActiveSession();
          return false;
        }

        const totalSec = session.timeLimitSeconds || (session.test.time_limit_min || 150) * 60;
        const elapsed = Math.floor((Date.now() - session.startTime) / 1000);
        const rem = totalSec - elapsed;

        if (rem <= 0) {
          clearActiveSession();
          showToast("Avvalgi test vaqti tugagan!", true);
          return false;
        }

        currentTest = session.test;
        questions = currentTest.questions || [];
        sessionStartTime = session.startTime;
        remainingSeconds = rem;
        answers = session.answers || {};

        showScreen('screenQuiz');
        renderAnswerSheet();
        startTimer();
        showToast("Test varaqasi tiklandi! Qolgan vaqt: " + Math.floor(rem / 60) + " daqiqa.");
        return true;
      } catch (err) {
        clearActiveSession();
        return false;
      }
    }

    function renderMathInDocument() {
      if (window.renderMathInElement) {
        renderMathInElement(document.body, {
          delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false},
            {left: '\\(', right: '\\)', display: false},
            {left: '\\[', right: '\\]', display: true}
          ],
          throwOnError: false
        });
      }
    }

    // ================= TESTNI BOSHLASH (KOD ORQALI) =================
    async function startTestWithCode() {
      const codeInput = document.getElementById('testCodeInput');
      const code = (codeInput?.value || '').trim();

      if (!code) {
        showToast("Iltimos, test kodini kiriting!", true);
        if (codeInput) codeInput.focus();
        return;
      }

      showToast("Test yuklanmoqda...");
      try {
        const res = await apiFetch(`/api/test/${encodeURIComponent(code)}`);
        if (res.status === 404) {
          showToast(`Kechirasiz, '${code}' kodli test topilmadi! Kodni to'g'ri kiritganingizni tekshiring.`, true);
          return;
        }
        if (!res.ok) {
          showToast("Testni yuklab bo'lmadi. Server javob bermadi.", true);
          return;
        }

        const data = await res.json();
        currentTest = data;
        questions = currentTest.questions;

        if (!questions || questions.length === 0) {
          showToast("Ushbu testda hali savollar mavjud emas!", true);
          return;
        }

        sessionStartTime = Date.now();
        remainingSeconds = (currentTest.time_limit_min || 150) * 60;
        answers = {};

        saveActiveSession();
        startTimer();

        showScreen('screenQuiz');
        renderAnswerSheet();
      } catch (err) {
        showToast("Server bilan aloqa uzildi. Iltimos, qayta urinib ko'ring!", true);
      }
    }

    function showScreen(screenId) {
      document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
      const target = document.getElementById(screenId);
      if (target) target.classList.add('active');
      window.scrollTo(0, 0);

      // Taymer boshqaruvi
      const timerBadge = document.getElementById('timerBadge');
      if (timerBadge) {
        if (screenId === 'screenCode') {
          timerBadge.style.display = 'none';
        } else if (screenId === 'screenQuiz') {
          timerBadge.style.display = 'flex';
        } else {
          // Natija yoki boshqa ekranlarda taymer ko'rinmasin
          timerBadge.style.display = 'none';
        }
      }

      // Natija ekranlarida suzuvchi yakunlash tugmasini yashir
      const floatingBar = document.getElementById('floatingSubmitBar');
      if (floatingBar) {
        const isResultScreen = (screenId === 'screenResult' || screenId === 'screenHiddenResult' || screenId === 'screenCode');
        floatingBar.style.display = isResultScreen ? 'none' : 'flex';
      }
    }

    function startTimer() {
      const timerBadge = document.getElementById('timerBadge');
      if (timerBadge) timerBadge.style.display = 'flex';

      clearInterval(timerInterval);
      const updateTimerDisplay = () => {
        if (sessionStartTime && currentTest) {
          const totalSec = (currentTest.time_limit_min || 150) * 60;
          const elapsed = Math.floor((Date.now() - sessionStartTime) / 1000);
          remainingSeconds = totalSec - elapsed;
        } else {
          remainingSeconds--;
        }

        if (remainingSeconds <= 0) {
          clearInterval(timerInterval);
          showToast("Vaqtingiz tugadi! Test avtomatik yakunlanmoqda...", true);
          executeSubmitTest(true);
          return;
        }
        const m = Math.floor(remainingSeconds / 60);
        const s = remainingSeconds % 60;
        document.getElementById('timerText').innerText = 
          `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
      };

      updateTimerDisplay();
      timerInterval = setInterval(updateTimerDisplay, 1000);
    }

    // ================= JAVOBLAR VARAQASINI GENERATSIYA QILISH =================
    function renderAnswerSheet() {
      const part1List = document.getElementById('sheetListPart1');
      const part2List = document.getElementById('sheetListPart2');
      const part3List = document.getElementById('sheetListPart3');
      const groupCtxWrap = document.getElementById('sheetGroupContextWrap');

      part1List.innerHTML = '';
      part2List.innerHTML = '';
      part3List.innerHTML = '';

      let groupContextHtml = '';

      questions.forEach((q) => {
        const qId = q.id;
        const orderNo = q.order_no;

        // I Bo'lim: 1–32 (4 ta variant A, B, C, D)
        if (orderNo <= 32) {
          const row = document.createElement('div');
          const hasAns = !!answers[qId]?.choice;
          row.className = 'sheet-row' + (hasAns ? ' has-answer' : '');
          row.id = `sheetRow_${qId}`;

          const opts = ['A', 'B', 'C', 'D'];
          let bubblesHtml = '';
          opts.forEach(opt => {
            const isSel = (answers[qId]?.choice === opt);
            bubblesHtml += `
              <div class="bubble-btn${isSel ? ' selected' : ''}" 
                   onclick="selectBubble(${qId}, '${opt}', this)">
                ${opt}
              </div>
            `;
          });

          row.innerHTML = `
            <div class="sheet-q-title">
              <span>${orderNo}-savol</span>
            </div>
            <div class="sheet-bubbles-group">
              ${bubblesHtml}
            </div>
          `;
          part1List.appendChild(row);
        }
        // II Bo'lim: 33–35 (6 ta variant A, B, C, D, E, F)
        else if (orderNo >= 33 && orderNo <= 35) {
          if (q.group_context && !groupContextHtml) {
            groupContextHtml = `
              <div style="font-weight:700; color:var(--primary); font-size:13px; margin-bottom:6px; display:flex; align-items:center; gap:6px;">
                <svg class="icon icon-sm" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line></svg>
                <span>33–35 testlar uchun umumiy shart:</span>
              </div>
              <div style="color:var(--text-main);">${q.group_context}</div>
              ${q.group_image_url ? `
                <div style="text-align:center; margin-top:8px;">
                  <img src="${(q.group_image_url.startsWith('http') || !API_BASE) ? q.group_image_url : (API_BASE + (q.group_image_url.startsWith('/') ? '' : '/') + q.group_image_url)}" alt="Umumiy chizma" style="max-width:100%; max-height:200px; border-radius:6px;">
                </div>
              ` : ''}
            `;
          }

          const row = document.createElement('div');
          const hasAns = !!answers[qId]?.choice;
          row.className = 'sheet-row' + (hasAns ? ' has-answer' : '');
          row.id = `sheetRow_${qId}`;

          const opts = ['A', 'B', 'C', 'D', 'E', 'F'];
          let bubblesHtml = '';
          opts.forEach(opt => {
            const isSel = (answers[qId]?.choice === opt);
            bubblesHtml += `
              <div class="bubble-btn${isSel ? ' selected' : ''}" 
                   onclick="selectBubble(${qId}, '${opt}', this)">
                ${opt}
              </div>
            `;
          });

          row.innerHTML = `
            <div class="sheet-q-title">
              <span>${orderNo}-savol</span>
            </div>
            <div class="sheet-bubbles-group six-opts">
              ${bubblesHtml}
            </div>
          `;
          part2List.appendChild(row);
        }
        // III Bo'lim: 36–45 (Ochiq savollar: a va b bandlari)
        else {
          const row = document.createElement('div');
          const ansA = answers[qId]?.a || '';
          const ansB = answers[qId]?.b || '';
          const hasAns = (ansA !== '' || ansB !== '');
          row.className = 'open-sheet-row' + (hasAns ? ' has-answer' : '');
          row.id = `sheetRow_${qId}`;

          row.innerHTML = `
            <div class="sheet-q-title">
              <span>${orderNo}-savol (yozma)</span>
            </div>
            <div class="open-inputs-pair">
              <div class="open-sub-field-wrap${ansA ? ' filled' : ''}" id="wrapSubA_${qId}">
                <span class="open-sub-label">a)</span>
                <input type="text" class="open-sub-input" placeholder="javob" value="${ansA}"
                       oninput="saveOpenSubPart(${qId}, 'a', this.value, this)">
              </div>
              <div class="open-sub-field-wrap${ansB ? ' filled' : ''}" id="wrapSubB_${qId}">
                <span class="open-sub-label">b)</span>
                <input type="text" class="open-sub-input" placeholder="javob" value="${ansB}"
                       oninput="saveOpenSubPart(${qId}, 'b', this.value, this)">
              </div>
            </div>
          `;
          part3List.appendChild(row);
        }
      });

      if (groupContextHtml) {
        groupCtxWrap.innerHTML = groupContextHtml;
        groupCtxWrap.style.display = 'block';
      } else {
        groupCtxWrap.style.display = 'none';
      }

      updateAnsweredCounter();
      setTimeout(renderMathInDocument, 40);
    }

    function selectBubble(qId, key, el) {
      if (!answers[qId]) answers[qId] = {};
      answers[qId].choice = key;

      const parent = el.parentElement;
      parent.querySelectorAll('.bubble-btn').forEach(b => b.classList.remove('selected'));
      el.classList.add('selected');

      const row = document.getElementById(`sheetRow_${qId}`);
      if (row) row.classList.add('has-answer');

      saveActiveSession();
      updateAnsweredCounter();
    }

    function saveOpenSubPart(qId, part, val, inputEl) {
      if (!answers[qId]) answers[qId] = {};
      answers[qId][part] = val.trim();

      const wrap = document.getElementById(`wrapSub${part.toUpperCase()}_${qId}`);
      if (wrap) {
        if (val.trim()) {
          wrap.classList.add('filled');
        } else {
          wrap.classList.remove('filled');
        }
      }

      const row = document.getElementById(`sheetRow_${qId}`);
      if (row) {
        if (answers[qId].a || answers[qId].b) {
          row.classList.add('has-answer');
        } else {
          row.classList.remove('has-answer');
        }
      }

      saveActiveSession();
      updateAnsweredCounter();
    }

    function updateAnsweredCounter() {
      let count = 0;
      questions.forEach(q => {
        const ans = answers[q.id];
        if (!ans) return;
        if (ans.choice) {
          count++;
        } else if (ans.a || ans.b) {
          count++;
        }
      });

      const total = questions.length || 45;
      const text = `${count} / ${total}`;
      const headerText = document.getElementById('sheetAnsweredCountText');
      const floatText = document.getElementById('floatingCounter');
      if (headerText) headerText.innerText = text;
      if (floatText) floatText.innerText = `${count} / ${total} ta`;
    }

    // ================= SAVOLNI KO'RISH MODALI (PEEK MODAL) =================
    function peekQuestion(orderNo) {
      const q = questions.find(item => item.order_no === orderNo);
      if (!q) return;

      document.getElementById('peekModalTitle').innerHTML = `
        <svg class="icon icon-sm" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>
        <span>Savol #${orderNo} (${q.section || 'Matematika'})</span>
      `;

      const ctxEl = document.getElementById('peekGroupContext');
      if (q.group_context) {
        ctxEl.innerHTML = `<b>33–35 umumiy shart:</b><br>${q.group_context}`;
        ctxEl.style.display = 'block';
      } else {
        ctxEl.style.display = 'none';
      }

      document.getElementById('peekQuestionText').innerHTML = q.text || '(Savol matni mavjud emas)';

      const imgWrap = document.getElementById('peekImageWrap');
      const imgEl = document.getElementById('peekImage');
      const targetImg = q.image_url || (q.group_context ? q.group_image_url : null);

      if (targetImg) {
        imgEl.src = (targetImg.startsWith('http') || !API_BASE) ? targetImg : (API_BASE + (targetImg.startsWith('/') ? '' : '/') + targetImg);
        imgWrap.style.display = 'block';
      } else {
        imgWrap.style.display = 'none';
      }

      document.getElementById('peekModal').classList.add('open');
      setTimeout(renderMathInDocument, 30);
    }

    function closePeekModal() {
      document.getElementById('peekModal').classList.remove('open');
    }

    // ================= TEZKOR TO'LDIRISH (QUICK PASTE) =================
    function openQuickPasteModal() {
      document.getElementById('quickPasteInput').value = '';
      document.getElementById('quickPasteModal').classList.add('open');
    }

    function closeQuickPasteModal() {
      document.getElementById('quickPasteModal').classList.remove('open');
    }

    function applyQuickPaste() {
      const raw = document.getElementById('quickPasteInput').value.toUpperCase().replace(/[^A-F]/g, '');
      if (!raw) {
        showToast("Hech qanday harf kiritilmadi!", true);
        return;
      }

      const keys = raw.split('');
      let filled = 0;

      questions.forEach((q, idx) => {
        if (q.order_no <= 35 && idx < keys.length) {
          const letter = keys[idx];
          if (q.order_no <= 32 && ['A', 'B', 'C', 'D'].includes(letter)) {
            if (!answers[q.id]) answers[q.id] = {};
            answers[q.id].choice = letter;
            filled++;
          } else if (q.order_no >= 33 && q.order_no <= 35 && ['A', 'B', 'C', 'D', 'E', 'F'].includes(letter)) {
            if (!answers[q.id]) answers[q.id] = {};
            answers[q.id].choice = letter;
            filled++;
          }
        }
      });

      closeQuickPasteModal();
      saveActiveSession();
      renderAnswerSheet();
      showToast(`${filled} ta test kaliti tezkor to'ldirildi!`);
    }

    // ================= YAKUNLASH TASDIQLASH VA SUBMIT =================
    let isSubmittingTest = false;
    let testAlreadySubmitted = false; // muvaffaqiyatli submit bo'lsa qaytmas flag

    function openFinishModal() {
      // Test allaqachon yakunlangan bo'lsa modal chiqmasin
      if (isSubmittingTest || testAlreadySubmitted) return;

      let count = 0;
      questions.forEach(q => {
        const ans = answers[q.id];
        if (ans && (ans.choice || ans.a || ans.b)) count++;
      });
      const emptyCount = questions.length - count;

      const descEl = document.getElementById('finishModalText');
      if (emptyCount > 0) {
        descEl.innerText = `Siz ${count} ta savolni to'ldirdingiz. ${emptyCount} ta savol belgilanmadi (ular xato deb baholanadi). Testni yakunlab, natijani chiqaramizmi?`;
      } else {
        descEl.innerText = `Barcha 45 ta savol to'liq to'ldirildi! Testni yakunlaysizmi?`;
      }

      document.getElementById('finishModal').classList.add('open');
    }

    function closeFinishModal() {
      // Faqat yuborilayotgan vaqtda (loading) modalni yopishni block qilamiz
      // testAlreadySubmitted holatida isSubmittingTest false bo'lgani uchun yopish ishlaydi
      if (isSubmittingTest) return;
      document.getElementById('finishModal').classList.remove('open');
    }

    async function executeSubmitTest(isTimeout = false) {
      if (isSubmittingTest) return;
      isSubmittingTest = true;

      // Asosiy yakunlash tugmasini disable qilamiz (qayta bosilmasin)
      const submitBtn = document.getElementById('btnMainSubmit');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = `
          <div style="display:flex; align-items:center; justify-content:center; gap:8px;">
            <div style="width:16px; height:16px; border:2px solid #fff; border-top:2px solid transparent; border-radius:50%; animation:spin 0.6s linear infinite;"></div>
            <span>Yakunlanmoqda...</span>
          </div>
        `;
      }

      // Modalni DARHOL to'g'ridan-to'g'ri yopamiz (closeFinishModal() ni ishlatmaymiz
      // chunki u isSubmittingTest=true bo'lganda ishlashdan bosh tortadi)
      document.getElementById('finishModal').classList.remove('open');
      // Floating bar ni ham darhol yashiramiz
      const floatingBarEl = document.getElementById('floatingSubmitBar');
      if (floatingBarEl) floatingBarEl.style.display = 'none';

      const overlay = document.getElementById('submitLoadingOverlay');
      if (overlay) {
        const titleEl = overlay.querySelector('.submit-loading-title');
        const descEl = overlay.querySelector('.submit-loading-desc');
        if (isTimeout) {
          if (titleEl) titleEl.innerText = "Vaqtingiz tugadi!";
          if (descEl) descEl.innerText = "Ajratilgan vaqt yakunlandi. Barcha belgilangan javoblaringiz avtomatik qabul qilinmoqda...";
        } else {
          if (titleEl) titleEl.innerText = "Natijangiz hisoblanmoqda...";
          if (descEl) descEl.innerText = "RASH (IRT) modeli asosida javoblaringiz baholanmoqda va rasmiy sertifikat blankasi shakllantirilmoqda. Iltimos, bir oz kuting.";
        }
        overlay.style.display = 'flex';
      }

      clearInterval(timerInterval);
      clearActiveSession();

      // Haqiqiy foydalanuvchini aniqlash (hech qachon admin ID si bilan aralashmasligi kerak)
      const tgUser = getTelegramUser();
      const urlParams = new URLSearchParams(window.location.search);
      const qTgId = urlParams.get('tg_id');

      let finalTelegramId = null;
      if (studentTelegramId) {
        finalTelegramId = studentTelegramId;
      } else if (qTgId && !isNaN(parseInt(qTgId))) {
        finalTelegramId = parseInt(qTgId);
      } else if (tgUser?.id) {
        finalTelegramId = tgUser.id;
      } else {
        const savedTgId = localStorage.getItem('ms_telegram_id');
        if (savedTgId && !isNaN(parseInt(savedTgId))) {
          finalTelegramId = parseInt(savedTgId);
        } else {
          finalTelegramId = getGuestBrowserId();
        }
      }

      const finalUsername = studentUsername || urlParams.get('username') || tgUser?.username || localStorage.getItem('ms_student_username') || null;
      const finalFullName = studentFullName || 
        urlParams.get('name') || 
        (tgUser ? `${tgUser.first_name || ''} ${tgUser.last_name || ''}`.trim() : '') || 
        localStorage.getItem('ms_student_name') || 
        'Talabgor';

      const payloadAnswers = [];
      for (const [qId, ansObj] of Object.entries(answers)) {
        if (ansObj.choice) {
          payloadAnswers.push({
            question_id: parseInt(qId),
            user_answer: ansObj.choice,
            sub_part_label: null
          });
        }
        if (ansObj.a) {
          payloadAnswers.push({
            question_id: parseInt(qId),
            user_answer: ansObj.a,
            sub_part_label: 'a'
          });
        }
        if (ansObj.b) {
          payloadAnswers.push({
            question_id: parseInt(qId),
            user_answer: ansObj.b,
            sub_part_label: 'b'
          });
        }
      }

      try {
        const res = await apiFetch('/api/test/submit', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            test_id: currentTest.id,
            telegram_id: finalTelegramId,
            full_name: finalFullName,
            username: finalUsername,
            answers: payloadAnswers
          })
        });

        if (!res.ok) {
          throw new Error(`Server xatosi: ${res.status}`);
        }

        const result = await res.json();
        // Muvaffaqiyatli submit — qaytmas flag o'rnatiladi
        testAlreadySubmitted = true;
        isSubmittingTest = false; // loading holat tugadi
        if (overlay) overlay.style.display = 'none';
        // Submit tugmasini butunlay o'chirib qo'yamiz
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.innerText = "Yakunlandi";
        }
        // Modalni yopamiz (endi closeFinishModal isSubmittingTest=false bo'lgani uchun ishlaydi)
        document.getElementById('finishModal').classList.remove('open');
        // Natija ekraniga o'tish
        if (result.hide_answers) {
          showHiddenResultScreen(result.message);
        } else {
          showToast("Test yakunlandi! Natijangiz hisoblandi.");
          displayResult(result);
        }
      } catch (err) {
        // Xatolik bo'lsa foydalanuvchi qayta urinib ko'rishi mumkin
        showToast("Natijani tekshirishda xatolik: " + err.message, true);
        isSubmittingTest = false;
        if (overlay) overlay.style.display = 'none';
        if (submitBtn) {
          submitBtn.disabled = false;
          submitBtn.innerText = "Ha, tugatish";
        }
      }
    }

    function showHiddenResultScreen(customMsg) {
      clearInterval(timerInterval);
      clearActiveSession();

      const timerBadge = document.getElementById('timerBadge');
      if (timerBadge) timerBadge.style.display = 'none';

      const bar = document.getElementById('floatingSubmitBar');
      if (bar) bar.style.display = 'none';

      if (customMsg) {
        const msgEl = document.getElementById('hiddenResultMsg');
        if (msgEl) msgEl.innerHTML = `Sizning barcha javoblaringiz qabul qilindi. <b>${customMsg}</b>`;
      }

      showScreen('screenHiddenResult');
    }

    function closeTelegramAppOrRestart() {
      if (window.Telegram?.WebApp?.close) {
        try {
          window.Telegram.WebApp.close();
          return;
        } catch (e) {}
      }
      window.location.reload();
    }

    // ================= NATIJA VA DIAGNOSTIKANI CHIQARISH =================
    function displayResult(res) {
      showScreen('screenResult');
      const gradeEl = document.getElementById('resGrade');
      gradeEl.innerText = res.grade;
      if (res.is_certified) {
        gradeEl.classList.remove('grade-badge-failed');
        gradeEl.classList.add('grade-badge-certified');
      } else {
        gradeEl.classList.remove('grade-badge-certified');
        gradeEl.classList.add('grade-badge-failed');
      }

      document.getElementById('resFinalScore').innerText = `${res.final_score.toFixed(1)} / 75`;
      document.getElementById('resRawScore').innerText = `${res.raw_score} / ${res.total_items}`;
      document.getElementById('resTheta').innerText = `${res.theta >= 0 ? '+' : ''}${res.theta.toFixed(2)} logit`;
      
      const statusEl = document.getElementById('resCertStatus');
      if (res.is_certified) {
        statusEl.innerText = "Tabriklaymiz, Sertifikat berildi!";
        statusEl.style.color = "var(--success)";
      } else {
        statusEl.innerText = "Sertifikat berilmadi (Minimal 46 ball)";
        statusEl.style.color = "var(--danger)";
      }

      // Rasmiy Sertifikat Blankasini ko'rsatish — FAQAT sertifikat olgan bo'lsagina
      const certBox = document.getElementById('certContainer');
      const certImg = document.getElementById('resCertImg');
      const certBadgeText = document.getElementById('certBadgeText');
      const certSpinner = document.getElementById('certImgSpinner');

      // Sertifikat olmagan bo'lsa — cert blokini umuman ko'rsatma
      if (res.is_certified && res.certificate_url) {
        let fullCertUrl = res.certificate_url;
        if (!fullCertUrl.startsWith('http://') && !fullCertUrl.startsWith('https://')) {
          const cleanApi = (API_BASE || '').replace(/\/+$/, '');
          const cleanPath = fullCertUrl.replace(/^\/+/, '');
          fullCertUrl = cleanApi ? `${cleanApi}/${cleanPath}` : `/${cleanPath}`;
        }
        window.currentCertFullUrl = fullCertUrl;

        if (certBox) certBox.style.display = 'block';
        if (certSpinner) certSpinner.style.display = 'flex';
        if (certImg) {
          certImg.style.display = 'none';
          certImg.src = fullCertUrl;
        }
        if (certBadgeText) {
          certBadgeText.innerText = "Sertifikat tayyor";
          certBadgeText.style.background = "rgba(16, 185, 129, 0.15)";
          certBadgeText.style.color = "var(--success)";
        }
      } else {
        // Sertifikat yo'q — blokni yashir
        if (certBox) certBox.style.display = 'none';
      }

      const grid = document.getElementById('diagGridContainer');
      grid.innerHTML = '';

      if (res.details && res.details.length > 0) {
        const qMap = {};
        res.details.forEach(item => {
          if (!qMap[item.order_no]) qMap[item.order_no] = [];
          qMap[item.order_no].push(item);
        });

        questions.forEach(q => {
          const items = qMap[q.order_no] || [];
          const cell = document.createElement('div');
          
          if (items.length === 0) {
            cell.className = 'diag-item incorrect';
            cell.innerHTML = `
              <span class="diag-num">#${q.order_no}</span>
              <span class="diag-ans" style="color:var(--danger);">-</span>
            `;
          } else if (items.length === 1) {
            const it = items[0];
            const isCor = it.is_correct;
            cell.className = 'diag-item ' + (isCor ? 'correct' : 'incorrect');
            cell.innerHTML = `
              <span class="diag-num">#${q.order_no}</span>
              <span class="diag-ans" style="color:${isCor ? 'var(--success)' : 'var(--danger)'};">${it.user_answer || '-'}</span>
            `;
          } else {
            const allCor = items.every(i => i.is_correct);
            const anyCor = items.some(i => i.is_correct);
            cell.className = 'diag-item ' + (allCor ? 'correct' : (anyCor ? 'correct' : 'incorrect'));
            const aItem = items.find(i => i.sub_part_label === 'a');
            const bItem = items.find(i => i.sub_part_label === 'b');
            cell.innerHTML = `
              <span class="diag-num">#${q.order_no}</span>
              <span style="font-size:10px; font-weight:700;">
                a:<b style="color:${aItem?.is_correct ? 'var(--success)' : 'var(--danger)'};">${aItem?.is_correct ? '✓' : '✗'}</b> 
                b:<b style="color:${bItem?.is_correct ? 'var(--success)' : 'var(--danger)'};">${bItem?.is_correct ? '✓' : '✗'}</b>
              </span>
            `;
          }
          grid.appendChild(cell);
        });
      } else {
        questions.forEach(q => {
          const cell = document.createElement('div');
          cell.className = 'diag-item';
          cell.innerHTML = `<span class="diag-num">#${q.order_no}</span>`;
          grid.appendChild(cell);
        });
      }
    }

    function openCertFullscreen() {
      const url = window.currentCertFullUrl || (document.getElementById('resCertImg')?.src);
      if (url) {
        window.open(url, '_blank');
      }
    }

    async function triggerDownloadCert() {
      const url = window.currentCertFullUrl || (document.getElementById('resCertImg')?.src);
      if (!url) {
        showToast("Sertifikat manzili topilmadi", true);
        return;
      }

      try {
        showToast("Sertifikat yuklab olinmoqda...");
        const resp = await fetch(url);
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const blob = await resp.blob();
        const blobUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = blobUrl;
        a.download = `sertifikat_${Date.now()}.jpg`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(blobUrl);
        showToast("Sertifikat muvaffaqiyatli saqlandi!");
      } catch (err) {
        window.open(url, '_blank');
      }
    }

    function restartApp() {
      clearActiveSession();
      answers = {};
      currentTest = null;
      const codeInput = document.getElementById('testCodeInput');
      if (codeInput) codeInput.value = '';
      showScreen('screenCode');
    }

    function getAdminPanelUrl() {
      // 1. Fayl protokoli orqali ochilgan bo'lsa
      if (window.location.protocol === 'file:') {
        return new URL('admin.html', window.location.href).href;
      }
      
      const currentUrl = new URL(window.location.href);
      let targetPath;
      
      // 2. Agar yo'l ichida /web/ bo'lsa (masalan GitHub Pages: /ms-bot/web/index.html)
      if (currentUrl.pathname.includes('/web/')) {
        const base = currentUrl.pathname.substring(0, currentUrl.pathname.lastIndexOf('/web/'));
        targetPath = base + '/web/admin.html';
      } else if (currentUrl.hostname.includes('github.io')) {
        // GitHub Pages repository root bo'lsa (/ms-bot/ yoki /ms-bot/index.html)
        const repo = currentUrl.pathname.replace(/\/index\.html$/, '').replace(/\/$/, '');
        targetPath = (repo ? repo : '') + '/web/admin.html';
      } else {
        // FastAPI / localhost server
        targetPath = '/admin';
      }
      
      const dest = new URL(targetPath, window.location.origin);
      // Barcha URL parametrlari (tg_id, api va hk) ni o'tkazish
      dest.search = window.location.search;
      dest.hash = window.location.hash;
      return dest.toString();
    }

    function navigateToAdminPanel(e) {
      if (e) {
        e.preventDefault();
        e.stopPropagation();
      }
      window.location.href = getAdminPanelUrl();
    }
    window.navigateToAdminPanel = navigateToAdminPanel;

    function updateAdminLink() {
      const link = document.getElementById('btnAdminPanelLink');
      if (!link) return;
      link.href = getAdminPanelUrl();
    }

    // ================= DASTUR ISHGA TUSHGANDA VA F5 BOSILGANDA TIKLASH =================
    window.addEventListener('DOMContentLoaded', () => {
      fetchUserProfile();
      updateAdminLink();
      checkAndRestoreSession();
    });

    window.addEventListener('beforeunload', () => {
      if (currentTest && document.getElementById('screenQuiz').classList.contains('active')) {
        saveActiveSession();
      }
    });

    fetchUserProfile();
    updateAdminLink();
    checkAndRestoreSession();
