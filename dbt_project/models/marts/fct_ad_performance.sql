-- Daily ad performance by platform and campaign.
select
    concat(cast(spend_date as string), '|', platform, '|', campaign_name) as ad_performance_id,
    spend_date,
    platform,
    campaign_name,
    spend_brl,
    impressions,
    clicks,
    safe_divide(clicks, impressions)    as ctr,
    safe_divide(spend_brl, clicks)      as cpc_brl
from {{ ref('stg_ad_spend') }}
