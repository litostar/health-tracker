/* =====================================================================
 * 动态 TDEE 计算核心（从后端 Python 算法 1:1 移植到前端）
 *
 * 设计要点（与后端完全一致）：
 *   1. BMR 用 Mifflin-St Jeor 公式（比 Harris-Benedict 更准）：
 *        BMR = 10×体重kg + 6.25×身高cm − 5×年龄 + (男 +5 / 女 −161)
 *   2. Apple Watch 的「活动消耗(Active Energy)」不含静息代谢，
 *      所以当日总消耗：
 *        TDEE = BMR + 当日活动消耗
 *      若同时录入「休息消耗(Resting Energy)」（它本身已≈BMR+躺平消耗），
 *      则 TDEE = 休息消耗 + 活动消耗（更精确，因为它直接来自手表实测）。
 *   3. 热量缺口 = TDEE − 当日实际摄入
 *        正 → 缺口（利于减脂）；负 → 盈余（需控制）
 * ===================================================================== */

/* 基础代谢率 BMR（无档案或信息不全时返回 null） */
function calcBMR(p) {
  if (!p || p.age == null || p.height_cm == null || p.current_weight_kg == null) return null;
  const base = 10 * p.current_weight_kg + 6.25 * p.height_cm - 5 * p.age;
  return base + (p.gender === "female" ? -161 : 5);
}

/* 当日总消耗 TDEE（无档案时返回 null） */
function calcTDEE(p, w) {
  const bmr = calcBMR(p);
  if (bmr == null) return null;
  // 有「休息消耗」就优先用「休息 + 活动」，否则用「BMR + 活动」
  if (w && w.resting_calories != null) {
    return (w.resting_calories || 0) + (w.active_calories || 0);
  }
  return bmr + (w && w.active_calories != null ? w.active_calories : 0);
}

/* 热量缺口/盈余 */
function calcDeficit(tdee, intake) {
  if (tdee == null || intake == null) return { net: null, status: "unknown" };
  const net = tdee - intake;
  return { net, status: net > 0 ? "deficit" : "surplus" };
}
