-- Ad spend can never be negative. Any returned row is a failure.
select
    ad_record_id,
    spend_date,
    platform,
    campaign_name,
    spend_brl
from {{ ref('stg_ad_spend') }}
where spend_brl < 0
