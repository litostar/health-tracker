"""
Pydantic 校验模型：定义 API 的「请求体」和「响应体」形状，并做类型校验。
Pydantic v2 语法：model_config = {"from_attributes": True} 让 ORM 对象能直接转成响应模型。
"""
from pydantic import BaseModel, Field
from datetime import date, datetime


# ---------------- 个人档案 ----------------
class ProfileBase(BaseModel):
    gender: str                              # male / female
    age: int
    height_cm: float
    current_weight_kg: float
    target_weight_kg: float | None = None
    target_body_fat: float | None = None
    daily_calorie_goal: float = 2000


class ProfileUpdate(ProfileBase):
    """创建/更新档案的请求体"""


class ProfileOut(ProfileBase):
    """档案的响应体"""
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


# ---------------- 体检指标 ----------------
class ExamMetricCreate(BaseModel):
    record_date: date = Field(default_factory=date.today)
    name: str
    value: float
    unit: str | None = None
    note: str | None = None


class ExamMetricOut(ExamMetricCreate):
    id: int
    model_config = {"from_attributes": True}


# ---------------- 食物记录 ----------------
class FoodLogCreate(BaseModel):
    log_date: date = Field(default_factory=date.today)
    meal_type: str                           # breakfast / lunch / dinner / snack
    name: str
    weight_g: float | None = None
    calories: float


class FoodLogOut(FoodLogCreate):
    id: int
    model_config = {"from_attributes": True}


# ---------------- Apple Watch 同步 ----------------
class WatchDataCreate(BaseModel):
    log_date: date = Field(default_factory=date.today)
    active_calories: float | None = None
    resting_calories: float | None = None
    steps: int | None = None


class WatchDataOut(WatchDataCreate):
    id: int
    updated_at: datetime | None = None
    model_config = {"from_attributes": True}


# ---------------- 每日汇总（首页核心） ----------------
class DailySummary(BaseModel):
    date: date
    intake_total: float                     # 当日摄入总和
    goal_intake: float                      # 目标摄入
    bmr: float | None                       # 基础代谢
    tdee: float | None                      # 动态总消耗
    deficit_or_surplus: float | None        # 正=缺口，负=盈余
    status: str                             # deficit / surplus / unknown
    meals: dict = {}                        # 按餐次汇总：{breakfast, lunch, dinner, snack}
