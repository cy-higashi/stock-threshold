{% for m in mention_members %}
[To:{{ m.account_id }}] {{ m.name }}さん
{% endfor %}
{% for alert in alerts %}
[info][title]在庫数アラート[/title]
ポータル名: {{ alert.portal_name }}, 商品コード: {{ alert.product_code }}
最低在庫数:{{ alert.portal_min_product_stock_num }}
現在在庫数:{{ alert.portal_product_stock_num }}
[/info]
{% endfor %}
