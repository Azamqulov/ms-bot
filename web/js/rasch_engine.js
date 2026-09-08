/**
 * Milliy Sertifikat — Matematika: Rasch Modeli (1PL IRT) Baholash Dvigateli (Frontend JS)
 * ====================================================================================
 * Ushbu modul O'zbekiston Milliy sertifikat imtihoni (Matematika) formati uchun
 * 45 ta topshiriq asosida Rasch o'lchov modelini (1-Parameter Logistic IRT) amalga oshiradi.
 *
 * DIQQAT:
 * Ushbu tizim Milliy sertifikatga o'xshash simulyatsion baholash vositasi bo'lib,
 * BBA (Bilim va malakalarni baholash agentligi) rasmiy baholash tizimi yoki
 * rasmiy parametrlari hisoblanmaydi.
 *
 * Modul funksiyalari:
 * - calculateProbability(theta, b)
 * - estimateItemDifficulty(orderNo, questionType, autoDifficulty, manualDifficulty, customMap)
 * - calculateRaschAbility(answersData, options)
 * - convertRaschToScore(theta, calibrationParams)
 * - getCertificateLevel(finalScore)
 */

(function (root, factory) {
  if (typeof define === 'function' && define.amd) {
    define([], factory);
  } else if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.RaschEngine = factory();
  }
}(typeof self !== 'undefined' ? self : this, function () {

  // Standart qiyinlik parametrlari (b_i logit)
  const DEFAULT_DIFFICULTY_MAP = {
    easy: -1.0,
    medium: 0.0,
    hard: 1.0
  };

  // Standart kalibrlash parametrlari (logit -> 0-75 ball shkalasi)
  const DEFAULT_CALIBRATION_PARAMS = {
    baseScore: 50.0,    // theta = 0 bo'lgandagi ball (C+ chegarasi)
    scaleFactor: 8.8,   // 1 logit uchun ball ko'paytuvchisi
    minScore: 0.0,
    maxScore: 75.0
  };

  /**
   * 1. Rasch logistik ehtimolligi:
   * P(X_ni = 1 | theta_n, b_i) = exp(theta_n - b_i) / (1 + exp(theta_n - b_i))
   *
   * @param {number} theta - Talabgorning qobiliyat parametri (ability)
   * @param {number} b - Savolning qiyinlik parametri (difficulty)
   * @returns {number} To'g'ri javob berish ehtimoli (0.0 dan 1.0 gacha)
   */
  function calculateProbability(theta, b) {
    const diff = theta - b;
    // Overflow va underflow himoyasi
    if (diff > 35.0) return 1.0;
    if (diff < -35.0) return 0.0;

    const expVal = Math.exp(diff);
    return expVal / (1.0 + expVal);
  }

  /**
   * 2. Savolning qiyinlik parametrini aniqlash (Auto difficulty yoki Manual)
   *
   * @param {number} orderNo - Savol tartib raqami (1-45)
   * @param {string} questionType - Savol turi ('Y', 'GROUPED', 'O' yoki '')
   * @param {boolean} autoDifficulty - Auto difficulty ON (true) yoki OFF (false)
   * @param {string|number} manualDifficulty - Admin tomonidan berilgan 'easy'|'medium'|'hard' yoki float b_i
   * @param {Object} customMap - Ixtiyoriy maxsus qiyinlik lug'ati
   * @returns {{ difficulty: string|number, numericalB: number, autoAssigned: boolean }}
   */
  function estimateItemDifficulty(orderNo, questionType, autoDifficulty, manualDifficulty, customMap) {
    const diffMap = Object.assign({}, DEFAULT_DIFFICULTY_MAP, customMap || {});

    // Agar Auto difficulty OFF bo'lsa va qo'lda qiymat kiritilgan bo'lsa:
    if (!autoDifficulty && manualDifficulty !== undefined && manualDifficulty !== null && manualDifficulty !== '') {
      if (typeof manualDifficulty === 'number' && !isNaN(manualDifficulty)) {
        return {
          difficulty: manualDifficulty,
          numericalB: manualDifficulty,
          autoAssigned: false
        };
      }

      const diffStr = String(manualDifficulty).trim().toLowerCase();
      if (diffMap.hasOwnProperty(diffStr)) {
        return {
          difficulty: diffStr,
          numericalB: diffMap[diffStr],
          autoAssigned: false
        };
      }

      const parsedNum = parseFloat(diffStr);
      if (!isNaN(parsedNum)) {
        return {
          difficulty: parsedNum,
          numericalB: parsedNum,
          autoAssigned: false
        };
      }

      return {
        difficulty: 'medium',
        numericalB: diffMap.medium,
        autoAssigned: false
      };
    }

    // Auto difficulty ON: Milliy sertifikat matematika strukturasiga binoan
    const qType = String(questionType || '').toUpperCase();
    const isOpen = qType.startsWith('O') || orderNo >= 36;

    let label = 'medium';
    if (isOpen || orderNo >= 36) {
      label = 'hard';
    } else if (orderNo <= 15) {
      label = 'easy';
    } else {
      label = 'medium';
    }

    return {
      difficulty: label,
      numericalB: diffMap[label] !== undefined ? diffMap[label] : 0.0,
      autoAssigned: true
    };
  }

  /**
   * 3. Rasch logit natijasini 0-75 (yoki 0-70+) ball shkalasiga kalibrlash
   *
   * @param {number} theta - Rasch qobiliyat parametri (logit)
   * @param {Object} calibrationParams - Ixtiyoriy kalibrlash sozlamalari
   * @returns {number} Kalibrlangan yakuniy ball (0.0 - 75.0)
   */
  function convertRaschToScore(theta, calibrationParams) {
    const p = Object.assign({}, DEFAULT_CALIBRATION_PARAMS, calibrationParams || {});
    const rawCalc = p.baseScore + (p.scaleFactor * theta);
    const clamped = Math.max(p.minScore, Math.min(p.maxScore, rawCalc));
    return Math.round(clamped * 10) / 10;
  }

  /**
   * 4. Milliy sertifikat darajasini aniqlash
   *
   * Shkala:
   * - 70+     -> A+
   * - 65-69.9 -> A
   * - 60-64.9 -> B+
   * - 55-59.9 -> B
   * - 50-54.9 -> C+
   * - 46-49.9 -> C
   * - < 46    -> Sertifikat darajasi yo'q
   *
   * @param {number} finalScore - Hisoblangan yakuniy ball
   * @returns {{ level: string, isCertified: boolean }}
   */
  function getCertificateLevel(finalScore) {
    if (finalScore >= 70.0) return { level: 'A+', isCertified: true };
    if (finalScore >= 65.0) return { level: 'A', isCertified: true };
    if (finalScore >= 60.0) return { level: 'B+', isCertified: true };
    if (finalScore >= 55.0) return { level: 'B', isCertified: true };
    if (finalScore >= 50.0) return { level: 'C+', isCertified: true };
    if (finalScore >= 46.0) return { level: 'C', isCertified: true };
    return { level: 'Sertifikat darajasi yo\'q', isCertified: false };
  }

  /**
   * 5. 45 ta savol bo'yicha Rasch modelida qobiliyat (theta) va yakuniy natijani hisoblash
   *
   * Har bir savol ma'lumoti:
   * {
   *   questionId: 1,
   *   correctAnswer: 'A',
   *   userAnswer: 'A',
   *   isCorrect: true, // yoki avtomatik solishtiriladi
   *   difficulty: 'easy' // yoki 'medium', 'hard', yoxud real float b_i
   * }
   *
   * @param {Array<Object>} answersData - 45 ta savol ma'lumotlari ro'yxati
   * @param {Object} options - Qo'shimcha parametrlar:
   *                           { autoDifficulty: boolean, maxIter: number, tolerance: number, calibrationParams: Object }
   * @returns {Object} To'liq baholash natijasi
   */
  function calculateRaschAbility(answersData, options) {
    const opts = options || {};
    const autoDifficulty = opts.autoDifficulty !== undefined ? Boolean(opts.autoDifficulty) : true;
    const maxIter = opts.maxIter || 60;
    const tolerance = opts.tolerance || 1e-5;
    const calibrationParams = opts.calibrationParams || null;
    const customDifficultyMap = opts.customDifficultyMap || null;

    const items = [];
    const rawList = Array.isArray(answersData) ? answersData : [];

    rawList.forEach((raw, idx) => {
      const orderNo = idx + 1;
      const qId = raw.questionId !== undefined ? raw.questionId : (raw.question_id !== undefined ? raw.question_id : orderNo);
      const cAns = String(raw.correctAnswer !== undefined ? raw.correctAnswer : (raw.correct_answer || '')).trim();
      const uAns = String(raw.userAnswer !== undefined ? raw.userAnswer : (raw.user_answer || '')).trim();

      let isCorr = false;
      if (raw.isCorrect !== undefined) {
        isCorr = Boolean(raw.isCorrect);
      } else if (raw.is_correct !== undefined) {
        isCorr = Boolean(raw.is_correct);
      } else {
        isCorr = (uAns && cAns) ? (uAns.toUpperCase() === cAns.toUpperCase()) : false;
      }

      const qType = raw.type || (orderNo >= 36 ? 'O' : 'Y');
      const diffEstimate = estimateItemDifficulty(
        orderNo,
        qType,
        autoDifficulty,
        raw.difficulty,
        customDifficultyMap
      );

      items.push({
        questionId: qId,
        correctAnswer: cAns,
        userAnswer: uAns,
        isCorrect: isCorr,
        difficulty: diffEstimate.difficulty,
        numericalB: diffEstimate.numericalB,
        autoAssigned: diffEstimate.autoAssigned
      });
    });

    const totalQuestions = items.length;
    if (totalQuestions === 0) {
      return {
        totalQuestions: 0,
        correctCount: 0,
        wrongCount: 0,
        theta: 0.0,
        standardError: 1.0,
        finalScore: 0.0,
        certificateLevel: 'Sertifikat darajasi yo\'q',
        isCertified: false,
        items: [],
        disclaimer: "Eslatma: Ushbu baholash Milliy sertifikat metodikasiga o'xshash simulyatsion model hisoblanadi."
      };
    }

    const correctCount = items.filter(it => it.isCorrect).length;
    const wrongCount = totalQuestions - correctCount;

    // Ekstremal holatlarni qayta ishlash (Bayes / Winsorized smoothing)
    let adjustedScore = correctCount;
    if (correctCount === 0) {
      adjustedScore = 0.3;
    } else if (correctCount === totalQuestions) {
      adjustedScore = totalQuestions - 0.3;
    }

    // Boshlang'ich theta (oddiy logit nisbati)
    let prop = adjustedScore / totalQuestions;
    prop = Math.max(0.001, Math.min(0.999, prop));
    let theta = Math.log(prop / (1.0 - prop));
    theta = Math.max(-4.5, Math.min(4.5, theta));

    // Newton-Raphson iteratsiyasi
    for (let iter = 0; iter < maxIter; iter++) {
      let fVal = 0.0;     // Sum(P_i) - r
      let infoVal = 0.0;  // Fisher Information

      for (let i = 0; i < totalQuestions; i++) {
        const pI = calculateProbability(theta, items[i].numericalB);
        fVal += pI;
        infoVal += pI * (1.0 - pI);
      }

      fVal -= adjustedScore;

      // Konvergentsiya
      if (Math.abs(fVal) < tolerance) {
        break;
      }

      if (infoVal < 1e-7) {
        break;
      }

      let delta = fVal / infoVal;
      // Qadamni chegaralash
      delta = Math.max(-1.0, Math.min(1.0, delta));
      theta -= delta;
      theta = Math.max(-5.5, Math.min(5.5, theta));
    }

    // Standart xatolik SE(theta) = 1 / sqrt(I(theta))
    let finalInfo = 0.0;
    for (let i = 0; i < totalQuestions; i++) {
      const pI = calculateProbability(theta, items[i].numericalB);
      finalInfo += pI * (1.0 - pI);
    }
    const se = finalInfo > 1e-7 ? (1.0 / Math.sqrt(finalInfo)) : 1.0;

    const roundedTheta = Math.round(theta * 100) / 100;
    const roundedSe = Math.round(se * 100) / 100;

    // Yakuniy ball va sertifikat darajasi
    const finalScore = convertRaschToScore(roundedTheta, calibrationParams);
    const certInfo = getCertificateLevel(finalScore);

    return {
      totalQuestions: totalQuestions,
      correctCount: correctCount,
      wrongCount: wrongCount,
      theta: roundedTheta,
      standardError: roundedSe,
      finalScore: finalScore,
      certificateLevel: certInfo.level,
      isCertified: certInfo.isCertified,
      items: items,
      disclaimer: "Eslatma: Ushbu baholash Milliy sertifikat metodikasiga o'xshash simulyatsion model hisoblanadi va BBA rasmiy natijasi deb talqin qilinmaydi."
    };
  }

  // Tashqi interfeys
  return {
    calculateProbability: calculateProbability,
    estimateItemDifficulty: estimateItemDifficulty,
    convertRaschToScore: convertRaschToScore,
    getCertificateLevel: getCertificateLevel,
    calculateRaschAbility: calculateRaschAbility,
    DEFAULT_DIFFICULTY_MAP: DEFAULT_DIFFICULTY_MAP,
    DEFAULT_CALIBRATION_PARAMS: DEFAULT_CALIBRATION_PARAMS
  };
}));
