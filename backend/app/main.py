"""
FastAPI 主应用：
  - 所有 /api/* 路由都需要 Bearer Token 鉴权
  - 生产环境下，FastAPI 直接托管 frontend/ 里的静态页面（单域名、手机刷新即用）
"""
import os
from datetime import date, timedelta
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func

from app.database import init_db, get_db
from app import models, schemas
from app.auth import require_token
from app.tdee import calc_bmr, calc_tdee, calc_deficit
from app.config import CORS_ORIGINS

# 启动时建表（幂等，已有表不会重复创建）
init_db()

app = FastAPI(title="个人健康与热量追踪工作台 API", version="1.0.0")

# 跨域：本地开发前端若单独跑（如 http://localhost:5500）需要放行
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================= 个人档案 =========================
@app.get("/api/profile", response_model=schemas.ProfileOut)
def get_profile(_=Depends(require_token), db=Depends(get_db)):
    p = db.query(models.Profile).first()
    if not p:
        raise HTTPException(status_code=404, detail="尚未创建档案，请先到「档案」页填写")
    return p


@app.post("/api/profile", response_model=schemas.ProfileOut)
def upsert_profile(payload: schemas.ProfileUpdate, _=Depends(require_token), db=Depends(get_db)):
    """新建或覆盖唯一一条档案记录"""
    p = db.query(models.Profile).first()
    data = payload.model_dump()
    if p:
        for k, v in data.items():
            setattr(p, k, v)
    else:
        p = models.Profile(**data)
        db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ========================= 体检指标 =========================
@app.get("/api/exam", response_model=list[schemas.ExamMetricOut])
def list_exam(_=Depends(require_token), db=Depends(get_db)):
    return db.query(models.ExamMetric).order_by(models.ExamMetric.record_date.desc()).all()


@app.post("/api/exam", response_model=schemas.ExamMetricOut)
def add_exam(payload: schemas.ExamMetricCreate, _=Depends(require_token), db=Depends(get_db)):
    m = models.ExamMetric(**payload.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


# ========================= 食物记录 =========================
@app.get("/api/food", response_model=list[schemas.FoodLogOut])
def list_food(log_date: date = date.today(), _=Depends(require_token), db=Depends(get_db)):
    return db.query(models.FoodLog).filter(models.FoodLog.log_date == log_date).all()


@app.post("/api/food", response_model=schemas.FoodLogOut)
def add_food(payload: schemas.FoodLogCreate, _=Depends(require_token), db=Depends(get_db)):
    f = models.FoodLog(**payload.model_dump())
    db.add(f)
    db.commit()
    db.refresh(f)
    return f


@app.delete("/api/food/{food_id}")
def delete_food(food_id: int, _=Depends(require_token), db=Depends(get_db)):
    f = db.query(models.FoodLog).filter(models.FoodLog.id == food_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="记录不存在")
    db.delete(f)
    db.commit()
    return {"ok": True}


# ==================== Apple Watch 同步（快捷指令调用） ====================
@app.post("/api/sync/watch", response_model=schemas.WatchDataOut)
def sync_watch(payload: schemas.WatchDataCreate, _=Depends(require_token), db=Depends(get_db)):
    """
    iPhone「快捷指令」每天定时调用的接口：把当日活动消耗 / 步数写进来。
    同一天多次调用会自动覆盖（upsert），所以重跑也不会产生重复行。
    """
    w = db.query(models.WatchData).filter(models.WatchData.log_date == payload.log_date).first()
    if w:
        for k, v in payload.model_dump().items():
            if v is not None:          # 只更新非空字段，方便「只补步数」这类部分更新
                setattr(w, k, v)
    else:
        w = models.WatchData(**payload.model_dump())
        db.add(w)
    db.commit()
    db.refresh(w)
    return w


# ========================= 每日汇总（首页核心） =========================
@app.get("/api/summary/today", response_model=schemas.DailySummary)
def summary_today(_=Depends(require_token), db=Depends(get_db)):
    return build_summary(date.today(), db)


def build_summary(d: date, db):
    """汇总某天的：摄入总和、目标、BMR、动态 TDEE、缺口/盈余。被 today 和趋势复用。"""
    profile = db.query(models.Profile).first()
    goal = profile.daily_calorie_goal if profile else 2000

    intake = db.query(func.sum(models.FoodLog.calories)).filter(
        models.FoodLog.log_date == d
    ).scalar() or 0.0

    watch = db.query(models.WatchData).filter(models.WatchData.log_date == d).first()
    bmr = calc_bmr(profile) if profile else None
    tdee = calc_tdee(profile, watch) if profile else None
    net, status = calc_deficit(tdee, intake)

    # 按餐次汇总（供首页圆环/占比条使用）
    meals = {}
    for mt in ("breakfast", "lunch", "dinner", "snack"):
        sub = db.query(func.sum(models.FoodLog.calories)).filter(
            models.FoodLog.log_date == d,
            models.FoodLog.meal_type == mt,
        ).scalar() or 0.0
        meals[mt] = round(sub, 1)

    return schemas.DailySummary(
        date=d,
        intake_total=round(intake, 1),
        goal_intake=goal,
        bmr=round(bmr, 1) if bmr else None,
        tdee=round(tdee, 1) if tdee else None,
        deficit_or_surplus=round(net, 1) if net is not None else None,
        status=status,
        meals=meals,
    )


# ========================= 历史趋势（图表） =========================
@app.get("/api/trend")
def trend(days: int = 7, _=Depends(require_token), db=Depends(get_db)):
    """返回最近 N 天每日「摄入 vs TDEE」序列，供前端折线图渲染。"""
    end = date.today()
    start = end - timedelta(days=days - 1)
    profile = db.query(models.Profile).first()

    data = []
    d = start
    while d <= end:
        intake = db.query(func.sum(models.FoodLog.calories)).filter(
            models.FoodLog.log_date == d
        ).scalar() or 0.0
        watch = db.query(models.WatchData).filter(models.WatchData.log_date == d).first()
        tdee = calc_tdee(profile, watch) if profile else None
        data.append({
            "date": d.isoformat(),
            "intake": round(intake, 1),
            "tdee": round(tdee, 1) if tdee else None,
        })
        d += timedelta(days=1)
    return {"days": days, "data": data}


# ========================= 静态前端托管 =========================
# 生产环境：FastAPI 直接把 frontend/ 作为网站根目录，/api 留给接口，其余返回页面。
# 本地若想单独跑前端（如 VS Code Live Server），此挂载不影响，前端直接连 localhost:8000 即可。
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
if os.path.isdir(FRONTEND_DIR):
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    from app.config import PORT
    uvicorn.run("app.main:app", host="0.0.0.0", port=PORT, reload=True)
