select
    p.product_id,
    p.product_category_name                                             as category_name_pt,
    t.product_category_name_english                                     as category_name_en,
    safe_cast(safe_cast(p.product_weight_g as float64) as int64)        as weight_g,
    safe_cast(safe_cast(p.product_length_cm as float64) as int64)       as length_cm,
    safe_cast(safe_cast(p.product_height_cm as float64) as int64)       as height_cm,
    safe_cast(safe_cast(p.product_width_cm as float64) as int64)        as width_cm
from {{ source('raw', 'olist_products') }} as p
left join {{ source('raw', 'product_category_name_translation') }} as t
    on p.product_category_name = t.product_category_name
