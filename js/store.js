/* =====================================================================
 * 本地数据层（替代后端 API）
 * 所有数据存浏览器 localStorage —— 与 wordbook 同架构，纯前端、无服务器。
 * 字段命名刻意与原后端 schema 保持一致，将来若想切回后端只需替换本文件。
 * ===================================================================== */
const Store = (() => {
  const K = { profile: "ht_profile", foods: "ht_foods", watch: "ht_watch", exam: "ht_exam" };
  const read  = (k, d) => { try { return JSON.parse(localStorage.getItem(k)) ?? d; } catch { return d; } };
  const write = (k, v) => localStorage.setItem(k, JSON.stringify(v));
  const genId = () => (crypto.randomUUID ? crypto.randomUUID() : Date.now() + "-" + Math.random().toString(16).slice(2));

  /* ---------- 个人档案 ---------- */
  function getProfile() { return read(K.profile, null); }
  function saveProfile(p) { write(K.profile, p); return p; }

  /* ---------- 食物记录 ---------- */
  function getFoods(date) {
    return read(K.foods, []).filter(f => f.log_date === date);
  }
  function addFood(f) {
    const all = read(K.foods, []);
    const rec = { id: genId(), log_date: f.log_date, meal_type: f.meal_type,
      name: f.name, weight_g: f.weight_g ?? null, calories: f.calories };
    all.push(rec); write(K.foods, all); return rec;
  }
  function delFood(id) { write(K.foods, read(K.foods, []).filter(f => f.id !== id)); }

  /* ---------- Apple Watch（按日期 upsert） ---------- */
  function getWatch(date) { return read(K.watch, []).find(w => w.log_date === date) || null; }
  function saveWatch(w) {
    const all = read(K.watch, []);
    const i = all.findIndex(x => x.log_date === w.log_date);
    const rec = { id: genId(), log_date: w.log_date,
      active_calories: w.active_calories ?? null,
      resting_calories: w.resting_calories ?? null,
      steps: w.steps ?? null };
    if (i >= 0) all[i] = rec; else all.push(rec);
    write(K.watch, all); return rec;
  }

  /* ---------- 体检指标 ---------- */
  function getExam() { return read(K.exam, []); }
  function addExam(m) {
    const all = read(K.exam, []);
    const rec = { id: genId(), name: m.name, value: m.value, unit: m.unit ?? null,
      note: m.note ?? null, record_date: m.record_date || new Date().toISOString().slice(0, 10) };
    all.unshift(rec); write(K.exam, all); return rec;
  }

  /* ---------- 今日汇总（对应原 /api/summary/today） ---------- */
  function getSummary(date) {
    const p = getProfile();
    const foods = getFoods(date);
    const intake = foods.reduce((s, f) => s + (f.calories || 0), 0);
    const meals = { breakfast: 0, lunch: 0, dinner: 0, snack: 0 };
    foods.forEach(f => { meals[f.meal_type] = (meals[f.meal_type] || 0) + (f.calories || 0); });
    const w = getWatch(date);
    const bmr = calcBMR(p);
    const tdee = calcTDEE(p, w);
    const goal = p?.daily_calorie_goal || 2000;
    const { net, status } = calcDeficit(tdee, intake > 0 ? intake : null);
    // 没吃东西时不展示缺口（避免误导），统一标 unknown
    const finalStatus = (tdee == null || intake <= 0) ? "unknown" : status;
    return { date, intake_total: intake, goal_intake: goal, bmr, tdee,
      deficit_or_surplus: net, status: finalStatus, meals };
  }

  /* ---------- 趋势（对应原 /api/trend） ---------- */
  function getTrend(days) {
    const p = getProfile();
    const allFoods = read(K.foods, []);
    const data = [];
    const today = new Date();
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(today); d.setDate(d.getDate() - i);
      const date = d.toISOString().slice(0, 10);
      const intake = allFoods.filter(f => f.log_date === date)
        .reduce((s, f) => s + (f.calories || 0), 0);
      data.push({ date, intake, bmr: calcBMR(p), tdee: calcTDEE(p, getWatch(date)) });
    }
    return { data };
  }

  /* ---------- 备份 / 恢复（健康数据丢了心疼，建议定期导出） ---------- */
  function exportAll() {
    return JSON.stringify({ profile: getProfile(), foods: read(K.foods, []),
      watch: read(K.watch, []), exam: read(K.exam, []) }, null, 2);
  }
  function importAll(json) {
    const o = JSON.parse(json);
    if (o.profile) write(K.profile, o.profile);
    if (Array.isArray(o.foods)) write(K.foods, o.foods);
    if (Array.isArray(o.watch)) write(K.watch, o.watch);
    if (Array.isArray(o.exam)) write(K.exam, o.exam);
  }

  return { getProfile, saveProfile, getFoods, addFood, delFood,
    getWatch, saveWatch, getExam, addExam, getSummary, getTrend, exportAll, importAll };
})();
