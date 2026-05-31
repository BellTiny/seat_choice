from pydantic import BaseModel, ConfigDict, HttpUrl


class SiteSettingUpdate(BaseModel):
    round_interval_days: int | None = None
    max_swap_count: int | None = None
    swap_reason_required: bool | None = None
    team_enabled: bool | None = None
    team_max_carry: int | None = None
    team_adjacent_required: bool | None = None
    team_adjacent_distance: int | None = None
    special_request_open: bool | None = None
    default_orientation: int | None = None
    webhook_url: HttpUrl | None = None
    jwt_expire_minutes: int | None = None


class SiteSettingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    round_interval_days: int
    max_swap_count: int
    swap_reason_required: bool
    team_enabled: bool
    team_max_carry: int
    team_adjacent_required: bool
    team_adjacent_distance: int
    special_request_open: bool
    default_orientation: int
    webhook_url: str | None
    jwt_expire_minutes: int
