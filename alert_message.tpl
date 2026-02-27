{% for m in mention_members %}[To:{{ m.account_id }}] {{ m.name }}さん
{% endfor %}[info][title]在庫数アラート[/title]
ポータル名: {{ portal_name }}, 商品コード: {{ product_code }}
最低在庫数:{{ portal_min_product_stock_num }}
現在在庫数:{{ portal_product_stock_num }}
[/info]
