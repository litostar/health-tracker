"""
SQLAlchemy 数据模型（表结构）。
共 4 张表：profile（个人档案）、exam_metrics（体检指标）、
food_logs（每日食物）、watch_data（Apple Watch 每日活动）。
"""
from sqlalchemy import Column, Integer, String, Float, Date, DateTime, Text, UniqueConstraint
from datetime import date, datetime, timezone
from app.database import Base


def _now():
    return datetime.now(timezone.utc)


class Profile(Base):
    """个人档案与身体数据（全表只保留一条，更新即覆盖）"""
    __tablename__ = "profile"

    id = Column(Integer, primary_key=True, index=True)
    gender = Column(String(10), nullable=False)          # male / female —— BMR 计算必需
    age = Column(Integer, nullable=False)
    height_cm = Column(Float, nullable=False)
    current_weight_kg = Column(Float, nullable=False)
    target_weight_kg = Column(Float)                     # 目标体重
    target_body_fat = Column(Float)                      # 目标体脂率 %
    daily_calorie_goal = Column(Float, default=2000)     # 每日目标摄入 kcal
    updated_at = Column(DateTime, default=_now, onupdate=_now)


class ExamMetric(Base):
    """体检指标记录（TSH、血脂等，用通用「名称-数值-单位」存储，可扩展任意指标）"""
    __tablename__ = "exam_metrics"

    id = Column(Integer, primary_key=True, index=True)
    record_date = Column(Date, default=date.today, nullable=False)
    name = Column(String(50), nullable=False)            # 例如 TSH / 总胆固醇 / LDL / 甘油三酯
    value = Column(Float, nullable=False)
    unit = Column(String(20))                            # 例如 mIU/L / mmol/L
    note = Column(Text)
    created_at = Column(DateTime, default=_now)


class FoodLog(Base):
    """每日按餐次记录的食物热量"""
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    log_date = Column(Date, default=date.today, nullable=False)
    meal_type = Column(String(10), nullable=False)       # breakfast / lunch / dinner / snack
    name = Column(String(100), nullable=False)
    weight_g = Column(Float)                             # 重量（克），可选
    calories = Column(Float, nullable=False)             # 该食物热量 kcal
    created_at = Column(DateTime, default=_now)


class WatchData(Base):
    """Apple Watch 每日活动数据（每天一条，upsert 覆盖）"""
    __tablename__ = "watch_data"

    id = Column(Integer, primary_key=True, index=True)
    log_date = Column(Date, default=date.today, nullable=False, unique=True)
    active_calories = Column(Float)                      # 活动消耗 kcal（Apple Watch 的 Active Energy，不含静息）
    resting_calories = Column(Float)                     # 休息消耗 kcal（Resting Energy，可选，已含 BMR）
    steps = Column(Integer)
    updated_at = Column(DateTime, default=_now, onupdate=_now)

    __table_args__ = (UniqueConstraint("log_date", name="uq_watch_date"),)
