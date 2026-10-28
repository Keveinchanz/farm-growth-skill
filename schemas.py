"""技能输入契约（本仓库只保留该技能的输入模型）。

裁剪自田头农技台的 `skills/schemas.py`：输出模型仅用于生成文档、
不参与校验，独立发布时不需要，因此整段删去。
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


def _check_iso_date(value: str) -> str:
    """校验 YYYY-MM-DD，返回原字符串。"""
    text = str(value or "").strip()
    try:
        date.fromisoformat(text)
    except ValueError as e:
        raise ValueError("日期格式应为 YYYY-MM-DD") from e
    return text


INCLUDE_KEYS = ("growth", "model", "harvest", "advice", "weather")


class FieldInput(BaseModel):
    """田块。字段与农田库的 field 保持一致，技能不读数据库。"""

    id: str = "skill_field"
    name: str = "技能演示田"
    crop: str = Field(..., min_length=1, description="作物名，如 水稻 / 玉米 / 油菜")
    sow_date: str = Field(..., description="播种日期 YYYY-MM-DD")
    area_mu: float = Field(1.0, gt=0, description="面积（亩）")
    province: str = ""
    city: str = ""
    county: str = ""
    lng: float | None = None
    lat: float | None = None

    @field_validator("sow_date")
    @classmethod
    def _validate_sow_date(cls, value: str) -> str:
        return _check_iso_date(value)


class WeatherRow(BaseModel):
    """逐日气温。`tmean` 缺省时由技能补 (tmax + tmin) / 2。"""

    date: str
    tmax: float
    tmin: float
    tmean: float | None = None
    precip: float | None = None
    humidity: float | None = None

    @field_validator("date")
    @classmethod
    def _validate_date(cls, value: str) -> str:
        return _check_iso_date(value)


class ManagementInput(BaseModel):
    """施肥等管理措施对成熟期的影响。"""

    days: float = 0.0
    note: str = ""
    sources: list[str] = Field(default_factory=list)


class FarmGrowthInput(BaseModel):
    """农田生长、收获预测与 3D 参数的输入。

    有 `history` 就直接算；没有但给了经纬度就联网取；两者都没有则返回完整结构 +
    降级标记，不编造收获日期。
    """

    field: FieldInput
    today: str | None = Field(None, description="计算基准日 YYYY-MM-DD；留空用今天")
    history: list[WeatherRow] = Field(default_factory=list, description="逐日历史气温")
    forecast: list[WeatherRow] = Field(default_factory=list, description="未来天气预报")
    management: ManagementInput | None = None
    sample_count: int | None = Field(None, ge=0, description="收获样本数；传了就不查数据库")
    include: list[str] = Field(
        default_factory=lambda: list(INCLUDE_KEYS),
        description="要返回的块：growth / model / harvest / advice / weather",
    )

    @field_validator("today")
    @classmethod
    def _validate_today(cls, value: str | None) -> str | None:
        return _check_iso_date(value) if value else None

    @field_validator("include")
    @classmethod
    def _validate_include(cls, value: list[str]) -> list[str]:
        unknown = [k for k in value if k not in INCLUDE_KEYS]
        if unknown:
            raise ValueError(f"未知的 include 项：{'、'.join(unknown)}")
        return list(dict.fromkeys(value)) or list(INCLUDE_KEYS)
