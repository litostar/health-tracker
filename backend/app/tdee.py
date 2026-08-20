"""
======================================================================
  动态热量计算核心算法（重点注释区）
======================================================================
  传统 TDEE 公式（如 Mifflin × 活动系数 1.2/1.5/1.75）的问题：
  活动系数是「拍脑袋」的常数，无法反映你今天到底动了多少。
  本系统改用 Apple Watch 的【真实活动数据】动态计算当日总消耗，
  所以同样一个人，躺着的一天和跑步的一天，TDEE 会实时不同。

  三个核心量：
    1) BMR   基础代谢率  —— 完全静止时维持生命的最低消耗（不含任何活动）
    2) TDEE  当日总消耗  —— BMR + 当天真实活动（来自 Watch）
    3) 缺口  = TDEE - 摄入 —— 正为减脂缺口，负为增重盈余
======================================================================
"""


def calc_bmr(profile) -> float:
    """
    基础代谢率 BMR —— 采用 Mifflin-St Jeor 公式（目前学界公认最准确，
    比老的 Harris-Benedict 误差更小）。

        男性: BMR = 10×体重(kg) + 6.25×身高(cm) − 5×年龄 + 5
        女性: BMR = 10×体重(kg) + 6.25×身高(cm) − 5×年龄 − 161

    注意：BMR 只跟「性别/年龄/身高/体重」有关，跟当天运动无关。
    """
    base = (
        10 * profile.current_weight_kg
        + 6.25 * profile.height_cm
        - 5 * profile.age
    )
    return base + 5 if profile.gender == "male" else base - 161


def calc_tdee(profile, watch) -> float | None:
    """
    动态总消耗 TDEE —— 本系统的灵魂，不用固定系数，而是用 Watch 真实数据。

    Apple Watch 有两个关键指标，含义不同，处理也不同：

    ┌─────────────────┬──────────────────────────┬───────────────────────────┐
    │ 指标             │ 含义                      │ 是否含 BMR               │
    ├─────────────────┼──────────────────────────┼───────────────────────────┤
    │ Active Energy    │ 活动消耗（运动/活动）     │ ❌ 不含静息代谢          │
    │ Resting Energy   │ 休息消耗（静息）         │ ✅ 已含 BMR + 部分 NEAT  │
    └─────────────────┴──────────────────────────┴───────────────────────────┘

    因此分两种口径：
      A) 若录入了「休息消耗 resting_calories」：
             TDEE = resting_calories + active_calories
         因为 Resting Energy 已经把 BMR 及部分非运动消耗(NEAT)打包了，
         只需再把 Active Energy 加上，就是当日真实总消耗，最精确。

      B) 若只录入「活动消耗 active_calories」（最常见，快捷指令默认取这个）：
             TDEE = BMR + active_calories
         因为 Active Energy 不含静息代谢，必须用 BMR 补足静息部分。

    没有任何 Watch 数据时返回 None —— 当天消耗无法估算，前端显示「数据不全」。
    """
    if watch is None:
        return None

    # 口径 A：有休息消耗时，直接 + 活动消耗
    if watch.resting_calories is not None:
        return watch.resting_calories + (watch.active_calories or 0.0)

    # 口径 B：只有活动消耗时，用 BMR 补足静息部分
    if watch.active_calories is not None:
        return calc_bmr(profile) + watch.active_calories

    return None


def calc_deficit(tdee: float | None, intake: float):
    """
    热量缺口 / 盈余 = TDEE − 当日实际摄入

        正值  → 缺口（热量亏空，利于减脂）
        负值  → 盈余（热量过剩，利于增重）
        None  → TDEE 未知（没同步 Watch 数据），无法判断

    返回 (数值, 状态字符串)，状态用于前端着色：deficit / surplus / unknown
    """
    if tdee is None:
        return None, "unknown"
    net = tdee - intake
    return net, ("deficit" if net >= 0 else "surplus")
