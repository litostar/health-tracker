/* =====================================================================
 * 主逻辑：标签切换、各模块数据加载与提交（纯前端，数据走 Store/localStorage）
 * ===================================================================== */

const $ = (id) => document.getElementById(id);
const todayStr = () => new Date().toISOString().slice(0, 10);

let currentMeal = "breakfast";   // 当前选中的餐次
let currentFoodDate = todayStr();

/* ---------- 启动 ---------- */
boot();

function boot() {
  $("homeDate") && ($("homeDate").textContent = todayStr());
  $("foodDate").value = todayStr();
  $("watchDate").value = todayStr();
  loadHome();
}

/* ---------- 底部标签切换 ---------- */
document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-pane").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    const tab = btn.dataset.tab;
    $("" + tab).classList.add("active");
    if (tab === "home") loadHome();
    if (tab === "food") loadFood();
    if (tab === "exam") loadExam();
    if (tab === "trend") loadTrend(7);
    if (tab === "watch") $("watchDate").value = todayStr();
    if (tab === "profile") loadProfile();
  });
});

/* ================= 首页 ================= */
async function loadHome() {
  try {
    const s = await Store.getSummary(todayStr());
    const goal = s.goal_intake || 1;
    const intake = s.intake_total || 0;

    // —— Apple 风格热量圆环 ——
    const pct = intake / goal;
    const clamped = Math.min(1, pct);
    const circ = 2 * Math.PI * 54;
    const ring = $("ringProg");
    ring.style.strokeDasharray = circ;
    ring.style.strokeDashoffset = circ * (1 - clamped);
    ring.style.stroke = pct > 1 ? "#ff6b6b" : pct >= 1 ? "#2ecc71" : "#4dd0e1";
    $("ringIntake").textContent = Math.round(intake);
    $("ringGoal").textContent = Math.round(goal);
    $("ringPct").textContent = Math.round(pct * 100) + "%";
    $("hDate").textContent = s.date;

    // —— 关键指标网格 ——
    $("hGoal").textContent = Math.round(goal) + " kcal";
    $("hBmr").textContent = s.bmr != null ? Math.round(s.bmr) + " kcal" : "—";
    $("hTdee").textContent = s.tdee != null ? Math.round(s.tdee) + " kcal" : "—";
    const net = s.deficit_or_surplus;
    const netEl = $("hNet");
    if (net == null) {
      netEl.textContent = "—";
      $("deficitStat").className = "stat";
    } else {
      netEl.textContent = (net >= 0 ? "+" : "") + Math.round(net) + " kcal";
      $("deficitStat").className = "stat " + (net >= 0 ? "pos" : "neg");
    }

    // —— 缺口/盈余状态条 ——
    const box = $("hStatus");
    if (s.status === "unknown") {
      box.className = "status-box unknown";
      box.textContent = "数据不全：请先填 Watch 活动消耗并记一笔摄入";
    } else if (s.status === "deficit") {
      box.className = "status-box deficit";
      box.textContent = `🔥 今日热量缺口 ${Math.round(net)} kcal（利于减脂）`;
    } else {
      box.className = "status-box surplus";
      box.textContent = `🍰 今日热量盈余 ${Math.round(Math.abs(net))} kcal（注意控制）`;
    }

    renderMeals(s.meals, intake);
  } catch (e) { console.error(e); }
}

function renderMeals(meals, intake) {
  const names = { breakfast: "早餐", lunch: "午餐", dinner: "晚餐", snack: "加餐" };
  const colors = { breakfast: "#4dd0e1", lunch: "#7e57c2", dinner: "#ffa726", snack: "#26a69a" };
  const bar = $("mealBar"); bar.innerHTML = "";
  const list = $("mealList"); list.innerHTML = "";
  let segs = "";
  Object.keys(names).forEach(k => {
    const v = (meals && meals[k]) || 0;
    const p = intake > 0 ? (v / intake * 100) : 0;
    if (v > 0) segs += `<div style="width:${p}%;background:${colors[k]}"></div>`;
    const li = document.createElement("li");
    li.innerHTML = `<span><i class="dot" style="background:${colors[k]}"></i>${names[k]}</span><b>${Math.round(v)} kcal</b>`;
    list.appendChild(li);
  });
  bar.innerHTML = segs || `<div style="width:100%;background:var(--line)"></div>`;
}

/* ================= 食物记录 ================= */
document.querySelectorAll(".meal").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".meal").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    currentMeal = b.dataset.meal;
  });
});

$("foodDate").addEventListener("change", (e) => { currentFoodDate = e.target.value; loadFood(); });

$("foodForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Store.addFood({
      log_date: currentFoodDate, meal_type: currentMeal,
      name: $("foodName").value.trim(),
      weight_g: $("foodWeight").value ? Number($("foodWeight").value) : null,
      calories: Number($("foodCal").value),
    });
    $("foodForm").reset();
    loadFood(); loadHome();
  } catch (err) { alert(err.message); }
});

async function loadFood() {
  const list = await Store.getFoods(currentFoodDate);
  const ul = $("foodList"); ul.innerHTML = "";
  const mealName = { breakfast: "早餐", lunch: "午餐", dinner: "晚餐", snack: "加餐" };
  let total = 0;
  list.forEach(f => {
    total += f.calories;
    const li = document.createElement("li");
    li.innerHTML = `
      <div>
        <div><b>${f.name}</b> <span class="meta">· ${mealName[f.meal_type] || f.meal_type}</span></div>
        <div class="meta">${f.weight_g ? f.weight_g + "g · " : ""}${f.calories} kcal</div>
      </div>
      <button class="del" data-id="${f.id}">✕</button>`;
    ul.appendChild(li);
  });
  ul.querySelectorAll(".del").forEach(btn => {
    btn.addEventListener("click", async () => { await Store.delFood(btn.dataset.id); loadFood(); loadHome(); });
  });
  $("foodTotal").innerHTML = `当日合计：<b>${Math.round(total)}</b> kcal`;
}

/* ================= Apple Watch ================= */
$("watchForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await Store.saveWatch({
      log_date: $("watchDate").value,
      active_calories: $("watchActive").value ? Number($("watchActive").value) : null,
      resting_calories: $("watchResting").value ? Number($("watchResting").value) : null,
      steps: $("watchSteps").value ? Number($("watchSteps").value) : null,
    });
    alert("已保存");
    loadHome();
  } catch (err) { alert(err.message); }
});

/* ================= 个人档案 ================= */
async function loadProfile() {
  const p = Store.getProfile();
  if (!p) return;   // 还没建档案，留空让用户填
  $("pGender").value = p.gender;
  $("pAge").value = p.age;
  $("pHeight").value = p.height_cm;
  $("pWeight").value = p.current_weight_kg;
  $("pTargetW").value = p.target_weight_kg ?? "";
  $("pTargetF").value = p.target_body_fat ?? "";
  $("pGoal").value = p.daily_calorie_goal;
}

$("profileForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    Store.saveProfile({
      gender: $("pGender").value,
      age: Number($("pAge").value),
      height_cm: Number($("pHeight").value),
      current_weight_kg: Number($("pWeight").value),
      target_weight_kg: $("pTargetW").value ? Number($("pTargetW").value) : null,
      target_body_fat: $("pTargetF").value ? Number($("pTargetF").value) : null,
      daily_calorie_goal: Number($("pGoal").value),
    });
    $("profileMsg").textContent = "✓ 档案已保存";
    setTimeout(() => ($("profileMsg").textContent = ""), 2000);
    loadHome();
  } catch (err) { alert(err.message); }
});

/* ================= 体检指标 ================= */
$("examForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    Store.addExam({
      name: $("examName").value.trim(),
      value: Number($("examValue").value),
      unit: $("examUnit").value.trim() || null,
      note: $("examNote").value.trim() || null,
    });
    $("examForm").reset();
    loadExam();
  } catch (err) { alert(err.message); }
});

async function loadExam() {
  const list = Store.getExam();
  const ul = $("examList"); ul.innerHTML = "";
  list.forEach(m => {
    const li = document.createElement("li");
    li.innerHTML = `
      <div>
        <div><b>${m.name}</b> <span class="meta">${m.record_date}</span></div>
        <div class="meta">${m.value} ${m.unit || ""} ${m.note ? "· " + m.note : ""}</div>
      </div>`;
    ul.appendChild(li);
  });
}

/* ================= 趋势 ================= */
document.querySelectorAll(".chip").forEach(b => {
  b.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach(x => x.classList.remove("active"));
    b.classList.add("active");
    loadTrend(Number(b.dataset.days));
  });
});

async function loadTrend(days) {
  const r = await Store.getTrend(days);
  renderTrend(r.data);
}

/* ================= 数据备份 / 恢复 ================= */
$("exportBtn").addEventListener("click", () => {
  const blob = new Blob([Store.exportAll()], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `health-backup-${todayStr()}.json`;
  a.click();
});

$("importBtn").addEventListener("click", () => $("importFile").click());
$("importFile").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try { Store.importAll(reader.result); alert("导入成功，正在刷新"); loadHome(); loadProfile(); loadExam(); }
    catch (err) { alert("导入失败：文件格式不正确"); }
  };
  reader.readAsText(file);
  e.target.value = "";
});

/* ---------- PWA：注册 Service Worker（添加到主屏幕 + 离线外壳缓存） ---------- */
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("./sw.js").catch(() => {}));
}
