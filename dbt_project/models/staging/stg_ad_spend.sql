select
    ad_record_id,
    safe_cast(date as date)             as spend_date,
    platform,
    campaign_name,
    safe_cast(spend_brl as numeric)     as spend_brl,
    safe_cast(impressions as int64)     as impressions,
    safe_cast(clicks as int64)          as clicks,
    _loaded_at
from {{ source('raw', 'ad_spend') }}
